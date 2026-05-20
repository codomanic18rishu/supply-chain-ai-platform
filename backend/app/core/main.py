from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.models import models
from app.routers import auth, forecast, upload_forecast

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Supply Chain AI Platform",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:5173/"],
    allow_methods=["*", "http://localhost:5173/"],
    allow_headers=["*", "http://localhost:5173/"],
    allow_credentials=False,
)

# Register routers
app.include_router(auth.router)
app.include_router(forecast.router)
app.include_router(upload_forecast.router)


@app.get("/")
def root():
    return {
        "message": "Supply Chain AI Platform API is running successfully!"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy api route"
    }


@app.get("/cors-test")
def cors_test():
    return {
        "message": "CORS middleware is active"
    }