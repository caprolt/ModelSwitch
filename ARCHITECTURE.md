# ModelSwitch Architecture

This document provides a detailed overview of the ModelSwitch architecture, design decisions, and technical implementation.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Core Components](#core-components)
- [Design Decisions](#design-decisions)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Performance Considerations](#performance-considerations)
- [Security Considerations](#security-considerations)
- [Scalability](#scalability)
- [Monitoring & Observability](#monitoring--observability)

## System Overview

ModelSwitch is a lightweight ML model serving platform designed around three core principles:

1. **Simplicity**: Minimal dependencies, easy to understand and deploy
2. **Reliability**: Robust error handling and graceful degradation
3. **Observability**: Comprehensive metrics and monitoring

The system enables teams to serve multiple versions of ML models simultaneously, switch between versions in real-time, and monitor model performance without service interruption.

### Key Features

- **Zero-downtime version switching**: Change active models without restarting
- **Lazy loading**: Models loaded on-demand and cached in memory
- **Version isolation**: Each model version is completely independent
- **Prometheus metrics**: Built-in observability for production monitoring
- **Docker-first deployment**: Containerized for consistent deployments

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Client Layer                         │
│  (Web App, Mobile App, External Services, Test Scripts)     │
└───────────────────┬──────────────────────────────────────────┘
                    │ HTTP/REST API
                    ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
│                      (FastAPI Router)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   /predict   │  │    /admin    │  │   /metrics   │     │
│  │   endpoint   │  │  endpoints   │  │   endpoint   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────────┬──────────────┬────────────────┬─────────────────┘
            │              │                │
            ▼              ▼                ▼
┌──────────────┐  ┌────────────────┐  ┌──────────────┐
│  Prediction  │  │  Admin Service │  │   Metrics    │
│   Service    │  │   (admin.py)   │  │   Service    │
│ (predict.py) │  │                │  │ (metrics.py) │
└──────┬───────┘  └────────┬───────┘  └──────┬───────┘
       │                   │                  │
       │                   │                  │
       ▼                   ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                     Model Registry Layer                     │
│                    (model_loader.py)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Model Cache (In-Memory)                               │ │
│  │  ┌────────┐    ┌────────┐    ┌────────┐              │ │
│  │  │   v1   │    │   v2   │    │   v3   │              │ │
│  │  └────────┘    └────────┘    └────────┘              │ │
│  │  Active Version Pointer: ────────►                     │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Storage Layer (Filesystem)                │
│  models/                                                     │
│  ├── v1/                                                     │
│  │   └── model.pkl                                          │
│  ├── v2/                                                     │
│  │   └── model.pkl                                          │
│  └── v3/                                                     │
│      └── model.pkl                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                          │
│  ┌─────────────┐      ┌──────────────┐                     │
│  │ Prometheus  │ ◄──── │  /metrics    │                     │
│  │  (Scraper)  │      │   Endpoint   │                     │
│  └──────┬──────┘      └──────────────┘                     │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────┐                                            │
│  │   Grafana   │                                            │
│  │ (Dashboard) │                                            │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. FastAPI Application (`main.py`)

**Responsibilities:**
- HTTP request handling and routing
- Middleware configuration (CORS, error handling)
- API documentation (OpenAPI/Swagger)
- Application lifecycle management

**Design Rationale:**
- FastAPI chosen for automatic API documentation, type validation, and async support
- ASGI-based for high performance under concurrent loads
- Built-in Pydantic integration for request/response validation

**Key Code:**
```python
app = FastAPI(
    title="ModelSwitch",
    description="ML Model Serving with Rollback Support",
    version="1.0.0"
)
```

### 2. Model Registry (`model_loader.py`)

**Responsibilities:**
- Model loading and caching
- Version management
- Active version tracking
- Cache invalidation

**Design Rationale:**
- **Lazy Loading**: Models loaded only when requested, reducing startup time
- **In-Memory Cache**: Fast access after initial load
- **Version Isolation**: Each version completely independent
- **Thread-Safe**: Safe for concurrent access (FastAPI handles this at request level)

**Key Design Pattern:**
```python
class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, Any] = {}  # Version -> Model cache
        self._active_version: str = settings.default_version
        self._load_times: Dict[str, float] = {}  # Performance tracking
```

**Trade-offs:**
- ✅ Fast prediction latency (no I/O after first load)
- ✅ Simple implementation
- ⚠️ Memory usage scales with number of loaded models
- ⚠️ No distributed state (single instance only without Redis)

### 3. Prediction Service (`predict.py`)

**Responsibilities:**
- Input validation
- Feature preprocessing
- Model inference
- Response formatting
- Metrics recording

**Design Rationale:**
- Separated from main routing logic for testability
- Pydantic models for automatic validation
- Explicit error handling with specific error types

**Request Flow:**
```python
Request → Validation → Version Resolution → Model Load → 
Inference → Metrics → Response
```

### 4. Admin Service (`admin.py`)

**Responsibilities:**
- Version switching
- Model information retrieval
- Cache management
- Health checks

**Design Rationale:**
- Separated admin operations from user-facing prediction API
- Clear distinction between operational and inference endpoints
- No authentication (designed for internal/trusted networks)

**Security Note:** In production, admin endpoints should be:
- Behind API gateway with authentication
- On separate port or path prefix
- Rate-limited
- Audit-logged

### 5. Metrics Service (`metrics.py`)

**Responsibilities:**
- Prometheus metric collection
- Performance tracking
- Model usage analytics

**Design Rationale:**
- Prometheus chosen for industry-standard monitoring
- Metrics include: latency, request count, error rates, active version
- Low overhead (atomic operations)

**Key Metrics:**
```python
- model_inference_latency_seconds (Histogram)
- model_prediction_requests_total (Counter)
- model_prediction_errors_total (Counter)
- model_version_active (Gauge)
- model_load_time_seconds (Histogram)
```

### 6. Configuration (`config.py`)

**Responsibilities:**
- Environment-based configuration
- Default values
- Configuration validation

**Design Rationale:**
- Pydantic BaseSettings for type-safe configuration
- Environment variable support (12-factor app methodology)
- Sensible defaults for development

## Design Decisions

### 1. File-Based Model Storage

**Decision:** Store models as pickle files in versioned directories

**Rationale:**
- Simple to understand and implement
- No database dependency
- Easy to backup/restore
- Compatible with most ML frameworks

**Alternatives Considered:**
- Database storage: Added complexity, not necessary for this use case
- Object storage (S3): Requires cloud dependency, adds latency
- Model registry (MLflow): Too heavy for simple use cases

**Trade-offs:**
- ✅ Simple and reliable
- ✅ Version control friendly (git-lfs)
- ⚠️ Manual version management
- ⚠️ No metadata storage (could add JSON sidecar files)

### 2. In-Memory Model Caching

**Decision:** Cache loaded models in application memory

**Rationale:**
- Drastically reduces prediction latency (no disk I/O)
- Simple implementation
- Acceptable for most deployment scenarios

**Alternatives Considered:**
- Redis cache: Added complexity, network latency
- No caching: Unacceptable latency for production
- LRU cache with size limits: Over-engineered for typical use case

**Trade-offs:**
- ✅ Fastest possible inference
- ✅ Simple code
- ⚠️ Memory usage proportional to model sizes
- ⚠️ Cache not shared across instances (need Redis for that)

### 3. Synchronous API

**Decision:** Use sync endpoints despite FastAPI's async capabilities

**Rationale:**
- scikit-learn models are CPU-bound, not I/O-bound
- Synchronous code is simpler and more maintainable
- Async provides no benefit for ML inference
- Uvicorn still handles concurrent requests via worker processes

**When to Consider Async:**
- Model inference requires network calls (e.g., remote GPU)
- Batch processing with I/O operations
- Integration with async databases

### 4. Docker-First Deployment

**Decision:** Provide Docker and Docker Compose as primary deployment method

**Rationale:**
- Consistent environment across dev/prod
- Easy to include monitoring stack
- Simplified dependency management
- Industry standard for microservices

**Provided:**
- Multi-stage Docker build (optimization)
- Non-root user (security)
- Health checks (orchestration)
- Volume mounts (data persistence)

### 5. No Built-In Authentication

**Decision:** No authentication in core application

**Rationale:**
- Keep core simple and focused
- Authentication is deployment-specific
- Should be handled at API gateway/load balancer level
- Easier to test and develop

**Production Recommendation:**
- Use API gateway (Kong, Tyk, AWS API Gateway)
- Add OAuth2/JWT middleware if needed
- Implement rate limiting at edge
- Network isolation for admin endpoints

## Data Flow

### Prediction Request Flow

```
1. Client sends POST /predict with features
   ↓
2. FastAPI validates request schema (Pydantic)
   ↓
3. predict_with_validation() called
   ↓
4. Determine version (request override or active version)
   ↓
5. model_registry.get_model(version) called
   ↓
6. If model not cached:
   - Load from disk (joblib.load)
   - Cache in memory
   - Record load time metric
   ↓
7. Model.predict(features) executed
   ↓
8. Record inference latency metric
   ↓
9. Format response with prediction and version
   ↓
10. Return JSON response to client
```

### Version Switch Flow

```
1. Admin sends POST /admin/set-active-version
   ↓
2. Validate version exists on disk
   ↓
3. Update active version in model_registry
   ↓
4. Update Prometheus gauge metric
   ↓
5. Return success response
   ↓
6. Next prediction request uses new version
   (No service interruption)
```

## Technology Stack

### Core Dependencies

| Technology | Purpose | Rationale |
|------------|---------|-----------|
| **FastAPI** | Web framework | Modern, fast, automatic API docs |
| **Uvicorn** | ASGI server | High performance, production-ready |
| **Pydantic** | Data validation | Type safety, automatic validation |
| **scikit-learn** | ML framework | Most common Python ML library |
| **joblib** | Model serialization | Efficient for numpy/sklearn models |
| **Prometheus** | Metrics collection | Industry standard monitoring |
| **Grafana** | Visualization | Beautiful dashboards, alerting |

### Development Dependencies

- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Static type checking

## Performance Considerations

### Latency Breakdown

Typical prediction request latency:

```
Component              | Cold Start | Warm (Cached)
-----------------------|------------|---------------
Request validation     | 1-2ms      | 1-2ms
Model load             | 100-500ms  | 0ms (cached)
Model inference        | 5-50ms     | 5-50ms
Response formatting    | 1ms        | 1ms
-----------------------|------------|---------------
Total                  | 107-553ms  | 7-53ms
```

### Optimization Strategies

1. **Model Caching**: Keeps hot models in memory
2. **Lazy Loading**: Only load models when requested
3. **Worker Processes**: Uvicorn runs multiple workers for parallelism
4. **Efficient Serialization**: joblib optimized for numpy arrays

### Bottlenecks

- **Model inference**: CPU-bound, scales with model complexity
- **Memory**: Limited by available RAM (cache all used models)
- **Disk I/O**: Only impacts first load per model per worker

### Scaling Recommendations

For high throughput:
1. Increase Uvicorn workers (`--workers N`)
2. Use gunicorn with uvicorn workers
3. Deploy multiple instances behind load balancer
4. Consider model optimization (quantization, ONNX)
5. Use faster inference engines for deep learning (TorchServe, TensorFlow Serving)

## Security Considerations

### Current Security Posture

- ✅ No credential storage
- ✅ Input validation via Pydantic
- ✅ Non-root Docker user
- ✅ CORS configuration
- ⚠️ No authentication/authorization
- ⚠️ No rate limiting
- ⚠️ No input sanitization beyond type validation
- ⚠️ Admin endpoints publicly accessible

### Production Security Checklist

- [ ] Add API authentication (OAuth2, JWT, API keys)
- [ ] Implement rate limiting (per-IP, per-user)
- [ ] Add request/response encryption (HTTPS/TLS)
- [ ] Sanitize and validate all inputs
- [ ] Implement audit logging
- [ ] Add security headers (HSTS, CSP, X-Frame-Options)
- [ ] Network isolation for admin endpoints
- [ ] Regular security updates
- [ ] Vulnerability scanning
- [ ] Secrets management (not in env files)

### Threat Model

**Threats:**
1. Unauthorized access to admin endpoints
2. Model theft via prediction API
3. DoS via expensive predictions
4. Code injection via model files
5. Data exfiltration

**Mitigations:**
1. API gateway with authentication
2. Rate limiting, usage monitoring
3. Request size limits, timeouts
4. Model validation, sandboxing
5. Network policies, audit logs

## Scalability

### Vertical Scaling

**Single Instance Limits:**
- Memory: ~2-8GB per model (depends on model size)
- CPU: Linear with number of workers
- Throughput: ~100-1000 req/sec (depends on model complexity)

**Scaling Up:**
- Increase worker count
- Larger instance type
- Faster CPU/more cores
- More RAM for larger models

### Horizontal Scaling

**Multi-Instance Deployment:**
```
┌───────────────┐
│ Load Balancer │
└───────┬───────┘
        │
   ┌────┴────────────┬──────────────┐
   ▼                 ▼              ▼
┌──────┐         ┌──────┐       ┌──────┐
│ App  │         │ App  │       │ App  │
│ (v1) │         │ (v2) │       │ (v3) │
└──────┘         └──────┘       └──────┘
```

**Considerations:**
- Stateless design enables easy horizontal scaling
- Shared storage for model files (NFS, S3)
- Optional: Redis for shared active version state
- Session affinity not required

### Database Considerations

**Current:** File-based storage

**For Scale:**
- Add PostgreSQL for metadata, audit logs
- Use Redis for shared cache and active version state
- Object storage (S3) for model files
- Model registry (MLflow, DVC) for versioning

## Monitoring & Observability

### Metrics Collection

**Application Metrics:**
- Request rate and latency
- Error rates and types
- Active model version
- Model load times
- Cache hit rates

**System Metrics:**
- CPU utilization
- Memory usage
- Disk I/O
- Network traffic

### Logging Strategy

**Current:** Standard output (Docker captures)

**Production:**
- Structured logging (JSON format)
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Correlation IDs for request tracing
- Centralized logging (ELK, Splunk, CloudWatch)

### Alerting

**Recommended Alerts:**
- High error rate (>1%)
- High latency (p99 > 500ms)
- Low success rate (<99%)
- Memory usage > 80%
- Model load failures

### Dashboards

**Key Metrics to Display:**
1. Request volume (by version)
2. Latency percentiles (p50, p95, p99)
3. Error rate and types
4. Active model version timeline
5. Resource utilization

## Future Enhancements

### Planned Improvements

1. **A/B Testing**: Route percentage of traffic to different versions
2. **Canary Deployments**: Gradual rollout of new versions
3. **Model Validation**: Automatic testing before activation
4. **Drift Detection**: Monitor prediction distributions
5. **Auto-Rollback**: Revert on performance degradation
6. **Multi-Model Support**: Different model types per endpoint
7. **Batch Predictions**: Process multiple requests efficiently
8. **Model Versioning**: Semantic versioning, changelog
9. **Web UI**: Visual model management interface
10. **Kubernetes**: Native k8s deployment manifests

### Technical Debt

- Add comprehensive integration tests
- Implement request batching
- Add model warmup on startup
- Improve error messages
- Add request/response logging
- Implement circuit breakers
- Add graceful shutdown handling

## Conclusion

ModelSwitch provides a solid foundation for serving ML models with version control. The architecture prioritizes simplicity and reliability while maintaining extensibility for future enhancements. The design choices reflect real-world production requirements balanced with ease of understanding and maintenance.

For questions or suggestions, please open an issue or contribute via pull request.
