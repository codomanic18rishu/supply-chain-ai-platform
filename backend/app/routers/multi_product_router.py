"""
multi_product_router.py
-----------------------
Placement: app/routers/multi_product_router.py

Defines the POST /upload-multi-product-forecast/ endpoint.

This router:
  1. Accepts a CSV file upload (up to 10 MB)
  2. Validates and normalises column names
  3. Optionally limits to top-N products by total sales (performance guard)
  4. Runs per-product XGBoost forecasting
  5. Calculates inventory optimisation metrics
  6. Detects supply chain risks
  7. Generates OpenAI insights
  8. Persists results to DB (deferred to Phase 2 — stub included)
  9. Returns structured JSON matching MultiProductForecastResponse

Registration in main.py (add these two lines):
    from app.routers.multi_product_router import router as multi_product_router
    app.include_router(multi_product_router)
"""

from __future__ import annotations

import io
import logging
import time
from dataclasses import asdict

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session


from app.core.database import get_db             # reuse your existing DB dependency
from app.schemas.multi_product_schemas import (
    AIInsightsSchema,
    InventoryMetricSchema,
    MultiProductForecastResponse,
    ProductForecastSchema,
    RiskAlertSchema,
    SkippedProductSchema,
    TopProductSchema,
)
from app.services.ai_insights import generate_ai_insights
from app.services.column_mapper import ColumnMapError, normalise_columns
from app.services.inventory_optimizer import calculate_inventory_metrics
from app.services.multi_product_forecaster import run_multi_product_forecast
from app.services.risk_detector import detect_risks

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Multi-Product Forecasting"],
)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# Helper – serialise dataclass instances to plain dicts
# ---------------------------------------------------------------------------

