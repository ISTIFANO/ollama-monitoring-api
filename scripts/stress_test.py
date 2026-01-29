import asyncio
import httpx
import time
from typing import List
import statistics


async def send_request(client: httpx.AsyncClient, url: str, prompt: str) -> dict:
    """Send a single request to the API"""
    start = time.time()
    try:
        response = await client.post(
            f"{url}/chat",
            json={"prompt": prompt},
            timeout=300.0
        )
        duration = time.time() - start
        return {
            "status": response.status_code,
            "duration": duration,
            "success": response.status_code == 200
        }
    except Exception as e:
        duration = time.time() - start
        return {
            "status": 0,
            "duration": duration,
            "success": False,
            "error": str(e)
        }


async def stress_test(
    url: str = "http://localhost:8000",
    num_requests: int = 100,
    concurrency: int = 10,
    prompt: str = "What is the meaning of life?"
):
    """Run a stress test against the API"""
    print(f"Starting stress test with {num_requests} requests, concurrency: {concurrency}")
    
    async with httpx.AsyncClient() as client:
        # Create batches of requests
        results: List[dict] = []
        
        for i in range(0, num_requests, concurrency):
            batch_size = min(concurrency, num_requests - i)
            tasks = [
                send_request(client, url, prompt)
                for _ in range(batch_size)
            ]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            print(f"Completed {i + batch_size}/{num_requests} requests")
    
    # Calculate statistics
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    durations = [r["duration"] for r in successful]
    
    print("\n=== Stress Test Results ===")
    print(f"Total requests: {num_requests}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if durations:
        print(f"\nLatency Statistics (seconds):")
        print(f"  Min: {min(durations):.2f}")
        print(f"  Max: {max(durations):.2f}")
        print(f"  Mean: {statistics.mean(durations):.2f}")
        print(f"  Median: {statistics.median(durations):.2f}")
        if len(durations) > 1:
            print(f"  Std Dev: {statistics.stdev(durations):.2f}")


if __name__ == "__main__":
    asyncio.run(stress_test(
        url="http://localhost:8000",
        num_requests=50,
        concurrency=5,
        prompt="Hello, how are you?"
    ))
