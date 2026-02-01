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


class StructuredChatRequest(BaseModel):
    query: str
    model: Optional[str] = None
    stream: bool = False
    rules: Optional[str] = None
    context: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    model: str
    duration_ms: float


def build_structured_prompt(query: str, rules: Optional[str] = None, context: Optional[str] = None) -> str:
    """Build a structured prompt with rules, context, and user query"""
    
    default_rules = """RULES:
- Provide concise and accurate answers
- Use professional technical language
- Focus on practical information
- Keep responses under 3 sentences unless asked otherwise
- Always provide examples when relevant"""

    default_context = """
CONTEXT:
You are an AI assistant specialized in DevOps, MLOps, and cloud technologies.
Your expertise includes Docker, Kubernetes, monitoring systems, and API development.
You help developers understand and implement modern infrastructure solutions."""

    final_rules = rules if rules else default_rules
    final_context = context if context else default_context
    
    structured_prompt = f"""{final_rules}

{final_context}

USER QUERY:
{query}"""
    
    return structured_prompt


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


@router.post("/chat/structured", response_model=ChatResponse)
async def chat_structured(request: StructuredChatRequest):
    """Send a structured chat request to Ollama with rules and context"""
    model = request.model or settings.ollama_model
    
    # Build the structured prompt
    structured_prompt = build_structured_prompt(
        query=request.query,
        rules=request.rules,
        context=request.context
    )
    
    active_requests.inc()
    try:
        with timer_context() as timer:
            with request_latency.labels(method="POST", endpoint="/chat/structured").time():
                response = await ollama_client.generate(
                    model=model,
                    prompt=structured_prompt,
                    stream=request.stream
                )
        
        request_counter.labels(method="POST", endpoint="/chat/structured", status="success").inc()
        
        return ChatResponse(
            response=response.get("response", ""),
            model=model,
            duration_ms=timer.duration_ms
        )
    
    except Exception as e:
        error_counter.labels(error_type=type(e).__name__).inc()
        request_counter.labels(method="POST", endpoint="/chat/structured", status="error").inc()
        raise HTTPException(status_code=500, detail=f"Error communicating with Ollama: {str(e)}")
    
    finally:
        active_requests.dec()
