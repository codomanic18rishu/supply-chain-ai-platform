"""
risk_detector.py
----------------
Placement: app/services/risk_detector.py

Detects supply chain risk signals for each product and emits structured
risk alerts. Four risk types are detected:

1. stockout_risk     – demand >= reorder point and no restock action
2. overstock_risk    – days of inventory exceeds threshold (default 60 d)
3. demand_spike      – growth rate exceeds spike threshold (default +50 %)
4. declining_demand  – growth rate below decline threshold (default -20 %)

Each alert has a severity level: low / medium / high / critical.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Thresholds (tune per business need)
# ---------------------------------------------------------------------------
STOCKOUT_DAYS_CRITICAL = 3     # days of stock remaining → critical
STOCKOUT_DAYS_HIGH = 7         # → high
STOCKOUT_DAYS_MEDIUM = 14      # → medium
OVERSTOCK_DAYS_MEDIUM = 60     # days of inventory above which → overstock
OVERSTOCK_DAYS_HIGH = 120
SPIKE_GROWTH_MEDIUM = 0.30     # +30 % growth → medium spike
SPIKE_GROWTH_HIGH = 0.50       # +50 % growth → high spike
SPIKE_GROWTH_CRITICAL = 1.00   # +100 % growth → critical spike
DECLINE_MEDIUM = -0.20         # -20 % → medium decline
DECLINE_HIGH = -0.40           # -40 % → high decline


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(str, Enum):
    STOCKOUT = "stockout_risk"
    OVERSTOCK = "overstock_risk"
    DEMAND_SPIKE = "demand_spike"
    DECLINING_DEMAND = "declining_demand"


@dataclass
class RiskAlert:
    product_id: str
    product_name: str
    risk_type: RiskType
    severity: RiskLevel
    message: str
    metric_value: Optional[float] = None   # the value that triggered the alert
    recommended_action: Optional[str] = None


@dataclass
class RiskDetectionResult:
    alerts: list[RiskAlert] = field(default_factory=list)
    high_priority_count: int = 0   # high + critical alerts
    products_at_risk: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Individual risk checks
# ---------------------------------------------------------------------------

def _check_stockout(
    product_id: str,
    product_name: str,
    days_of_inventory: Optional[float],
    reorder_point: float,
    avg_daily_demand: float,
) -> Optional[RiskAlert]:
    """Flag products where current stock is critically low."""
    if days_of_inventory is None:
        return None

    if days_of_inventory <= STOCKOUT_DAYS_CRITICAL:
        severity = RiskLevel.CRITICAL
        action = "Emergency restock required immediately."
    elif days_of_inventory <= STOCKOUT_DAYS_HIGH:
        severity = RiskLevel.HIGH
        action = "Place replenishment order today."
    elif days_of_inventory <= STOCKOUT_DAYS_MEDIUM:
        severity = RiskLevel.MEDIUM
        action = "Monitor closely and plan reorder."
    else:
        return None

    return RiskAlert(
        product_id=product_id,
        product_name=product_name,
        risk_type=RiskType.STOCKOUT,
        severity=severity,
        message=(
            f"Only {days_of_inventory:.1f} days of inventory remaining. "
            f"Reorder point is {reorder_point:.0f} units."
        ),
        metric_value=days_of_inventory,
        recommended_action=action,
    )


def _check_overstock(
    product_id: str,
    product_name: str,
    days_of_inventory: Optional[float],
) -> Optional[RiskAlert]:
    """Flag products with excess inventory tying up capital."""
    if days_of_inventory is None:
        return None

    if days_of_inventory >= OVERSTOCK_DAYS_HIGH:
        severity = RiskLevel.HIGH
        action = "Consider promotions or liquidation to reduce holding costs."
    elif days_of_inventory >= OVERSTOCK_DAYS_MEDIUM:
        severity = RiskLevel.MEDIUM
        action = "Pause replenishment orders; evaluate demand trend."
    else:
        return None

    return RiskAlert(
        product_id=product_id,
        product_name=product_name,
        risk_type=RiskType.OVERSTOCK,
        severity=severity,
        message=f"{days_of_inventory:.1f} days of inventory on hand — excess stock detected.",
        metric_value=days_of_inventory,
        recommended_action=action,
    )


def _check_demand_spike(
    product_id: str,
    product_name: str,
    growth_rate: float,
    total_projected_7d: float,
) -> Optional[RiskAlert]:
    """Flag sudden upward demand surges that may cause stockouts."""
    if growth_rate >= SPIKE_GROWTH_CRITICAL:
        severity = RiskLevel.CRITICAL
        action = "Expedite restock; demand has more than doubled."
    elif growth_rate >= SPIKE_GROWTH_HIGH:
        severity = RiskLevel.HIGH
        action = "Increase reorder quantity significantly."
    elif growth_rate >= SPIKE_GROWTH_MEDIUM:
        severity = RiskLevel.MEDIUM
        action = "Review reorder point — demand is trending up."
    else:
        return None

    return RiskAlert(
        product_id=product_id,
        product_name=product_name,
        risk_type=RiskType.DEMAND_SPIKE,
        severity=severity,
        message=(
            f"Demand forecast shows a {growth_rate * 100:.0f}% surge. "
            f"Projected 7-day sales: {total_projected_7d:.0f} units."
        ),
        metric_value=round(growth_rate * 100, 1),
        recommended_action=action,
    )


def _check_declining_demand(
    product_id: str,
    product_name: str,
    growth_rate: float,
) -> Optional[RiskAlert]:
    """Flag products with significantly declining demand."""
    if growth_rate <= DECLINE_HIGH:
        severity = RiskLevel.HIGH
        action = "Reduce safety stock; investigate root cause of decline."
    elif growth_rate <= DECLINE_MEDIUM:
        severity = RiskLevel.MEDIUM
        action = "Monitor trend; consider promotional activity."
    else:
        return None

    return RiskAlert(
        product_id=product_id,
        product_name=product_name,
        risk_type=RiskType.DECLINING_DEMAND,
        severity=severity,
        message=f"Demand is declining at {abs(growth_rate) * 100:.0f}% below recent levels.",
        metric_value=round(growth_rate * 100, 1),
        recommended_action=action,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_risks(
    product_forecasts: list[dict],      # from MultiProductForecastOutput.top_products or all products
    inventory_metrics: list[dict],      # from InventoryOptimizationResult serialized
) -> RiskDetectionResult:
    """
    Cross-reference forecast data with inventory metrics to produce risk alerts.

    Parameters
    ----------
    product_forecasts:
        List of dicts with keys: product_id, product_name,
        demand_growth_rate, total_projected_7d.
    inventory_metrics:
        List of dicts with keys: product_id, product_name,
        days_of_inventory, reorder_point, avg_daily_demand.
    """
    # Index inventory metrics by product_id for fast lookup
    inv_index: dict[str, dict] = {m["product_id"]: m for m in inventory_metrics}

    result = RiskDetectionResult()

    for pf in product_forecasts:
        pid = pf["product_id"]
        pname = pf["product_name"]
        growth_rate = pf.get("demand_growth_rate", 0.0)
        projected_7d = pf.get("total_projected_7d", 0.0)
        inv = inv_index.get(pid, {})

        doi = inv.get("days_of_inventory")          # may be None
        rop = inv.get("reorder_point", 0.0)
        avg_demand = inv.get("avg_daily_demand", pf.get("avg_daily_demand", 0.0))

        alerts_for_product: list[RiskAlert] = []

        for checker_result in [
            _check_stockout(pid, pname, doi, rop, avg_demand),
            _check_overstock(pid, pname, doi),
            _check_demand_spike(pid, pname, growth_rate, projected_7d),
            _check_declining_demand(pid, pname, growth_rate),
        ]:
            if checker_result is not None:
                alerts_for_product.append(checker_result)

        if alerts_for_product:
            result.alerts.extend(alerts_for_product)
            result.products_at_risk.append(pid)

    # Count high-priority alerts
    result.high_priority_count = sum(
        1 for a in result.alerts
        if a.severity in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    )

    # Sort: critical first, then high, medium, low
    severity_order = {
        RiskLevel.CRITICAL: 0,
        RiskLevel.HIGH: 1,
        RiskLevel.MEDIUM: 2,
        RiskLevel.LOW: 3,
    }
    result.alerts.sort(key=lambda a: severity_order[a.severity])

    logger.info(
        "Risk detection complete. Alerts: %d | High-priority: %d | Products at risk: %d",
        len(result.alerts),
        result.high_priority_count,
        len(result.products_at_risk),
    )
    return result
