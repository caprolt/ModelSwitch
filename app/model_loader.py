import os
import time
import joblib
from typing import Dict, Optional, Any
from pathlib import Path

from .config import settings, get_model_path, get_available_versions
from .metrics import record_model_load_time, set_active_version


class ModelRegistry:
    """Manages model loading, caching, and version control."""
    
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._active_version: str = settings.default_version
        self._load_times: Dict[str, float] = {}
        
        # Set initial active version in metrics
        set_active_version(self._active_version)
    
    def get_model(self, version: Optional[str] = None) -> Any:
        """Get a model instance, loading it if necessary."""
        version = version or self._active_version
        
        if version not in self._models:
            self._load_model(version)
        
        return self._models[version]
    
    def _load_model(self, version: str) -> None:
        """Load a model from disk and cache it."""
        model_path = get_model_path(version)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        start_time = time.time()
        
        try:
            model = joblib.load(model_path)
            self._models[version] = model
            self._load_times[version] = time.time() - start_time
            
            # Record metrics
            record_model_load_time(version, self._load_times[version])
            
        except Exception as e:
            raise RuntimeError(f"Failed to load model {version}: {str(e)}")
    
    def set_active_version(self, version: str) -> bool:
        """Set the active model version."""
        # Verify the model exists
        model_path = get_model_path(version)
        if not os.path.exists(model_path):
            return False
        
        self._active_version = version
        set_active_version(version)
        return True
    
    def get_active_version(self) -> str:
        """Get the currently active version."""
        return self._active_version
    
    def get_available_versions(self) -> list[str]:
        """Get list of available model versions."""
        return get_available_versions()
    
    def is_version_loaded(self, version: str) -> bool:
        """Check if a model version is loaded in memory."""
        return version in self._models
    
    def get_load_time(self, version: str) -> Optional[float]:
        """Get the load time for a model version."""
        return self._load_times.get(version)
    
    def clear_cache(self, version: Optional[str] = None) -> None:
        """Clear model cache for a specific version or all versions."""
        if version:
            self._models.pop(version, None)
            self._load_times.pop(version, None)
        else:
            self._models.clear()
            self._load_times.clear()
    
    def get_model_info(self, version: str) -> Dict[str, Any]:
        """Get information about a model version."""
        model_path = get_model_path(version)
        
        info = {
            "version": version,
            "exists": os.path.exists(model_path),
            "loaded": version in self._models,
            "load_time": self._load_times.get(version),
            "active": version == self._active_version
        }
        
        if os.path.exists(model_path):
            stat = os.stat(model_path)
            info["file_size"] = stat.st_size
            info["modified_time"] = stat.st_mtime
        
        return info


# Global model registry instance
model_registry = ModelRegistry() 