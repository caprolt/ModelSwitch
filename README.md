# 🧠 ModelSwitch

[![CI/CD Pipeline](https://github.com/caprolt/ModelSwitch/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/caprolt/ModelSwitch/actions/workflows/ci-cd.yml)
[![codecov](https://codecov.io/gh/caprolt/ModelSwitch/branch/main/graph/badge.svg)](https://codecov.io/gh/caprolt/ModelSwitch)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://hub.docker.com/r/caprolt/modelswitch)

> **A lightweight, production-ready ML model serving platform with version control, rollback capability, and real-time monitoring.**

A minimal, self-hostable alternative to Seldon, MLflow, or BentoML — designed for solo developers, fast prototyping, and educational use.

---

## 📌 Overview

This project provides a plug-and-play system for serving machine learning models via a REST API, while allowing:
- Seamless **version switching** and rollback via admin endpoints
- Reproducible predictions with explicit model version targeting
- Real-time **metrics and observability** using Prometheus and Grafana
- Easy extension for teams, CI pipelines, or local research workflows

Unlike heavier tools, this system runs locally or on a single VM with minimal setup—no Kubernetes or cloud account required.

---

## 🎯 Use Cases

- 🔁 **Experiment iteration** — switch between model versions with a single API call  
- 🧪 **A/B testing** — compare accuracy or latency across model versions  
- 🧵 **MLOps education** — understand the building blocks of model deployment  
- 🧰 **Internal tools** — quickly expose models to downstream apps  
- 📊 **Live demos** — serve notebook-trained models in a real API  

---

## 🧰 Features

### ✅ Model Serving
- POST endpoint for real-time predictions  
- Supports any `scikit-learn`, `joblib`, or Pickle-based model  
- Optional version override per request  

### 🔁 Rollback & Versioning
- Admin API to set the **active version** (`v1`, `v2`, etc.)  
- All new requests are routed to the active version  
- Models stored in a clear directory structure (`/models/vX/`)  

### 📊 Monitoring
- **Prometheus metrics**: inference latency, model usage, error counts  
- **Grafana dashboards**: visualize trends and performance  
- `/metrics` endpoint exposed for scraping  

### ⚙️ Configuration
- JSON or `.env` based config for paths, ports, etc.  
- Optional: Redis for shared state across instances  

### 🐳 Deployment
- Dockerized, with `docker-compose.yml` for single-command setup  
- Works locally, on a VPS, or in the cloud  

---

## 🏗️ Project Structure

```
ModelSwitch/
├── app/                    # Core application
│   ├── __init__.py
│   ├── main.py            # FastAPI app entrypoint
│   ├── predict.py         # Prediction logic and routing
│   ├── model_loader.py    # Model registry and lazy loading
│   ├── admin.py           # Version switching and rollback
│   ├── config.py          # Config parsing
│   └── metrics.py         # Prometheus metrics
├── models/                 # Model storage
│   ├── v1/model.pkl
│   └── v2/model.pkl
├── examples/              # Example scripts
│   ├── train_example_models.py
│   └── test_api.py
├── tests/                 # Test suite
│   ├── __init__.py
│   └── test_model_loader.py
├── grafana/               # Monitoring dashboards
│   ├── dashboard.json
│   └── datasource.yml
├── prometheus.yml         # Metrics configuration
├── docker-compose.yml     # Full stack orchestration
├── Dockerfile            # Application container
├── requirements.txt      # Python dependencies
├── env.example          # Environment template
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (optional but recommended)
- `scikit-learn`, `joblib` or compatible ML model

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/ModelSwitch.git
cd ModelSwitch
pip install -r requirements.txt
```

### 2. Train Example Models

The project includes example training scripts:

```bash
# Train example models for testing
python examples/train_example_models.py
```

Or manually save a trained model to `models/v1/model.pkl`:

```python
import joblib
from sklearn.ensemble import RandomForestClassifier

model = RandomForestClassifier().fit(X_train, y_train)
joblib.dump(model, 'models/v1/model.pkl')
```

### 3. Run the API

**Local Development:**
```bash
uvicorn app.main:app --reload
```

**Docker (Recommended):**
```bash
docker-compose up --build
```

### 4. Test the API

```bash
python examples/test_api.py
```

**Access Points:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Metrics: http://localhost:8000/metrics
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

---

## 🌐 API Reference

### `POST /predict`
**Body:**
```json
{ "features": [1.2, 3.4, 5.6] }
```

**Optional:** `?version=v2`

**Returns:**
```json
{ "prediction": 1, "model_version": "v1" }
```

---

### `POST /admin/set-active-version`

Set active model globally:
```json
{ "version": "v2" }
```

---

### `GET /healthz`

Simple health check.

---

### `GET /metrics`

Prometheus-compatible metrics endpoint.

---

## 📊 Monitoring

### Prometheus

Scrape config included in `prometheus.yml`. Metrics tracked:
- `model_inference_latency_seconds`
- `model_prediction_requests_total`
- `model_prediction_errors_total`
- `model_version_active{version="vX"}`

### Grafana

Import `grafana/dashboard.json` to get a pre-built dashboard with:
- Request volume over time  
- Average latency per model version  
- Active version indicator  

---

## 🧩 Roadmap Ideas

- [ ] Add SQLite or Redis for persistent state across restarts  
- [ ] UI for switching versions  
- [ ] Canary routing (e.g., 90% to v2, 10% to v1)  
- [ ] CI/CD: Deploy models on push via GitHub Actions  
- [ ] Hugging Face/ONNX support  

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Code of conduct
- Development setup
- Coding standards
- Testing requirements
- Pull request process

### Quick Start for Contributors

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/ModelSwitch.git
cd ModelSwitch

# Install development dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linters
black app/ tests/
isort app/ tests/
flake8 app/ tests/
```

---

## 📚 Documentation

- **[Architecture](ARCHITECTURE.md)**: System design and technical decisions
- **[Deployment Guide](DEPLOYMENT.md)**: Deploy to AWS, GCP, Azure, or Kubernetes
- **[Contributing](CONTRIBUTING.md)**: How to contribute to the project
- **[API Documentation](http://localhost:8000/docs)**: Interactive API docs (when running)

---

## 🌟 Project Highlights

This project demonstrates:

- ✅ **Clean Architecture**: Separation of concerns, testable code
- ✅ **Production Practices**: Monitoring, logging, health checks
- ✅ **DevOps Pipeline**: CI/CD, automated testing, Docker
- ✅ **Cloud-Ready**: Deploy to AWS, GCP, Azure, or Kubernetes
- ✅ **Type Safety**: Full type hints and static analysis
- ✅ **Comprehensive Testing**: Unit, integration, and performance tests
- ✅ **Security**: Best practices for production deployments
- ✅ **Observability**: Prometheus metrics and Grafana dashboards

---

## 📊 Project Status

| Component | Status |
|-----------|--------|
| Core API | ✅ Stable |
| Version Control | ✅ Stable |
| Monitoring | ✅ Stable |
| Docker Support | ✅ Stable |
| Documentation | ✅ Complete |
| Test Coverage | 🟡 In Progress |
| Cloud Deployment | ✅ Documented |

---

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [scikit-learn](https://scikit-learn.org/) - Machine learning
- [Prometheus](https://prometheus.io/) - Monitoring
- [Grafana](https://grafana.com/) - Visualization

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📧 Contact

- **GitHub**: [@caprolt](https://github.com/caprolt)
- **Issues**: [GitHub Issues](https://github.com/caprolt/ModelSwitch/issues)
- **Discussions**: [GitHub Discussions](https://github.com/caprolt/ModelSwitch/discussions)

---

<div align="center">

**⭐ Star this repository if you find it useful! ⭐**

Made with ❤️ for the ML community

</div>

