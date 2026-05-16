from fastapi import APIRouter
from pydantic import BaseModel

from app.services.openai_service import generate_insights

router = APIRouter(
    prefix="/insights",
    tags=["AI Insights"],
)


class InsightsRequest(BaseModel):
    forecast: list[float]


@router.post("/")
def create_insights(request: InsightsRequest):
    insights = generate_insights(request.forecast)

    return {
        "insights": insights
    }
