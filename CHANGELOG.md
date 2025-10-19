# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- ✨ Type hints throughout the codebase (full mypy --strict compatibility)
- ✨ Comprehensive test suite with pytest and conftest fixtures
- ✨ GitHub Actions CI/CD pipeline for automated testing and security checks
- ✨ Pre-commit hooks configuration for code quality
- ✨ pyproject.toml with modern Python project configuration
- ✨ Detailed README with installation, development, and troubleshooting guides
- ✨ Security-focused features: bandit and safety checks in CI
- ✨ Environment variable validation with .env.example
- 🧪 Extended test coverage for validation utilities, auth module, and rate limiting
- 📊 Coverage reporting (target: ≥80%)
- 🔒 Enhanced error handling and logging

### Changed
- ♻️ Refactored auth.py: fixed decorator pattern for async functions
- ♻️ Improved database/connection.py: proper error handling and removed echo=True
- ♻️ Improved database/migrations.py: better error handling and logging
- ♻️ Enhanced logging configuration in bot/main.py
- 📝 Updated all docstrings to Google style with comprehensive descriptions
- 🎨 Improved code formatting with black and isort configurations

### Fixed
- 🐛 Fixed session.get() anti-pattern in auth.py (replaced with select() + scalar())
- 🐛 Fixed async/await patterns in decorators
- 🐛 Removed dangerous echo=True from database configuration
- 🐛 Added proper exception handling for database operations
- 🐛 Fixed type hints in validation functions

### Removed
- ❌ Removed old unittest-based tests (migrated to pytest)
- ❌ Removed redundant requirements.txt comments

## [0.1.0] - 2024-10-18

### Added
- Initial project setup
- Basic Telegram bot structure with aiogram 3.22
- SQLAlchemy 2.0 models for User, Request, Comment, File
- Database connection and migrations
- Authentication and authorization utilities
- Input validation and rate limiting
- Request creation and management handlers
- File upload support
- Docker and Docker Compose configuration
- Basic test suite for validation utilities
