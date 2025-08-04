from typing import Dict, List, Any
from pydantic import BaseModel, Field

from .model_loader import model_registry
from .config import settings


class VersionRequest(BaseModel):
    """Request schema for setting active version."""
    version: str = Field(..., description="Model version to activate")


class VersionResponse(BaseModel):
    """Response schema for version operations."""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    active_version: str = Field(..., description="Currently active version")


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Service status")
    active_version: str = Field(..., description="Active model version")
    available_versions: List[str] = Field(..., description="Available model versions")
    models_loaded: int = Field(..., description="Number of models loaded in memory")


class ModelInfoResponse(BaseModel):
    """Model information response schema."""
    version: str = Field(..., description="Model version")
    exists: bool = Field(..., description="Whether model file exists")
    loaded: bool = Field(..., description="Whether model is loaded in memory")
    load_time: float = Field(None, description="Model load time in seconds")
    active: bool = Field(..., description="Whether this is the active version")
    file_size: int = Field(None, description="Model file size in bytes")
    modified_time: float = Field(None, description="Model file modification time")


async def set_active_version(request: VersionRequest) -> VersionResponse:
    """Set the active model version."""
    version = request.version
    
    # Check if version exists
    available_versions = model_registry.get_available_versions()
    if version not in available_versions:
        return VersionResponse(
            success=False,
            message=f"Version '{version}' not found. Available versions: {available_versions}",
            active_version=model_registry.get_active_version()
        )
    
    # Set active version
    success = model_registry.set_active_version(version)
    
    if success:
        return VersionResponse(
            success=True,
            message=f"Successfully switched to version '{version}'",
            active_version=version
        )
    else:
        return VersionResponse(
            success=False,
            message=f"Failed to switch to version '{version}'",
            active_version=model_registry.get_active_version()
        )


async def get_health_status() -> HealthResponse:
    """Get the health status of the service."""
    active_version = model_registry.get_active_version()
    available_versions = model_registry.get_available_versions()
    
    # Count loaded models
    loaded_count = sum(1 for version in available_versions 
                      if model_registry.is_version_loaded(version))
    
    # Determine overall status
    if not available_versions:
        status = "no_models"
    elif active_version not in available_versions:
        status = "no_active_model"
    else:
        status = "healthy"
    
    return HealthResponse(
        status=status,
        active_version=active_version,
        available_versions=available_versions,
        models_loaded=loaded_count
    )


async def get_model_info(version: str) -> ModelInfoResponse:
    """Get detailed information about a model version."""
    info = model_registry.get_model_info(version)
    
    return ModelInfoResponse(
        version=info["version"],
        exists=info["exists"],
        loaded=info["loaded"],
        load_time=info["load_time"],
        active=info["active"],
        file_size=info.get("file_size"),
        modified_time=info.get("modified_time")
    )


async def get_all_models_info() -> List[ModelInfoResponse]:
    """Get information about all available models."""
    available_versions = model_registry.get_available_versions()
    models_info = []
    
    for version in available_versions:
        info = await get_model_info(version)
        models_info.append(info)
    
    return models_info


async def clear_model_cache(version: str = None) -> Dict[str, Any]:
    """Clear model cache for a specific version or all versions."""
    model_registry.clear_cache(version)
    
    return {
        "success": True,
        "message": f"Cache cleared for {'all models' if version is None else f'version {version}'}",
        "cleared_version": version
    } 