import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Model settings
    models_dir: str = Field(default="models", env="MODELS_DIR")
    default_version: str = Field(default="v1", env="DEFAULT_VERSION")
    
    # Redis settings (optional)
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    redis_enabled: bool = Field(default=False, env="REDIS_ENABLED")
    
    # Monitoring settings
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    
    # CORS settings
    cors_origins: list = Field(default=["*"], env="CORS_ORIGINS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_model_path(version: str) -> str:
    """Get the full path to a model version."""
    return os.path.join(settings.models_dir, version, "model.pkl")


def get_available_versions() -> list[str]:
    """Get list of available model versions."""
    if not os.path.exists(settings.models_dir):
        return []
    
    versions = []
    for item in os.listdir(settings.models_dir):
        model_path = get_model_path(item)
        if os.path.exists(model_path):
            versions.append(item)
    
    return sorted(versions) 