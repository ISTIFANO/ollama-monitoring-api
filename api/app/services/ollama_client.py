import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.utils.retry import retry_with_backoff


class OllamaClient:
    """Client for communicating with Ollama API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=settings.api_timeout)
    
    async def check_health(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    @retry_with_backoff(max_retries=settings.max_retries, delay=settings.retry_delay)
    async def generate(
        self,
        model: str,
        prompt: str,
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a response from Ollama"""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }
        
        if options:
            payload["options"] = options
        
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def list_models(self) -> Dict[str, Any]:
        """List available models"""
        response = await self.client.get(f"{self.base_url}/api/tags")
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
