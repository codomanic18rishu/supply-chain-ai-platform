"""
inventory_optimizer.py
----------------------
Placement: app/services/inventory_optimizer.py

Calculates inventory management metrics for each product using
standard supply chain formulas.

Formulas used
-------------
  Safety Stock   = Z * σ_demand * sqrt(lead_time)
  Reorder Point  = (avg_demand * lead_time) + safety_stock
  Reorder Qty    = EOQ  ≈  sqrt(2 * avg_demand * order_cost / holding_cost_rate)
  Days on Hand   = current_inventory / avg_daily_demand   (when stock provided)

Service level → Z-score mapping
--------------------------------
  90% → 1.28
  95% → 1.645   (default)
  98% → 2.055
  99% → 2.326

All monetary assumptions are configurable; sensible defaults are provided
so the endpoint works without the caller supplying cost parameters.
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------
DEFAULT_LEAD_TIME_DAYS: int = 7       # days from order to receipt
DEFAULT_SERVICE_LEVEL: float = 0.95   # 95 % service level → Z ≈ 1.645
DEFAULT_ORDER_COST: float = 50.0      # fixed cost per order (USD)
DEFAULT_HOLDING_COST_RATE: float = 0.25  # 25 % of unit value per year
DEFAULT_UNIT_VALUE: float = 10.0      # assumed unit value when unknown

SERVICE_LEVEL_Z: dict[float, float] = {
    0.90: 1.281,
    0.95: 1.645,
    0.98: 2.055,
    0.99: 2.326,
}


def _z_score(service_level: float) -> float:
    """Return Z-score for the nearest configured service level."""
    closest = min(SERVICE_LEVEL_Z.keys(), key=lambda k: abs(k - service_level))
    return SERVICE_LEVEL_Z[closest]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class InventoryMetrics:
    product_id: str
    product_name: str
    avg_daily_demand: float           # units/day
    demand_std: float                 # std dev of daily demand
    safety_stock: float               # units
    reorder_point: float              # units
    reorder_quantity: float           # units (EOQ-based)
    days_of_inventory: Optional[float] = None   # only when current_stock provided
    current_stock: Optional[float] = None
    lead_time_days: int = DEFAULT_LEAD_TIME_DAYS
    service_level: float = DEFAULT_SERVICE_LEVEL


@dataclass
class InventoryOptimizationResult:
    metrics: list[InventoryMetrics] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Core calculation
# ---------------------------------------------------------------------------

def _calc_safety_stock(
    demand_std: float,
    lead_time_days: int,
    z: float,
) -> float:
    """Safety stock = Z × σ_demand × √(lead_time)."""
    return z * demand_std * math.sqrt(lead_time_days)


def _calc_reorder_point(
    avg_daily_demand: float,
    lead_time_days: int,
    safety_stock: float,
) -> float:
    """ROP = (avg_demand × lead_time) + safety_stock."""
    return (avg_daily_demand * lead_time_days) + safety_stock


def _calc_eoq(
    avg_daily_demand: float,
    order_cost: float,
    holding_cost_rate: float,
    unit_value: float,
) -> float:
    """
    Economic Order Quantity (Wilson formula).
    EOQ = sqrt(2 × D × S / H)
    where D = annual demand, S = order cost, H = annual holding cost per unit.
    """
    annual_demand = avg_daily_demand * 365.0
    holding_cost_per_unit = holding_cost_rate * unit_value
    if holding_cost_per_unit <= 0 or annual_demand <= 0:
        return 1.0
    return math.sqrt((2 * annual_demand * order_cost) / holding_cost_per_unit)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def calculate_inventory_metrics(
    product_forecasts: list[dict],               # list of ProductForecastResult-like dicts
    lead_time_days: int = DEFAULT_LEAD_TIME_DAYS,
    service_level: float = DEFAULT_SERVICE_LEVEL,
    order_cost: float = DEFAULT_ORDER_COST,
    holding_cost_rate: float = DEFAULT_HOLDING_COST_RATE,
    unit_value: float = DEFAULT_UNIT_VALUE,
    current_stock_map: Optional[dict[str, float]] = None,  # product_id -> stock
) -> InventoryOptimizationResult:
    """
    Compute inventory metrics for each product.

    Parameters
    ----------
    product_forecasts:
        List of dicts with keys: product_id, product_name,
        avg_daily_demand, demand_std.
    lead_time_days:
        Supplier lead time in days.
    service_level:
        Desired service level (0.90 / 0.95 / 0.98 / 0.99).
    order_cost:
        Fixed cost per replenishment order (USD).
    holding_cost_rate:
        Annual holding cost as fraction of unit value.
    unit_value:
        Assumed unit value (USD) when not provided.
    current_stock_map:
        Optional mapping of product_id → current inventory level.
    """
    z = _z_score(service_level)
    metrics_list: list[InventoryMetrics] = []

    for pf in product_forecasts:
        pid = pf["product_id"]
        pname = pf["product_name"]
        avg_demand = pf.get("avg_daily_demand", 0.0)
        demand_std = pf.get("demand_std", 0.0)

        if avg_demand <= 0:
            logger.warning("Product '%s' has zero avg demand; skipping inventory calc.", pid)
            continue

        ss = _calc_safety_stock(demand_std, lead_time_days, z)
        rop = _calc_reorder_point(avg_demand, lead_time_days, ss)
        eoq = _calc_eoq(avg_demand, order_cost, holding_cost_rate, unit_value)

        current_stock = (current_stock_map or {}).get(pid)
        doi: Optional[float] = None
        if current_stock is not None and avg_demand > 0:
            doi = current_stock / avg_demand

        metrics = InventoryMetrics(
            product_id=pid,
            product_name=pname,
            avg_daily_demand=round(avg_demand, 4),
            demand_std=round(demand_std, 4),
            safety_stock=round(ss, 2),
            reorder_point=round(rop, 2),
            reorder_quantity=round(eoq, 2),
            days_of_inventory=round(doi, 1) if doi is not None else None,
            current_stock=current_stock,
            lead_time_days=lead_time_days,
            service_level=service_level,
        )
        metrics_list.append(metrics)

    logger.info("Inventory metrics calculated for %d products.", len(metrics_list))
    return InventoryOptimizationResult(metrics=metrics_list)
