"""
column_mapper.py
----------------
Placement: app/services/column_mapper.py

Normalises arbitrary CSV column names to the internal schema expected by
the multi-product forecasting pipeline.

Internal schema
---------------
  date         : datetime column
  product_id   : unique product identifier
  product_name : human-readable name (optional, falls back to product_id)
  sales        : numeric quantity sold
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Alias maps – order matters: first match wins (most specific first)
# ---------------------------------------------------------------------------

DATE_ALIASES: list[str] = [
    "date",
    "invoicedate",
    "invoice_date",
    "order_date",
    "orderdate",
    "transaction_date",
    "transactiondate",
    "timestamp",
    "period",
]

PRODUCT_ID_ALIASES: list[str] = [
    "product_id",
    "productid",
    "stockcode",
    "stock_code",
    "sku",
    "item_id",
    "itemid",
    "item_code",
    "itemcode",
    "product_code",
    "productcode",
    "asin",
]

PRODUCT_NAME_ALIASES: list[str] = [
    "product_name",
    "productname",
    "description",
    "item_name",
    "itemname",
    "product",
    "name",
    "title",
]

SALES_ALIASES: list[str] = [
    "sales",
    "quantity",
    "qty",
    "units",
    "units_sold",
    "unitssold",
    "amount",
    "volume",
    "demand",
    "revenue",
    "sold",
]


def _find_column(df: pd.DataFrame, aliases: list[str]) -> Optional[str]:
    """Return the first column whose lowercased, stripped name matches an alias."""
    normalised = {col.strip().lower().replace(" ", "_"): col for col in df.columns}
    for alias in aliases:
        if alias in normalised:
            return normalised[alias]
    return None


class ColumnMapError(ValueError):
    """Raised when a required column cannot be resolved."""


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a copy of *df* with columns renamed to the internal schema.

    Required mappings: date, product_id, sales
    Optional mapping : product_name (defaults to product_id value when absent)

    Raises
    ------
    ColumnMapError
        If any required column cannot be found.
    """
    df = df.copy()

    mapping: dict[str, str] = {}  # original_col -> internal_name

    # --- date ---
    date_col = _find_column(df, DATE_ALIASES)
    if date_col is None:
        raise ColumnMapError(
            f"Cannot find a date column. Expected one of: {DATE_ALIASES}. "
            f"Got columns: {list(df.columns)}"
        )
    mapping[date_col] = "date"

    # --- product_id ---
    pid_col = _find_column(df, PRODUCT_ID_ALIASES)
    if pid_col is None:
        raise ColumnMapError(
            f"Cannot find a product identifier column. "
            f"Expected one of: {PRODUCT_ID_ALIASES}. "
            f"Got columns: {list(df.columns)}"
        )
    mapping[pid_col] = "product_id"

    # --- sales ---
    sales_col = _find_column(df, SALES_ALIASES)
    if sales_col is None:
        raise ColumnMapError(
            f"Cannot find a sales/quantity column. "
            f"Expected one of: {SALES_ALIASES}. "
            f"Got columns: {list(df.columns)}"
        )
    mapping[sales_col] = "sales"

    # --- product_name (optional) ---
    name_col = _find_column(df, PRODUCT_NAME_ALIASES)
    if name_col and name_col not in mapping:
        mapping[name_col] = "product_name"

    df = df.rename(columns=mapping)

    # Add product_name column if missing
    if "product_name" not in df.columns:
        df["product_name"] = df["product_id"].astype(str)
        logger.info("No product_name column found; using product_id as product_name.")

    # Parse date column
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    invalid_dates = df["date"].isna().sum()
    if invalid_dates > 0:
        logger.warning("Dropped %d rows with unparseable dates.", invalid_dates)
        df = df.dropna(subset=["date"])

    # Coerce sales to numeric, drop NaN
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
    invalid_sales = df["sales"].isna().sum()
    if invalid_sales > 0:
        logger.warning("Dropped %d rows with non-numeric sales values.", invalid_sales)
        df = df.dropna(subset=["sales"])

    # Drop negative sales (returns / adjustments)
    neg_sales = (df["sales"] < 0).sum()
    if neg_sales > 0:
        logger.info("Dropped %d rows with negative sales (returns).", neg_sales)
        df = df[df["sales"] >= 0]

    # Keep only required columns (plus any extras the caller might want)
    core_cols = ["date", "product_id", "product_name", "sales"]
    df = df[core_cols]

    logger.info(
        "Column normalisation complete. Shape: %s | Products: %d",
        df.shape,
        df["product_id"].nunique(),
    )

    return df
