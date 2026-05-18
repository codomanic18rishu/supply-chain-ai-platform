"""
multi_product_schemas.py
------------------------
Placement: app/schemas/multi_product_schemas.py

Pydantic v2 response models for the POST /upload-multi-product-forecast/
endpoint. These models define the exact JSON contract between the backend
and frontend.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Per-product forecast
# ---------------------------------------------------------------------------

class ProductForecastSchema(BaseModel):
    product_id: str
    product_name: str
    forecast_dates: list[str]
    forecast_values: list[float]
    historical_dates: list[str]
    historical_values: list[float]
    avg_daily_demand: float
    demand_std: float
    demand_growth_rate: float
    total_projected_7d: float
    skipped: bool = False
    skip_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Top products summary row
# ---------------------------------------------------------------------------

class TopProductSchema(BaseModel):
    rank: int
    product_id: str
    product_name: str
    avg_daily_demand: float
    demand_std: float
    total_projected_7d: float
    demand_growth_rate: float
    demand_growth_pct: float


# ---------------------------------------------------------------------------
# Inventory metrics per product
# ---------------------------------------------------------------------------

class InventoryMetricSchema(BaseModel):
    product_id: str
    product_name: str
    avg_daily_demand: float
    demand_std: float
    safety_stock: float
    reorder_point: float
    reorder_quantity: float
    days_of_inventory: Optional[float] = None
    current_stock: Optional[float] = None
    lead_time_days: int
    service_level: float


# ---------------------------------------------------------------------------
# Risk alerts
# ---------------------------------------------------------------------------

class RiskAlertSchema(BaseModel):
    product_id: str
    product_name: str
    risk_type: str
    severity: str   # low / medium / high / critical
    message: str
    metric_value: Optional[float] = None
    recommended_action: Optional[str] = None


# ---------------------------------------------------------------------------
# AI insights
# ---------------------------------------------------------------------------

class AIInsightsSchema(BaseModel):
    urgent_actions: list[str] = Field(default_factory=list)
    fastest_growing: list[str] = Field(default_factory=list)
    optimization_recs: list[str] = Field(default_factory=list)
    risk_summary: list[str] = Field(default_factory=list)
    executive_summary: str = ""
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Skipped product info
# ---------------------------------------------------------------------------

class SkippedProductSchema(BaseModel):
    product_id: str
    product_name: str
    reason: str


# ---------------------------------------------------------------------------
# Top-level response
# ---------------------------------------------------------------------------

class MultiProductForecastResponse(BaseModel):
    """
    Full response from POST /upload-multi-product-forecast/

    Structure mirrors the processing pipeline:
      1. per-product forecast results (all products, including skipped)
      2. top-N products ranked by demand growth
      3. inventory optimisation metrics (non-skipped only)
      4. risk alerts (all severities, sorted critical→low)
      5. AI-generated insights
      6. metadata
    """

    # Forecast data
    products: list[ProductForecastSchema] = Field(
        default_factory=list,
        description="Per-product forecast results for all processed products.",
    )
    top_products: list[TopProductSchema] = Field(
        default_factory=list,
        description="Top N products ranked by projected demand growth rate.",
    )

    # Inventory & risk
    inventory_metrics: list[InventoryMetricSchema] = Field(
        default_factory=list,
        description="Inventory optimisation metrics for each processed product.",
    )
    risk_alerts: list[RiskAlertSchema] = Field(
        default_factory=list,
        description="Risk alerts sorted by severity (critical first).",
    )

    # AI insights
    ai_insights: AIInsightsSchema = Field(
        default_factory=AIInsightsSchema,
        description="OpenAI-generated supply chain insights.",
    )

    # Skipped / metadata
    skipped_products: list[SkippedProductSchema] = Field(
        default_factory=list,
        description="Products skipped due to insufficient data or errors.",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Processing metadata: counts, timing, config used.",
    )


# ---------------------------------------------------------------------------
# Request parameters (passed as form data alongside the file upload)
# ---------------------------------------------------------------------------

class MultiProductForecastParams(BaseModel):
    lead_time_days: int = Field(default=7, ge=1, le=365, description="Supplier lead time in days.")
    service_level: float = Field(default=0.95, ge=0.5, le=0.999, description="Desired service level (0.90–0.99).")
    top_n: int = Field(default=20, ge=1, le=100, description="Number of top products to return.")
    forecast_horizon: int = Field(default=7, ge=1, le=30, description="Forecast horizon in days.")
    max_products: int = Field(default=200, ge=1, le=1000, description="Maximum products to process (performance guard).")
