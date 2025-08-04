import time
import numpy as np
from typing import List, Union, Optional
from pydantic import BaseModel, Field

from .model_loader import model_registry
from .metrics import record_inference_latency, record_prediction_request, record_prediction_error


class PredictionRequest(BaseModel):
    """Request schema for model predictions."""
    features: List[Union[float, int]] = Field(..., description="Input features for prediction")
    version: Optional[str] = Field(None, description="Optional model version override")


class PredictionResponse(BaseModel):
    """Response schema for model predictions."""
    prediction: Union[int, float, List[Union[int, float]]] = Field(..., description="Model prediction")
    model_version: str = Field(..., description="Version of model used")
    latency_ms: float = Field(..., description="Inference latency in milliseconds")


class PredictionError(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error message")
    model_version: Optional[str] = Field(None, description="Model version if available")


async def make_prediction(request: PredictionRequest) -> PredictionResponse:
    """Make a prediction using the specified or active model version."""
    start_time = time.time()
    
    try:
        # Determine which version to use
        version = request.version or model_registry.get_active_version()
        
        # Get the model
        model = model_registry.get_model(version)
        
        # Prepare features
        features = np.array(request.features).reshape(1, -1)
        
        # Make prediction
        prediction = model.predict(features)
        
        # Handle different prediction formats
        if hasattr(prediction, 'tolist'):
            prediction = prediction.tolist()
        if len(prediction) == 1:
            prediction = prediction[0]
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Record metrics
        record_inference_latency(version, latency_ms / 1000)  # Convert to seconds for Prometheus
        record_prediction_request(version, "success")
        
        return PredictionResponse(
            prediction=prediction,
            model_version=version,
            latency_ms=latency_ms
        )
        
    except FileNotFoundError:
        record_prediction_error(version, "model_not_found")
        raise ValueError(f"Model version '{version}' not found")
        
    except Exception as e:
        error_type = type(e).__name__
        record_prediction_error(version, error_type)
        raise RuntimeError(f"Prediction failed: {str(e)}")


def validate_features(features: List[Union[float, int]]) -> bool:
    """Validate input features."""
    if not features:
        return False
    
    # Check for valid numeric values
    for feature in features:
        if not isinstance(feature, (int, float)) or np.isnan(feature) or np.isinf(feature):
            return False
    
    return True


async def predict_with_validation(request: PredictionRequest) -> PredictionResponse:
    """Make a prediction with input validation."""
    # Validate features
    if not validate_features(request.features):
        raise ValueError("Invalid features provided")
    
    return await make_prediction(request) 