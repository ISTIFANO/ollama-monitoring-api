import asyncio
import httpx
import sys


async def warmup_model(
    api_url: str = "http://localhost:8000",
    model: str = "llama2",
    test_prompt: str = "Hello"
):
    """
    Warm up the Ollama model by sending a test request
    This helps load the model into memory before actual usage
    """
    print(f"Warming up model: {model}")
    print(f"API URL: {api_url}")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            # Check API health first
            health_response = await client.get(f"{api_url}/health")
            if health_response.status_code != 200:
                print("❌ API health check failed")
                sys.exit(1)
            print("✓ API is healthy")
            
            # Check Ollama health
            ollama_health = await client.get(f"{api_url}/health/ollama")
            if ollama_health.status_code != 200:
                print("❌ Ollama health check failed")
                sys.exit(1)
            print("✓ Ollama is healthy")
            
            # Send warmup request
            print(f"Sending warmup request with prompt: '{test_prompt}'")
            response = await client.post(
                f"{api_url}/chat",
                json={
                    "prompt": test_prompt,
                    "model": model
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Warmup successful!")
                print(f"  Response time: {data.get('duration_ms', 0):.2f}ms")
                print(f"  Model: {data.get('model')}")
            else:
                print(f"❌ Warmup failed with status code: {response.status_code}")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Error during warmup: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(warmup_model())