def _dataclass_to_dict(obj) -> dict:
    return asdict(obj)


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/upload-multi-product-forecast/",
    response_model=MultiProductForecastResponse,
    summary="Multi-Product Demand Forecast & Inventory Optimisation",
    description=(
        "Upload a CSV file containing multi-product sales history. "
        "Returns per-product 7-day demand forecasts, inventory metrics, "
        "risk alerts, and AI-generated executive insights."
    ),
    status_code=status.HTTP_200_OK,
)
async def upload_multi_product_forecast(
    file: UploadFile = File(..., description="CSV file with date, product_id, and sales columns."),
    lead_time_days: int = Form(default=7),
    service_level: float = Form(default=0.95),
    top_n: int = Form(default=20),
    forecast_horizon: int = Form(default=7),
    max_products: int = Form(default=200),
    db: Session = Depends(get_db),
):
    start_time = time.perf_counter()

    # ------------------------------------------------------------------
    # 1. File validation
    # ------------------------------------------------------------------
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are accepted.",
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB.",
        )
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # ------------------------------------------------------------------
    # 2. Parse CSV
    # ------------------------------------------------------------------
    try:
        df_raw = pd.read_csv(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV: {exc}",
        ) from exc

    if df_raw.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file contains no data rows.",
        )

    logger.info(
        "User %s uploaded multi-product CSV: %d rows, %d columns.",
        1,
        len(df_raw),
        len(df_raw.columns),
    )

    # ------------------------------------------------------------------
    # 3. Normalise columns
    # ------------------------------------------------------------------
    try:
        df = normalise_columns(df_raw)
    except ColumnMapError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    # ------------------------------------------------------------------
    # 4. Performance guard – limit to top-N products by total sales
    # ------------------------------------------------------------------
    all_product_ids = df["product_id"].unique()
    n_total = len(all_product_ids)

    if n_total > max_products:
        logger.info(
            "Dataset has %d products; limiting to top %d by total sales.",
            n_total,
            max_products,
        )
        top_pids = (
            df.groupby("product_id")["sales"]
            .sum()
            .nlargest(max_products)
            .index.tolist()
        )
        df = df[df["product_id"].isin(top_pids)]

    # ------------------------------------------------------------------
    # 5. Multi-product XGBoost forecasting
    # ------------------------------------------------------------------
    try:
        forecast_output = run_multi_product_forecast(
            df=df,
            top_n=top_n,
            horizon=forecast_horizon,
            min_history=14,
        )
    except Exception as exc:
        logger.error("Forecasting pipeline failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecasting failed: {exc}",
        ) from exc

    # ------------------------------------------------------------------
    # 6. Inventory optimisation
    # ------------------------------------------------------------------
    # Build simple dict list from forecast results for the optimizer
    forecast_dicts = [
        {
            "product_id": r.product_id,
            "product_name": r.product_name,
            "avg_daily_demand": r.avg_daily_demand,
            "demand_std": r.demand_std,
        }
        for r in forecast_output.products
        if not r.skipped
    ]

    inv_result = calculate_inventory_metrics(
        product_forecasts=forecast_dicts,
        lead_time_days=lead_time_days,
        service_level=service_level,
    )
    inv_dicts = [_dataclass_to_dict(m) for m in inv_result.metrics]

    # ------------------------------------------------------------------
    # 7. Risk detection
    # ------------------------------------------------------------------
    # Build product dicts for risk detector (uses growth_rate from forecast)
    risk_product_dicts = [
        {
            "product_id": r.product_id,
            "product_name": r.product_name,
            "demand_growth_rate": r.demand_growth_rate,
            "total_projected_7d": r.total_projected_7d,
            "avg_daily_demand": r.avg_daily_demand,
        }
        for r in forecast_output.products
        if not r.skipped
    ]

    risk_result = detect_risks(
        product_forecasts=risk_product_dicts,
        inventory_metrics=inv_dicts,
    )
    risk_dicts = [_dataclass_to_dict(a) for a in risk_result.alerts]

    # ------------------------------------------------------------------
    # 8. AI insights
    # ------------------------------------------------------------------
    ai_response = generate_ai_insights(
        top_products=forecast_output.top_products,
        inventory_metrics=inv_dicts,
        risk_alerts=risk_dicts,
        total_products=forecast_output.total_products_processed,
        total_skipped=forecast_output.total_products_skipped,
    )

    # ------------------------------------------------------------------
    # 9. Persist to DB (Phase 2 stub — uncomment after DB migration)
    # ------------------------------------------------------------------
    # from app.services.db_persister import persist_multi_product_session
    # session_id = persist_multi_product_session(
    #     db=db,
    #     user_id=1,
    #     filename=file.filename,
    #     forecast_output=forecast_output,
    #     inv_result=inv_result,
    #     risk_result=risk_result,
    #     ai_response=ai_response,
    # )

    # ------------------------------------------------------------------
    # 10. Build and return response
    # ------------------------------------------------------------------
    elapsed = time.perf_counter() - start_time

    product_schemas = [
        ProductForecastSchema(
            product_id=r.product_id,
            product_name=r.product_name,
            forecast_dates=r.forecast_dates,
            forecast_values=r.forecast_values,
            historical_dates=r.historical_dates,
            historical_values=r.historical_values,
            avg_daily_demand=r.avg_daily_demand,
            demand_std=r.demand_std,
            demand_growth_rate=r.demand_growth_rate,
            total_projected_7d=r.total_projected_7d,
            skipped=r.skipped,
            skip_reason=r.skip_reason,
        )
        for r in forecast_output.products
    ]

    top_product_schemas = [
        TopProductSchema(**p) for p in forecast_output.top_products
    ]

    inv_schemas = [
        InventoryMetricSchema(**m) for m in inv_dicts
    ]

    risk_schemas = [
        RiskAlertSchema(**a) for a in risk_dicts
    ]

    ai_schema = AIInsightsSchema(
        urgent_actions=ai_response.urgent_actions,
        fastest_growing=ai_response.fastest_growing,
        optimization_recs=ai_response.optimization_recs,
        risk_summary=ai_response.risk_summary,
        executive_summary=ai_response.executive_summary,
        error=ai_response.error,
    )

    skipped_schemas = [
        SkippedProductSchema(**s) for s in forecast_output.skipped_products
    ]

    metadata = {
        "filename": file.filename,
        "total_rows": int(len(df_raw)),
        "total_products_in_file": int(n_total),
        "products_processed": int(forecast_output.total_products_processed),
        "products_skipped": int(forecast_output.total_products_skipped),
        "risk_alerts_total": int(len(risk_result.alerts)),
        "risk_alerts_high_priority": int(risk_result.high_priority_count),
        "products_at_risk": int(len(risk_result.products_at_risk)),
        "processing_time_seconds": round(elapsed, 2),
        "config": {
            "lead_time_days": lead_time_days,
            "service_level": service_level,
            "top_n": top_n,
            "forecast_horizon": forecast_horizon,
        },
    }

    metadata["session_id"] = 999
    response = MultiProductForecastResponse(
        products=product_schemas,
        top_products=top_product_schemas,
        inventory_metrics=inv_schemas,
        risk_alerts=risk_schemas,
        ai_insights=ai_schema,
        skipped_products=skipped_schemas,
        metadata=metadata,
    )

    logger.info(
        "Multi-product forecast complete for user %s | products=%d | elapsed=%.2fs",
        1,
        forecast_output.total_products_processed,
        elapsed,
    )

    return response

    # -----------------------------
    # Phase 2: Persist results to database
    # -----------------------------
    try:
        from app.models.multi_product_models import MultiProductSession

        session = MultiProductSession(
            user_id=1,
            filename=metadata["filename"],
            total_products=metadata["products_processed"],
            processing_time_seconds=metadata["processing_time_seconds"]
