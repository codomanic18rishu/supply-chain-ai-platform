from app.core.database import SessionLocal
from app.models.models import ForecastHistory


def save_forecast_history(
    user_id: int,
    forecast_data: str,
    insights: str,
    model_used: str = 'XGBoost',
    confidence: float = 0.93,
):
    db = SessionLocal()

    try:
        record = ForecastHistory(
            user_id=user_id,
            forecast_data=forecast_data,
            insights=insights,
            model_used=model_used,
            confidence=confidence,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return record
    finally:
        db.close()
