from prometheus_client import Counter, Histogram, Gauge, Info

# Request counters
request_counter = Counter(
    'ollama_requests_total',
    'Total number of requests to Ollama',
    ['method', 'endpoint', 'status']
)

# Latency histogram
request_latency = Histogram(
    'ollama_request_duration_seconds',
    'Request latency in seconds',
    ['method', 'endpoint']
)

# Active requests gauge
active_requests = Gauge(
    'ollama_active_requests',
    'Number of active requests to Ollama'
)

# Error counter
error_counter = Counter(
    'ollama_errors_total',
    'Total number of errors',
    ['error_type']
)

# Model info
model_info = Info(
    'ollama_model',
    'Information about the Ollama model'
)

# Token metrics
tokens_processed = Counter(
    'ollama_tokens_processed_total',
    'Total number of tokens processed',
    ['model']
)


def initialize_metrics():
    """Initialize metrics with default values"""
    model_info.info({'model': 'llama2', 'version': '1.0'})
