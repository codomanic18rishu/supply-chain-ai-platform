from fastapi import APIRouter
from app.schemas.forecast import ForecastRequest, ForecastResponse
from app.services.forecasting_service import generate_forecast

router = APIRouter(
    prefix="/forecast",
    tags=["Demand Forecasting"]
)

@router.post("/", response_model=ForecastResponse)
def create_forecast(request: ForecastRequest):
    return generate_forecast(
        historical_sales=request.historical_sales,
        periods=request.periods
    )
