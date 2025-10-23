"""
Integration tests for the ModelSwitch API.
"""

import pytest
from fastapi.testclient import TestClient
import joblib
import os
import tempfile
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification

from app.main import app


@pytest.fixture(scope="module")
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(scope="module")
def setup_test_models():
    """Create test models for integration testing."""
    # Create temporary models directory
    models_dir = tempfile.mkdtemp()
    
    # Generate test data
    X, y = make_classification(n_samples=100, n_features=10, random_state=42)
    
    # Train and save test models
    for version in ["v1", "v2"]:
        version_dir = os.path.join(models_dir, version)
        os.makedirs(version_dir, exist_ok=True)
        
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)
        
        model_path = os.path.join(version_dir, "model.pkl")
        joblib.dump(model, model_path)
    
    # Temporarily set the models directory
    original_dir = os.environ.get("MODELS_DIR")
    os.environ["MODELS_DIR"] = models_dir
    
    yield models_dir
    
    # Cleanup
    if original_dir:
        os.environ["MODELS_DIR"] = original_dir
    else:
        os.environ.pop("MODELS_DIR", None)
    
    # Remove test models
    import shutil
    shutil.rmtree(models_dir, ignore_errors=True)


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint returns correct information."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "ModelSwitch"
        assert "docs" in data
        assert "health" in data


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    def test_health_check(self, test_client, setup_test_models):
        """Test health check endpoint."""
        response = test_client.get("/healthz")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "active_version" in data
        assert "available_versions" in data


class TestPredictionEndpoint:
    """Tests for the prediction endpoint."""
    
    def test_prediction_success(self, test_client, setup_test_models):
        """Test successful prediction."""
        payload = {
            "features": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        }
        
        response = test_client.post("/predict", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "model_version" in data
        assert "latency_ms" in data
        assert data["latency_ms"] > 0
    
    def test_prediction_with_version(self, test_client, setup_test_models):
        """Test prediction with specific version."""
        payload = {
            "features": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "version": "v2"
        }
        
        response = test_client.post("/predict", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["model_version"] == "v2"
    
    def test_prediction_invalid_features(self, test_client):
        """Test prediction with invalid features."""
        payload = {"features": []}
        
        response = test_client.post("/predict", json=payload)
        
        assert response.status_code == 400
    
    def test_prediction_invalid_json(self, test_client):
        """Test prediction with invalid JSON."""
        response = test_client.post(
            "/predict",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422


class TestAdminEndpoints:
    """Tests for admin endpoints."""
    
    def test_get_active_version(self, test_client, setup_test_models):
        """Test getting active version."""
        response = test_client.get("/admin/active-version")
        
        assert response.status_code == 200
        data = response.json()
        assert "active_version" in data
        assert "available_versions" in data
    
    def test_set_active_version(self, test_client, setup_test_models):
        """Test setting active version."""
        payload = {"version": "v2"}
        
        response = test_client.post("/admin/set-active-version", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["active_version"] == "v2"
    
    def test_set_invalid_version(self, test_client, setup_test_models):
        """Test setting invalid version."""
        payload = {"version": "v999"}
        
        response = test_client.post("/admin/set-active-version", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
    
    def test_get_models_info(self, test_client, setup_test_models):
        """Test getting all models information."""
        response = test_client.get("/admin/models")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "version" in data[0]
        assert "exists" in data[0]
    
    def test_get_single_model_info(self, test_client, setup_test_models):
        """Test getting single model information."""
        response = test_client.get("/admin/models/v1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "v1"
        assert "exists" in data
        assert "loaded" in data
    
    def test_clear_cache(self, test_client, setup_test_models):
        """Test clearing model cache."""
        response = test_client.post("/admin/cache/clear?version=v1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestMetricsEndpoint:
    """Tests for metrics endpoint."""
    
    def test_metrics_endpoint(self, test_client):
        """Test Prometheus metrics endpoint."""
        response = test_client.get("/metrics")
        
        assert response.status_code == 200
        content = response.text
        
        # Check for expected metrics
        assert "model_inference_latency_seconds" in content or "Metrics disabled" in response.json().get("detail", "")


class TestCORS:
    """Tests for CORS configuration."""
    
    def test_cors_headers(self, test_client):
        """Test CORS headers are present."""
        response = test_client.options(
            "/predict",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # CORS should allow the request
        assert response.status_code in [200, 204]


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_404_error(self, test_client):
        """Test 404 error for non-existent endpoint."""
        response = test_client.get("/nonexistent")
        
        assert response.status_code == 404
    
    def test_method_not_allowed(self, test_client):
        """Test 405 error for wrong HTTP method."""
        response = test_client.get("/predict")
        
        assert response.status_code == 405


class TestEndToEnd:
    """End-to-end workflow tests."""
    
    def test_complete_workflow(self, test_client, setup_test_models):
        """Test complete workflow: health check, predict, switch version, predict again."""
        # 1. Health check
        health_response = test_client.get("/healthz")
        assert health_response.status_code == 200
        
        # 2. Make prediction with v1 (default)
        predict_payload = {
            "features": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        }
        prediction1 = test_client.post("/predict", json=predict_payload)
        assert prediction1.status_code == 200
        v1_result = prediction1.json()["prediction"]
        
        # 3. Switch to v2
        switch_response = test_client.post(
            "/admin/set-active-version",
            json={"version": "v2"}
        )
        assert switch_response.status_code == 200
        assert switch_response.json()["active_version"] == "v2"
        
        # 4. Make prediction with v2
        prediction2 = test_client.post("/predict", json=predict_payload)
        assert prediction2.status_code == 200
        assert prediction2.json()["model_version"] == "v2"
        
        # 5. Verify we can still explicitly use v1
        predict_payload["version"] = "v1"
        prediction3 = test_client.post("/predict", json=predict_payload)
        assert prediction3.status_code == 200
        assert prediction3.json()["model_version"] == "v1"
