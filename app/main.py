from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from .config import settings
from .predict import PredictionRequest, PredictionResponse, predict_with_validation
from .admin import (
    VersionRequest, VersionResponse, HealthResponse, ModelInfoResponse,
    set_active_version, get_health_status, get_model_info, get_all_models_info, clear_model_cache
)
from .model_loader import model_registry


# Create FastAPI app
app = FastAPI(
    title="ModelSwitch - ML Model Serving with Rollback Support",
    description="A lightweight machine learning model serving API with version control and rollback capability",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "name": "ModelSwitch",
        "description": "ML Model Serving with Rollback Support",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/healthz"
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Make a prediction using the active model or a specified version.
    
    - **features**: Input features for the model
    - **version**: Optional model version override (e.g., "v2")
    """
    try:
        return await predict_with_validation(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/set-active-version", response_model=VersionResponse)
async def admin_set_active_version(request: VersionRequest):
    """
    Set the active model version for all future predictions.
    
    - **version**: Model version to activate (e.g., "v2")
    """
    return await set_active_version(request)


@app.get("/admin/active-version")
async def admin_get_active_version():
    """Get the currently active model version."""
    return {
        "active_version": model_registry.get_active_version(),
        "available_versions": model_registry.get_available_versions()
    }


@app.get("/admin/models", response_model=list[ModelInfoResponse])
async def admin_get_models_info():
    """Get detailed information about all available models."""
    return await get_all_models_info()


@app.get("/admin/models/{version}", response_model=ModelInfoResponse)
async def admin_get_model_info(version: str):
    """Get detailed information about a specific model version."""
    return await get_model_info(version)


@app.post("/admin/cache/clear")
async def admin_clear_cache(version: str = Query(None, description="Version to clear (optional, clears all if not specified)")):
    """Clear model cache for a specific version or all versions."""
    return await clear_model_cache(version)


@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return await get_health_status()


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if not settings.metrics_enabled:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    # Ensure models directory exists
    import os
    os.makedirs(settings.models_dir, exist_ok=True)
    
    # Load the default model if it exists
    try:
        model_registry.get_model()
    except FileNotFoundError:
        # This is expected if no models are available yet
        pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 