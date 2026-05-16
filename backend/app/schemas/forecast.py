from typing import List

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    historical_sales: List[float] = Field(
        ...,
        min_length=7,
        description="At least 7 historical sales values",
    )
    periods: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Number of future periods to forecast",
    )


class ForecastResponse(BaseModel):
    forecast: List[float]
    model_used: str
    confidence: float