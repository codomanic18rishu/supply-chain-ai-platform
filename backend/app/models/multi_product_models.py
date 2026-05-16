"""
multi_product_models.py
-----------------------
Placement: app/models/multi_product_models.py  (or add to your existing models.py)

Four new SQLAlchemy ORM models that persist multi-product forecast sessions.

Relationship summary:
  MultiProductSession  1──* ProductForecast
  MultiProductSession  1──* InventoryMetricRecord
  MultiProductSession  1──* RiskAlertRecord
  MultiProductSession  1──1  AIInsightRecord

Registration in database.py / models.py:
  Import this module and ensure Base.metadata.create_all(bind=engine) is called,
  or run the Alembic migration generated in Phase 2.

Usage from router (Phase 2 — uncomment the stub in multi_product_router.py):
  from app.models.multi_product_models import MultiProductSession, ...
"""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

# Import your existing Base and User model
from app.core.database import Base   # adjust import path to match your project


class MultiProductSession(Base):
    """
    One row per CSV upload / forecast run.
    Parent of all per-product and session-level records.
    """
    __tablename__ = "multi_product_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Metadata stored as JSON blob for flexibility
    metadata_json = Column(Text, nullable=True)   # stores the metadata dict

    # Relationships
    product_forecasts = relationship(
        "ProductForecast",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    inventory_metrics = relationship(
        "InventoryMetricRecord",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    risk_alerts = relationship(
        "RiskAlertRecord",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    ai_insight = relationship(
        "AIInsightRecord",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @property
    def metadata_dict(self) -> dict:
        if self.metadata_json:
            return json.loads(self.metadata_json)
        return {}


class ProductForecast(Base):
    """
    One row per product per session — stores forecast and historical series.
    """
    __tablename__ = "product_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("multi_product_sessions.id"), nullable=False, index=True)
    product_id = Column(String(100), nullable=False, index=True)
    product_name = Column(String(255), nullable=True)

    # Forecast output
    forecast_dates = Column(JSON, nullable=True)    # list[str]
    forecast_values = Column(JSON, nullable=True)   # list[float]
    historical_dates = Column(JSON, nullable=True)  # list[str]
    historical_values = Column(JSON, nullable=True) # list[float]

    # Derived metrics
    avg_daily_demand = Column(Float, nullable=True)
    demand_std = Column(Float, nullable=True)
    demand_growth_rate = Column(Float, nullable=True)
    total_projected_7d = Column(Float, nullable=True)

    skipped = Column(Boolean, default=False)
    skip_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    session = relationship("MultiProductSession", back_populates="product_forecasts")


class InventoryMetricRecord(Base):
    """
    Inventory optimisation metrics for one product within a session.
    """
    __tablename__ = "inventory_metric_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("multi_product_sessions.id"), nullable=False, index=True)
    product_id = Column(String(100), nullable=False)
    product_name = Column(String(255), nullable=True)

    avg_daily_demand = Column(Float, nullable=True)
    demand_std = Column(Float, nullable=True)
    safety_stock = Column(Float, nullable=True)
    reorder_point = Column(Float, nullable=True)
    reorder_quantity = Column(Float, nullable=True)
    days_of_inventory = Column(Float, nullable=True)
    current_stock = Column(Float, nullable=True)
    lead_time_days = Column(Integer, nullable=True)
    service_level = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("MultiProductSession", back_populates="inventory_metrics")


class RiskAlertRecord(Base):
    """
    Individual risk alert — one row per product-risk-type combination.
    """
    __tablename__ = "risk_alert_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("multi_product_sessions.id"), nullable=False, index=True)
    product_id = Column(String(100), nullable=False)
    product_name = Column(String(255), nullable=True)

    risk_type = Column(String(50), nullable=False)   # e.g. "stockout_risk"
    severity = Column(String(20), nullable=False)    # low / medium / high / critical
    message = Column(Text, nullable=True)
    metric_value = Column(Float, nullable=True)
    recommended_action = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("MultiProductSession", back_populates="risk_alerts")


class AIInsightRecord(Base):
    """
    Stores the OpenAI-generated insight sections for a session.
    Lists stored as JSON arrays; executive_summary as plain text.
    """
    __tablename__ = "ai_insight_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("multi_product_sessions.id"), nullable=False, unique=True)

    urgent_actions_json = Column(Text, nullable=True)    # JSON list
    fastest_growing_json = Column(Text, nullable=True)   # JSON list
    optimization_recs_json = Column(Text, nullable=True) # JSON list
    risk_summary_json = Column(Text, nullable=True)      # JSON list
    executive_summary = Column(Text, nullable=True)
    error = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("MultiProductSession", back_populates="ai_insight")

    # Convenience properties
    @property
    def urgent_actions(self) -> list:
        return json.loads(self.urgent_actions_json or "[]")

    @property
    def fastest_growing(self) -> list:
        return json.loads(self.fastest_growing_json or "[]")

    @property
    def optimization_recs(self) -> list:
        return json.loads(self.optimization_recs_json or "[]")

    @property
    def risk_summary(self) -> list:
        return json.loads(self.risk_summary_json or "[]")
