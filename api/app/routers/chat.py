from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.ollama_client import OllamaClient
from app.config import settings
from app.utils.timers import timer_context
from app.metrics import request_counter, request_latency, active_requests, error_counter

router = APIRouter()
ollama_client = OllamaClient(settings.ollama_url)


class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    model: str
    duration_ms: float


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a chat request to Ollama"""
    model = request.model or settings.ollama_model
    
    active_requests.inc()
    try:
        with timer_context() as timer:
            with request_latency.labels(method="POST", endpoint="/chat").time():
                response = await ollama_client.generate(
                    model=model,
                    prompt=request.prompt,
                    stream=request.stream
                )
        
        request_counter.labels(method="POST", endpoint="/chat", status="success").inc()
        
        return ChatResponse(
            response=response.get("response", ""),
            model=model,
            duration_ms=timer.duration_ms
        )
    
    except Exception as e:
        error_counter.labels(error_type=type(e).__name__).inc()
        request_counter.labels(method="POST", endpoint="/chat", status="error").inc()
        raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")
    
    finally:
        active_requests.dec()
