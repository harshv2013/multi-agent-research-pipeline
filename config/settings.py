"""
Production-grade configuration management using Pydantic Settings.
"""
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation."""
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: str = Field(
        ..., 
        description="Azure OpenAI endpoint URL"
    )
    azure_openai_api_key: str = Field(
        ..., 
        description="Azure OpenAI API key"
    )
    azure_openai_api_version: str = Field(
        default="2024-02-15-preview",
        description="Azure OpenAI API version"
    )
    azure_openai_deployment_name: str = Field(
        default="gpt-4",
        description="Azure OpenAI deployment name"
    )
    
    # Tavily Search API
    tavily_api_key: str = Field(
        ...,
        description="Tavily API key for web search"
    )
    
    # Model Configuration
    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperature for model responses"
    )
    llm_max_tokens: int = Field(
        default=4000,
        ge=1,
        le=128000,
        description="Maximum tokens per request"
    )
    llm_top_p: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Top-p sampling parameter"
    )
    
    # Agent Configuration
    max_iterations: int = Field(
        default=15,
        ge=1,
        le=50,
        description="Maximum iterations for agent reasoning loops"
    )
    timeout_seconds: int = Field(
        default=300,
        ge=10,
        description="Timeout for agent execution in seconds"
    )
    
    # Rate Limiting
    requests_per_minute: int = Field(
        default=60,
        ge=1,
        description="Maximum API requests per minute"
    )
    tokens_per_minute: int = Field(
        default=150000,
        ge=1000,
        description="Maximum tokens per minute"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_file: str = Field(
        default="logs/agent_pipeline.log",
        description="Log file path"
    )
    
    # Optional: Redis Configuration
    redis_host: str = Field(
        default="localhost",
        description="Redis host for distributed checkpointing"
    )
    redis_port: int = Field(
        default=6379,
        description="Redis port"
    )
    redis_db: int = Field(
        default=0,
        description="Redis database number"
    )
    
    # Feature Flags
    enable_streaming: bool = Field(
        default=True,
        description="Enable streaming responses"
    )
    enable_human_in_loop: bool = Field(
        default=False,
        description="Enable human-in-the-loop intervention points"
    )
    enable_visualization: bool = Field(
        default=True,
        description="Enable graph visualization"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=()
    )
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper
    
    @field_validator("azure_openai_endpoint")
    @classmethod
    def validate_endpoint(cls, v: str) -> str:
        """Ensure endpoint has proper format."""
        if not v.startswith("https://"):
            raise ValueError("azure_openai_endpoint must start with https://")
        if not v.endswith("/"):
            v = v + "/"
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get settings singleton instance."""
    return Settings()