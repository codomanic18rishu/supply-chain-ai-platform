from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)

    forecasts = relationship('ForecastHistory', back_populates='user')


class ForecastHistory(Base):
    __tablename__ = 'forecast_history'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    model_used = Column(String, default='XGBoost')
    confidence = Column(Float, default=0.93)
    forecast_data = Column(Text)
    insights = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship('User', back_populates='forecasts')
