# Contributing to ModelSwitch

Thank you for your interest in contributing to ModelSwitch! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- **Be respectful**: Treat everyone with respect and kindness
- **Be collaborative**: Work together to find the best solutions
- **Be constructive**: Provide helpful feedback and accept criticism gracefully
- **Be inclusive**: Welcome diverse perspectives and backgrounds

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/ModelSwitch.git
   cd ModelSwitch
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/caprolt/ModelSwitch.git
   ```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (optional but recommended)
- Git

### Local Environment Setup

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Install pre-commit hooks**:
   ```bash
   pre-commit install
   ```

4. **Create environment file**:
   ```bash
   cp env.example .env
   # Edit .env with your local configuration
   ```

5. **Train example models**:
   ```bash
   python examples/train_example_models.py
   ```

6. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Development Setup

```bash
docker-compose up --build
```

## Development Workflow

1. **Sync with upstream**:
   ```bash
   git checkout main
   git fetch upstream
   git merge upstream/main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Make your changes** following the code style guidelines

4. **Run tests**:
   ```bash
   pytest
   pytest --cov=app tests/  # With coverage
   ```

5. **Run linters**:
   ```bash
   black app/ tests/
   isort app/ tests/
   flake8 app/ tests/
   mypy app/
   ```

6. **Commit your changes** using conventional commit messages

7. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

8. **Open a Pull Request** on GitHub

## Code Style Guidelines

### Python Style

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 100 characters (not 79)
- **Formatting**: Use [Black](https://black.readthedocs.io/) for code formatting
- **Import sorting**: Use [isort](https://pycqa.github.io/isort/) for import organization
- **Type hints**: Use type hints for all function signatures
- **Docstrings**: Use Google-style docstrings

### Code Formatting

```python
# Good example
def predict_with_model(
    features: List[float], 
    version: Optional[str] = None
) -> Dict[str, Any]:
    """
    Make a prediction using the specified model version.
    
    Args:
        features: Input features for prediction
        version: Optional model version override
        
    Returns:
        Dictionary containing prediction and metadata
        
    Raises:
        ValueError: If features are invalid
        RuntimeError: If model loading fails
    """
    if not features:
        raise ValueError("Features cannot be empty")
    
    model = model_registry.get_model(version)
    prediction = model.predict([features])
    
    return {
        "prediction": prediction[0],
        "version": version or model_registry.get_active_version()
    }
```

### Import Organization

```python
# Standard library imports
import os
import time
from typing import Dict, Optional, Any

# Third-party imports
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib

# Local imports
from .config import settings
from .model_loader import model_registry
```

## Testing Guidelines

### Writing Tests

- **Coverage**: Aim for >80% code coverage
- **Test structure**: Use Arrange-Act-Assert pattern
- **Naming**: Use descriptive test names that explain what is being tested
- **Fixtures**: Use pytest fixtures for common setup
- **Mocking**: Mock external dependencies (filesystem, network, etc.)

### Test Organization

```python
class TestModelRegistry:
    """Test cases for ModelRegistry class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.registry = ModelRegistry()
    
    def test_get_model_success(self):
        """Test successful model retrieval."""
        # Arrange
        version = "v1"
        
        # Act
        model = self.registry.get_model(version)
        
        # Assert
        assert model is not None
        assert self.registry.is_version_loaded(version)
    
    def test_get_model_not_found(self):
        """Test model retrieval when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            self.registry.get_model("nonexistent")
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_model_loader.py

# Run specific test
pytest tests/test_model_loader.py::TestModelRegistry::test_get_model_success

# Run with verbose output
pytest -v

# Run and stop at first failure
pytest -x
```

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, missing semicolons, etc.)
- **refactor**: Code refactoring without feature changes
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (dependencies, build process, etc.)
- **ci**: CI/CD changes

### Examples

```
feat(api): add support for batch predictions

Implement batch prediction endpoint that accepts multiple
feature vectors and returns predictions for all of them.

Closes #123
```

```
fix(model-loader): handle corrupted model files gracefully

Previously, loading a corrupted model would crash the application.
Now it raises a RuntimeError with a descriptive message.

Fixes #456
```

```
docs(readme): update deployment instructions

Add detailed steps for deploying to AWS ECS and update
Docker Compose examples.
```

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass**: Run `pytest` locally
2. **Update documentation**: Add/update relevant docs
3. **Add tests**: Include tests for new features
4. **Run linters**: Ensure code passes all linting checks
5. **Update CHANGELOG**: Add entry for significant changes
6. **Rebase on main**: Ensure your branch is up to date

### PR Description Template

```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
Describe the tests you ran and how to reproduce them.

## Checklist
- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published
```

### Review Process

1. **Automatic checks**: CI pipeline must pass
2. **Code review**: At least one maintainer approval required
3. **Testing**: Reviewers may test changes locally
4. **Feedback**: Address all review comments
5. **Merge**: Maintainer will merge once approved

## Project Structure

```
ModelSwitch/
├── app/                    # Core application code
│   ├── __init__.py        # Package initialization
│   ├── main.py            # FastAPI app entrypoint
│   ├── predict.py         # Prediction logic
│   ├── model_loader.py    # Model registry
│   ├── admin.py           # Admin endpoints
│   ├── config.py          # Configuration
│   └── metrics.py         # Prometheus metrics
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_*.py          # Test modules
│   └── conftest.py        # Pytest fixtures
├── examples/              # Example scripts
├── docs/                  # Additional documentation
├── grafana/               # Grafana dashboards
├── .github/               # GitHub Actions workflows
└── requirements.txt       # Python dependencies
```

## Adding New Features

### 1. Model Formats

To add support for new model formats:

1. Update `model_loader.py` to handle the new format
2. Add tests in `tests/test_model_loader.py`
3. Update documentation with examples
4. Add example training script if needed

### 2. API Endpoints

To add new endpoints:

1. Define request/response models using Pydantic
2. Implement endpoint in appropriate module (`main.py`, `admin.py`, etc.)
3. Add comprehensive tests
4. Update API documentation
5. Add metrics tracking if applicable

### 3. Metrics

To add new metrics:

1. Define metric in `metrics.py`
2. Instrument code to record metric
3. Update Grafana dashboard
4. Document metric in README

## Questions?

If you have questions or need help:

1. Check existing [Issues](https://github.com/caprolt/ModelSwitch/issues)
2. Search [Discussions](https://github.com/caprolt/ModelSwitch/discussions)
3. Open a new issue with the `question` label

## License

By contributing to ModelSwitch, you agree that your contributions will be licensed under the MIT License.
