from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.models import models
from app.routers import (

    auth,
    forecast,
    upload_forecast,
    insights,
    history,
    report,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title='Supply Chain AI Platform',
    version='1.0.0',
)

origins = [
    "http://localhost:5173",
    "https://supply-chain-ai-platform-kappa.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(forecast.router)
app.include_router(upload_forecast.router)
app.include_router(insights.router)
app.include_router(history.router)
app.include_router(report.router)


@app.get('/')
def root():
    return {
        'message': 'Supply Chain AI Platform API is running successfully!'
    }


@app.get('/health')
def health():
    return {
        'status': 'healthy'
    }


@app.get('/cors-test')
def cors_test():
    return {
        'message': 'CORS middleware is active'
    }



