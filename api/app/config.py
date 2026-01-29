from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration"""
    
    # Ollama configuration
    ollama_url: str = "http://localhost:11434"
    # Configuration pour 6GB RAM: qwen2.5:7b-instruct-q4_0 (qwen-8b quantifié)
    # Taille mémoire: ~4.4-4.7GB selon quantization
    ollama_model: str = "qwen2.5:7b-instruct-q4_0"
    
    # API configuration
    api_timeout: int = 300
    max_retries: int = 3
    retry_delay: int = 1
    
    # Rate limiting
    max_requests_per_minute: int = 60
    
    # Memory optimization settings
    # Contexte adapté pour qwen-8b (6GB RAM)
    max_context_length: int = 4096
    # Streaming disponible avec 6GB RAM
    enable_streaming: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
