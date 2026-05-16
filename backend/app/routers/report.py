import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

from app.core.database import SessionLocal
from app.models.models import ForecastHistory

router = APIRouter(
    prefix='/report',
    tags=['PDF Reports'],
)


@router.get('/history.pdf')
def export_history_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    story = []

    db = SessionLocal()

    try:
        records = (
            db.query(ForecastHistory)
            .order_by(ForecastHistory.created_at.desc())
            .all()
        )

        story.append(
            Paragraph(
                'Supply Chain AI - Forecast History Report',
                styles['Title'],
            )
        )
        story.append(Spacer(1, 24))

        for record in records:
            block = [
                Paragraph(
                    f'Forecast #{record.id}',
                    styles['Heading2'],
                ),
                Paragraph(
                    f'Model: {record.model_used}',
                    styles['BodyText'],
                ),
                Paragraph(
                    f'Confidence: {record.confidence}',
                    styles['BodyText'],
                ),
                Paragraph(
                    f'Date: {record.created_at}',
                    styles['BodyText'],
                ),
                Paragraph(
                    f'Insights: {record.insights}',
                    styles['BodyText'],
                ),
                Spacer(1, 18),
            ]

            story.append(KeepTogether(block))

        doc.build(story)
        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type='application/pdf',
            headers={
                'Content-Disposition':
                    'attachment; filename=forecast_history.pdf'
            },
        )
    finally:
        db.close()
