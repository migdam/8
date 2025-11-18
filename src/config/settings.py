"""Settings and configuration management for Deep Agents v2"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    langchain_api_key: Optional[str] = None

    # LangChain Settings
    langchain_tracing_v2: bool = False
    langchain_project: str = "deep-agents-v2"

    # Agent Configuration
    agent_model: str = "gpt-4-turbo-preview"
    agent_temperature: float = 0.7
    max_iterations: int = 10
    max_execution_time: int = 300  # seconds

    # Memory Configuration
    memory_type: str = "sqlite"
    memory_path: str = "./data/agent_memory.db"

    # Logging
    log_level: str = "INFO"

    # Advanced Settings
    enable_parallel_execution: bool = True
    max_parallel_agents: int = 5
    checkpoint_dir: str = "./checkpoints"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def validate_api_keys(self) -> bool:
        """Validate that at least one LLM API key is configured"""
        return bool(self.openai_api_key or self.anthropic_api_key)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
