"""
Comprehensive tests for the predict module.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from app.predict import (
    PredictionRequest,
    PredictionResponse,
    make_prediction,
    validate_features,
    predict_with_validation
)


class TestPredictionRequest:
    """Tests for PredictionRequest schema."""
    
    def test_valid_request(self):
        """Test creating a valid prediction request."""
        request = PredictionRequest(features=[1.0, 2.0, 3.0])
        assert request.features == [1.0, 2.0, 3.0]
        assert request.version is None
    
    def test_request_with_version(self):
        """Test request with specific version."""
        request = PredictionRequest(features=[1.0, 2.0], version="v2")
        assert request.version == "v2"
    
    def test_mixed_numeric_types(self):
        """Test request with mixed int and float features."""
        request = PredictionRequest(features=[1, 2.5, 3])
        assert request.features == [1, 2.5, 3]


class TestFeatureValidation:
    """Tests for feature validation."""
    
    def test_validate_valid_features(self):
        """Test validation of valid features."""
        assert validate_features([1.0, 2.0, 3.0]) is True
        assert validate_features([1, 2, 3]) is True
        assert validate_features([0.0]) is True
    
    def test_validate_empty_features(self):
        """Test validation of empty features."""
        assert validate_features([]) is False
    
    def test_validate_nan_features(self):
        """Test validation rejects NaN values."""
        assert validate_features([1.0, float('nan'), 3.0]) is False
    
    def test_validate_inf_features(self):
        """Test validation rejects infinity values."""
        assert validate_features([1.0, float('inf'), 3.0]) is False
        assert validate_features([1.0, float('-inf'), 3.0]) is False
    
    def test_validate_invalid_types(self):
        """Test validation rejects non-numeric values."""
        assert validate_features([1.0, "invalid", 3.0]) is False
        assert validate_features([1.0, None, 3.0]) is False


@pytest.mark.asyncio
class TestMakePrediction:
    """Tests for the make_prediction function."""
    
    @patch('app.predict.model_registry')
    async def test_successful_prediction(self, mock_registry):
        """Test successful prediction."""
        # Setup mock model
        mock_model = Mock()
        mock_model.predict.return_value = np.array([1])
        mock_registry.get_model.return_value = mock_model
        mock_registry.get_active_version.return_value = "v1"
        
        # Make prediction
        request = PredictionRequest(features=[1.0, 2.0, 3.0])
        response = await make_prediction(request)
        
        # Assertions
        assert response.prediction == 1
        assert response.model_version == "v1"
        assert response.latency_ms > 0
        mock_model.predict.assert_called_once()
    
    @patch('app.predict.model_registry')
    async def test_prediction_with_specific_version(self, mock_registry):
        """Test prediction with specific version override."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([2])
        mock_registry.get_model.return_value = mock_model
        
        request = PredictionRequest(features=[1.0, 2.0], version="v2")
        response = await make_prediction(request)
        
        assert response.model_version == "v2"
        mock_registry.get_model.assert_called_with("v2")
    
    @patch('app.predict.model_registry')
    async def test_prediction_model_not_found(self, mock_registry):
        """Test prediction when model is not found."""
        mock_registry.get_model.side_effect = FileNotFoundError()
        mock_registry.get_active_version.return_value = "v1"
        
        request = PredictionRequest(features=[1.0, 2.0])
        
        with pytest.raises(ValueError, match="Model version .* not found"):
            await make_prediction(request)
    
    @patch('app.predict.model_registry')
    async def test_prediction_runtime_error(self, mock_registry):
        """Test prediction when runtime error occurs."""
        mock_model = Mock()
        mock_model.predict.side_effect = RuntimeError("Model error")
        mock_registry.get_model.return_value = mock_model
        mock_registry.get_active_version.return_value = "v1"
        
        request = PredictionRequest(features=[1.0, 2.0])
        
        with pytest.raises(RuntimeError, match="Prediction failed"):
            await make_prediction(request)
    
    @patch('app.predict.model_registry')
    async def test_prediction_with_array_output(self, mock_registry):
        """Test prediction that returns array."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([[0.1, 0.9]])
        mock_registry.get_model.return_value = mock_model
        mock_registry.get_active_version.return_value = "v1"
        
        request = PredictionRequest(features=[1.0, 2.0])
        response = await make_prediction(request)
        
        # Should unwrap single-row array
        assert response.prediction == [0.1, 0.9]


@pytest.mark.asyncio
class TestPredictWithValidation:
    """Tests for predict_with_validation function."""
    
    @patch('app.predict.make_prediction')
    async def test_valid_prediction(self, mock_predict):
        """Test prediction with valid features."""
        mock_response = PredictionResponse(
            prediction=1,
            model_version="v1",
            latency_ms=10.0
        )
        mock_predict.return_value = mock_response
        
        request = PredictionRequest(features=[1.0, 2.0, 3.0])
        response = await predict_with_validation(request)
        
        assert response == mock_response
        mock_predict.assert_called_once_with(request)
    
    async def test_invalid_features(self):
        """Test prediction with invalid features."""
        request = PredictionRequest(features=[])
        
        with pytest.raises(ValueError, match="Invalid features"):
            await predict_with_validation(request)
    
    async def test_nan_features(self):
        """Test prediction with NaN features."""
        request = PredictionRequest(features=[1.0, float('nan')])
        
        with pytest.raises(ValueError, match="Invalid features"):
            await predict_with_validation(request)


@pytest.mark.asyncio
class TestMetricsRecording:
    """Tests for metrics recording during predictions."""
    
    @patch('app.predict.record_inference_latency')
    @patch('app.predict.record_prediction_request')
    @patch('app.predict.model_registry')
    async def test_metrics_recorded_on_success(
        self, mock_registry, mock_request, mock_latency
    ):
        """Test that metrics are recorded on successful prediction."""
        mock_model = Mock()
        mock_model.predict.return_value = np.array([1])
        mock_registry.get_model.return_value = mock_model
        mock_registry.get_active_version.return_value = "v1"
        
        request = PredictionRequest(features=[1.0, 2.0])
        await make_prediction(request)
        
        # Verify metrics were recorded
        mock_latency.assert_called_once()
        mock_request.assert_called_once_with("v1", "success")
    
    @patch('app.predict.record_prediction_error')
    @patch('app.predict.model_registry')
    async def test_metrics_recorded_on_error(self, mock_registry, mock_error):
        """Test that error metrics are recorded on failure."""
        mock_registry.get_model.side_effect = FileNotFoundError()
        mock_registry.get_active_version.return_value = "v1"
        
        request = PredictionRequest(features=[1.0, 2.0])
        
        with pytest.raises(ValueError):
            await make_prediction(request)
        
        # Verify error metric was recorded
        mock_error.assert_called_once()
