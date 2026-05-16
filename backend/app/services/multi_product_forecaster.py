"""
multi_product_forecaster.py
---------------------------
Placement: app/services/multi_product_forecaster.py

Trains a separate XGBoost model per product and generates 7-day-ahead
demand forecasts. Returns per-product forecast data and a ranked summary
of the top N products by projected demand growth.

Key design decisions
--------------------
* Minimum history threshold: 14 days (configurable). Products with fewer
  dates are skipped with a logged warning.
* Feature set: lag features (1, 7, 14 days), rolling means (7, 14 days),
  rolling std (7 days), day-of-week, day-of-month, month, quarter, year,
  is_weekend.
* Forecast horizon: 7 days (configurable).
* Growth metric: (sum of 7-day forecast) / (mean of last 7 actual days) - 1.
  Products with zero recent demand are handled safely.
* Top-N selection: ranked by growth rate descending (default N=20).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
MIN_HISTORY_DAYS = 14          # minimum unique dates required to train
FORECAST_HORIZON = 7           # days ahead to forecast
TOP_N_PRODUCTS = 20            # products returned in ranked summary
RANDOM_STATE = 42


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ProductForecastResult:
    product_id: str
    product_name: str
    forecast_dates: list[str]          # ISO format: YYYY-MM-DD
    forecast_values: list[float]
    historical_dates: list[str]        # last 30 days of actuals for charting
    historical_values: list[float]
    avg_daily_demand: float
    demand_std: float
    demand_growth_rate: float          # decimal e.g. 0.15 = +15 %
    total_projected_7d: float
    skipped: bool = False
    skip_reason: Optional[str] = None


@dataclass
class MultiProductForecastOutput:
    products: list[ProductForecastResult] = field(default_factory=list)
    top_products: list[dict] = field(default_factory=list)   # ranked summary
    skipped_products: list[dict] = field(default_factory=list)
    total_products_processed: int = 0
    total_products_skipped: int = 0


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def _add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add calendar and lag features to a single-product daily series."""
    df = df.sort_values("date").reset_index(drop=True)
    df["dayofweek"] = df["date"].dt.dayofweek
    df["dayofmonth"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter
    df["year"] = df["date"].dt.year
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)

    for lag in [1, 7, 14]:
        df[f"lag_{lag}"] = df["sales"].shift(lag)

    df["rolling_mean_7"] = df["sales"].shift(1).rolling(7).mean()
    df["rolling_mean_14"] = df["sales"].shift(1).rolling(14).mean()
    df["rolling_std_7"] = df["sales"].shift(1).rolling(7).std()

    return df


FEATURE_COLS = [
    "dayofweek", "dayofmonth", "month", "quarter", "year", "is_weekend",
    "lag_1", "lag_7", "lag_14",
    "rolling_mean_7", "rolling_mean_14", "rolling_std_7",
]


# ---------------------------------------------------------------------------
# Single-product training + forecasting
# ---------------------------------------------------------------------------

