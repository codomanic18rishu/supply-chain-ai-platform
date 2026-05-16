import json

from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.models import ForecastHistory

router = APIRouter(
    prefix='/history',
    tags=['Forecast History'],
)


@router.get('/')
def get_history():
    db: Session = SessionLocal()

    try:
        records = (
            db.query(ForecastHistory)
            .order_by(ForecastHistory.created_at.desc())
            .all()
        )

        result = []

        for record in records:
            result.append({
                'id': record.id,
                'user_id': record.user_id,
                'model_used': record.model_used,
                'confidence': record.confidence,
                'forecast': json.loads(record.forecast_data),
                'insights': record.insights,
                'created_at': record.created_at.isoformat(),
            })

        return {
            'count': len(result),
            'history': result,
        }
    finally:
        db.close()
