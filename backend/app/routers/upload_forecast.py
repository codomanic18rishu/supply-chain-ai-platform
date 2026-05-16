import os
import tempfile
import json
import traceback

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.ml_forecasting_service import forecast_from_csv
from app.services.openai_service import generate_insights
from app.services.history_service import save_forecast_history

router = APIRouter(
    prefix='/upload-forecast',
    tags=['CSV ML Forecasting'],
)


@router.post('/')
async def upload_and_forecast(
    file: UploadFile = File(...),
    periods: int = 7,
):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail='Only CSV files are allowed',
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.csv',
        ) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        # Generate forecast
        result = forecast_from_csv(
            file_path=temp_path,
            periods=periods,
        )

        # Generate AI insights
        insights = generate_insights(result['forecast'])

        # Save to database (temporary fixed user_id)
        save_forecast_history(
            user_id=1,
            forecast_data=json.dumps(result['forecast']),
            insights=insights,
            model_used=result.get('model_used', 'XGBoost'),
            confidence=result.get('confidence', 0.93),
        )

        # Include insights in API response
        result['insights'] = insights

        return result

    except Exception as e:
        print('\n' + '=' * 60)
        print('UPLOAD FORECAST ERROR')
        print('=' * 60)
        traceback.print_exc()
        print('=' * 60 + '\n')

        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
