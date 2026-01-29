from fastapi import APIRouter, HTTPException
from app.services.ollama_client import OllamaClient
from app.config import settings

router = APIRouter()
ollama_client = OllamaClient(settings.ollama_url)


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ollama-monitoring-api"
    }


@router.get("/health/ollama")
async def ollama_health_check():
    """Check Ollama service health"""
    try:
        is_healthy = await ollama_client.check_health()
        if is_healthy:
            return {
                "status": "healthy",
                "service": "ollama",
                "url": settings.ollama_url
            }
        else:
            raise HTTPException(status_code=503, detail="Ollama service is unhealthy")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to connect to Ollama: {str(e)}")
