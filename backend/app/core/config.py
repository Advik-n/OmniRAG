from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./omnirag.db"
    storage_dir: str = "./storage"
    embedding_model: str = "BAAI/bge-base-en"
    llm_provider: str = "offline"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"
    custom_llm_endpoint: str = ""
    default_chunk_size: int = 800
    default_chunk_overlap: int = 150
    default_top_k: int = 5
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
