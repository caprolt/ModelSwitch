# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive testing suite with unit and integration tests
- Pre-commit hooks for code quality (black, isort, flake8, mypy)
- CI/CD pipeline with GitHub Actions
- Comprehensive documentation (ARCHITECTURE.md, DEPLOYMENT.md, CONTRIBUTING.md)
- Development requirements and setup tools
- Security scanning with Bandit and Trivy
- Performance testing with Locust
- Code coverage reporting

### Changed
- Enhanced README with badges and project status
- Improved error handling and validation
- Updated Docker configuration for production readiness

### Fixed
- Model caching edge cases
- Type hints consistency

## [1.0.0] - 2024-01-15

### Added
- Core FastAPI application with prediction endpoints
- Model registry with lazy loading and caching
- Version switching and rollback functionality
- Prometheus metrics integration
- Admin endpoints for model management
- Health check endpoint
- Docker and Docker Compose support
- Grafana dashboard for monitoring
- Example training scripts
- Basic test suite
- Environment-based configuration
- CORS middleware support

### Security
- Non-root Docker user
- Input validation with Pydantic
- Health check endpoints

## [0.2.0] - 2023-12-20

### Added
- Admin API for version management
- Model metadata tracking
- Cache management endpoints
- Multiple model version support

### Changed
- Improved model loading performance
- Enhanced error messages

## [0.1.0] - 2023-12-01

### Added
- Initial release
- Basic model serving functionality
- Single model version support
- Simple prediction endpoint

[Unreleased]: https://github.com/caprolt/ModelSwitch/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/caprolt/ModelSwitch/compare/v0.2.0...v1.0.0
[0.2.0]: https://github.com/caprolt/ModelSwitch/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/caprolt/ModelSwitch/releases/tag/v0.1.0
