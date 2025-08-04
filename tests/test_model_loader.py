import pytest
import os
import tempfile
import joblib
from unittest.mock import patch, MagicMock

from app.model_loader import ModelRegistry
from app.config import get_model_path, get_available_versions


class TestModelRegistry:
    """Test cases for ModelRegistry class."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.registry = ModelRegistry()
        self.registry._models = {}  # Clear cache
        self.registry._load_times = {}
        
        # Create test models directory
        os.makedirs(os.path.join(self.temp_dir, "v1"), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, "v2"), exist_ok=True)
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_model_path(self):
        """Test model path generation."""
        path = get_model_path("v1")
        assert path.endswith("models/v1/model.pkl")
    
    def test_get_available_versions_empty(self):
        """Test getting available versions when none exist."""
        with patch('app.config.settings') as mock_settings:
            mock_settings.models_dir = self.temp_dir
            versions = get_available_versions()
            assert versions == []
    
    def test_get_available_versions_with_models(self):
        """Test getting available versions when models exist."""
        # Create test model files
        model1_path = os.path.join(self.temp_dir, "v1", "model.pkl")
        model2_path = os.path.join(self.temp_dir, "v2", "model.pkl")
        
        # Create dummy model files
        joblib.dump({"test": "model1"}, model1_path)
        joblib.dump({"test": "model2"}, model2_path)
        
        with patch('app.config.settings') as mock_settings:
            mock_settings.models_dir = self.temp_dir
            versions = get_available_versions()
            assert "v1" in versions
            assert "v2" in versions
            assert len(versions) == 2
    
    def test_load_model_success(self):
        """Test successful model loading."""
        # Create test model
        model_path = os.path.join(self.temp_dir, "v1", "model.pkl")
        test_model = {"test": "data"}
        joblib.dump(test_model, model_path)
        
        with patch('app.config.get_model_path') as mock_path:
            mock_path.return_value = model_path
            
            model = self.registry.get_model("v1")
            assert model == test_model
            assert "v1" in self.registry._models
            assert "v1" in self.registry._load_times
    
    def test_load_model_not_found(self):
        """Test model loading when file doesn't exist."""
        with patch('app.config.get_model_path') as mock_path:
            mock_path.return_value = "nonexistent/path/model.pkl"
            
            with pytest.raises(FileNotFoundError):
                self.registry.get_model("v1")
    
    def test_set_active_version_success(self):
        """Test successful version switching."""
        # Create test model
        model_path = os.path.join(self.temp_dir, "v1", "model.pkl")
        joblib.dump({"test": "data"}, model_path)
        
        with patch('app.config.get_model_path') as mock_path:
            mock_path.return_value = model_path
            
            success = self.registry.set_active_version("v1")
            assert success is True
            assert self.registry.get_active_version() == "v1"
    
    def test_set_active_version_not_found(self):
        """Test version switching when model doesn't exist."""
        with patch('app.config.get_model_path') as mock_path:
            mock_path.return_value = "nonexistent/path/model.pkl"
            
            success = self.registry.set_active_version("v1")
            assert success is False
    
    def test_get_model_info(self):
        """Test getting model information."""
        # Create test model
        model_path = os.path.join(self.temp_dir, "v1", "model.pkl")
        test_model = {"test": "data"}
        joblib.dump(test_model, model_path)
        
        with patch('app.config.get_model_path') as mock_path:
            mock_path.return_value = model_path
            
            # Load the model first
            self.registry.get_model("v1")
            
            # Get info
            info = self.registry.get_model_info("v1")
            
            assert info["version"] == "v1"
            assert info["exists"] is True
            assert info["loaded"] is True
            assert info["active"] is False  # Not set as active
            assert info["load_time"] is not None
            assert info["file_size"] is not None
            assert info["modified_time"] is not None
    
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        # Create and load a model
        model_path = os.path.join(self.temp_dir, "v1", "model.pkl")
        joblib.dump({"test": "data"}, model_path)
        
        with patch('app.config.get_model_path') as mock_path:
            mock_path.return_value = model_path
            
            self.registry.get_model("v1")
            assert "v1" in self.registry._models
            
            # Clear specific version
            self.registry.clear_cache("v1")
            assert "v1" not in self.registry._models
            
            # Clear all
            self.registry.get_model("v1")  # Reload
            self.registry.clear_cache()
            assert len(self.registry._models) == 0 