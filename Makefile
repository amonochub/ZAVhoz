.PHONY: help install dev lint format typecheck test coverage security clean docker-up docker-down

help:
	@echo "ZAVhoz Bot - Development Commands"
	@echo "=================================="
	@echo "make install      - Install dependencies"
	@echo "make dev          - Install dev dependencies"
	@echo "make lint         - Run linting checks (ruff, black, isort)"
	@echo "make format       - Format code (black, isort)"
	@echo "make typecheck    - Run type checking (mypy)"
	@echo "make test         - Run tests"
	@echo "make coverage     - Run tests with coverage report"
	@echo "make security     - Run security checks (bandit, safety)"
	@echo "make ci           - Run all CI checks"
	@echo "make clean        - Clean up cache files"
	@echo "make docker-up    - Start Docker containers"
	@echo "make docker-down  - Stop Docker containers"

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

lint:
	ruff check .
	black --check .
	isort --check .

format:
	ruff check . --fix
	black .
	isort .

typecheck:
	mypy . --strict

test:
	pytest tests/ -v

coverage:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated: htmlcov/index.html"

security:
	bandit -r . -ll
	safety check

ci: format typecheck test coverage security
	@echo "✅ All CI checks passed!"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	@echo "Clean complete!"

docker-up:
	docker-compose up -d --build
	@echo "Docker containers started!"

docker-down:
	docker-compose down
	@echo "Docker containers stopped!"

.DEFAULT_GOAL := help
