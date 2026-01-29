from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.config import settings
from app.routers import health, chat
from app.metrics import initialize_metrics

app = FastAPI(
    title="Ollama Monitoring API",
    description="API with monitoring for Ollama interactions",
    version="1.0.0"
)

# Initialize Prometheus metrics
initialize_metrics()

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, tags=["Chat"])


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Expose Prometheus metrics"""
    return generate_latest()


@app.get("/")
async def root():
    return {
        "message": "Ollama Monitoring API",
        "version": "1.0.0",
        "docs": "/docs"
    }