def _aggregate_daily(product_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate a product's rows to one row per date."""
    daily = (
        product_df
        .groupby("date", as_index=False)["sales"]
        .sum()
        .sort_values("date")
        .reset_index(drop=True)
    )
    # Fill missing calendar dates with 0 demand
    full_range = pd.date_range(daily["date"].min(), daily["date"].max(), freq="D")
    daily = (
        daily
        .set_index("date")
        .reindex(full_range, fill_value=0)
        .rename_axis("date")
        .reset_index()
    )
    return daily


def _train_and_forecast(
    daily: pd.DataFrame,
    horizon: int = FORECAST_HORIZON,
) -> tuple[list[str], list[float]]:
    """
    Train XGBoost on *daily* and recursively forecast *horizon* days ahead.

    Returns
    -------
    (forecast_dates, forecast_values)
    """
    feat_df = _add_time_features(daily.copy())
    train = feat_df.dropna(subset=FEATURE_COLS)

    X_train = train[FEATURE_COLS]
    y_train = train["sales"]

    model = XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_STATE,
        verbosity=0,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # --- recursive multi-step forecasting ---
    # Extend the series day-by-day, feeding each prediction back as a lag.
    extended = daily.copy()
    forecast_dates: list[str] = []
    forecast_values: list[float] = []

    for _ in range(horizon):
        next_date = extended["date"].max() + pd.Timedelta(days=1)
        next_row = pd.DataFrame({"date": [next_date], "sales": [np.nan]})
        extended = pd.concat([extended, next_row], ignore_index=True)
        feat_ext = _add_time_features(extended.copy())
        last_feat = feat_ext.iloc[[-1]][FEATURE_COLS]

        # Replace NaN lag/rolling with column median from training set
        for col in FEATURE_COLS:
            if last_feat[col].isna().any():
                last_feat[col] = train[col].median()

        pred = float(model.predict(last_feat)[0])
        pred = max(0.0, round(pred, 4))   # clip negative predictions

        forecast_dates.append(next_date.strftime("%Y-%m-%d"))
        forecast_values.append(pred)

        # Feed prediction back into series
        extended.at[extended.index[-1], "sales"] = pred

    return forecast_dates, forecast_values


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_multi_product_forecast(
    df: pd.DataFrame,
    top_n: int = TOP_N_PRODUCTS,
    horizon: int = FORECAST_HORIZON,
    min_history: int = MIN_HISTORY_DAYS,
    history_window: int = 30,           # days of actuals to return for charts
) -> MultiProductForecastOutput:
    """
    Main entry point. Expects *df* with columns:
        date, product_id, product_name, sales

    Returns a ``MultiProductForecastOutput`` containing per-product results
    and a ranked top-N summary.
    """
    output = MultiProductForecastOutput()
    product_ids = df["product_id"].unique()
    logger.info("Starting multi-product forecast. Total products: %d", len(product_ids))

    results: list[ProductForecastResult] = []

    for pid in product_ids:
        pname = df.loc[df["product_id"] == pid, "product_name"].iloc[0]
        product_df = df[df["product_id"] == pid].copy()

        daily = _aggregate_daily(product_df)
        n_dates = len(daily)

        if n_dates < min_history:
            logger.warning(
                "Skipping product '%s' (%s): only %d days of history (min %d).",
                pname, pid, n_dates, min_history,
            )
            output.skipped_products.append({
                "product_id": str(pid),
                "product_name": str(pname),
                "reason": f"Insufficient history: {n_dates} days (minimum {min_history})",
            })
            output.total_products_skipped += 1
            results.append(ProductForecastResult(
                product_id=str(pid),
                product_name=str(pname),
                forecast_dates=[],
                forecast_values=[],
                historical_dates=[],
                historical_values=[],
                avg_daily_demand=0.0,
                demand_std=0.0,
                demand_growth_rate=0.0,
                total_projected_7d=0.0,
                skipped=True,
                skip_reason=f"Insufficient history: {n_dates} days",
            ))
            continue

        try:
            forecast_dates, forecast_values = _train_and_forecast(daily, horizon)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to forecast product '%s': %s", pid, exc, exc_info=True)
            output.skipped_products.append({
                "product_id": str(pid),
                "product_name": str(pname),
                "reason": f"Training error: {exc}",
            })
            output.total_products_skipped += 1
            continue

        # Historical window for charting
        hist = daily.tail(history_window)
        historical_dates = [d.strftime("%Y-%m-%d") for d in hist["date"]]
        historical_values = [round(float(v), 4) for v in hist["sales"]]

        avg_demand = float(daily["sales"].mean())
        demand_std = float(daily["sales"].std())

        # Growth rate: compare projected vs recent actuals
        recent_actual_mean = float(daily["sales"].tail(7).mean())
        projected_mean = float(np.mean(forecast_values)) if forecast_values else 0.0
        if recent_actual_mean > 0:
            growth_rate = (projected_mean - recent_actual_mean) / recent_actual_mean
        else:
            growth_rate = 0.0

        result = ProductForecastResult(
            product_id=str(pid),
            product_name=str(pname),
            forecast_dates=forecast_dates,
            forecast_values=[round(v, 4) for v in forecast_values],
            historical_dates=historical_dates,
            historical_values=historical_values,
            avg_daily_demand=round(avg_demand, 4),
            demand_std=round(demand_std, 4),
            demand_growth_rate=round(growth_rate, 6),
            total_projected_7d=round(sum(forecast_values), 4),
        )
        results.append(result)
        output.total_products_processed += 1
        logger.debug("Forecasted product '%s' | growth=%.2f%%", pid, growth_rate * 100)

    # --- Build top-N ranked summary ---
    eligible = [r for r in results if not r.skipped]
    ranked = sorted(eligible, key=lambda r: r.demand_growth_rate, reverse=True)[:top_n]

    output.top_products = [
        {
            "rank": i + 1,
            "product_id": r.product_id,
            "product_name": r.product_name,
            "avg_daily_demand": r.avg_daily_demand,
            "demand_std": r.demand_std,
            "total_projected_7d": r.total_projected_7d,
            "demand_growth_rate": r.demand_growth_rate,
            "demand_growth_pct": round(r.demand_growth_rate * 100, 2),
        }
        for i, r in enumerate(ranked)
    ]

    output.products = results
    logger.info(
        "Forecast complete. Processed: %d | Skipped: %d | Top-%d selected.",
        output.total_products_processed,
        output.total_products_skipped,
        len(output.top_products),
    )
    return output
