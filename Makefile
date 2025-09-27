# Makefile for structured-logger project using uv
.PHONY: help install install-dev sync venv clean clean-all test test-cov lint format check build publish

# Default target
help:
	@echo "Available targets:"
	@echo "  help          - Show this help message"
	@echo "  venv          - Create virtual environment using uv"
	@echo "  install       - Install production dependencies"
	@echo "  install-dev   - Install development dependencies"
	@echo "  sync          - Sync dependencies with uv.lock"
	@echo ""
	@echo "Testing:"
	@echo "  test          - Run all tests"
	@echo "  test-cov      - Run tests with coverage"
	@echo "  test-unit     - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-sentry   - Run Sentry tests only"
	@echo "  test-env      - Run environment config tests"
	@echo "  test-format   - Run format validation tests"
	@echo "  test-simple   - Run simple format demo tests"
	@echo "  test-demo     - Run format demo (with full output)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint          - Run linting (flake8)"
	@echo "  format        - Format code with black"
	@echo "  format-check  - Check code formatting"
	@echo "  check         - Run all checks (lint, format check, tests)"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  build         - Build the package"
	@echo "  publish       - Publish to PyPI"
	@echo "  clean         - Clean temporary files"
	@echo "  clean-all     - Clean everything including venv"

# Virtual environment management
venv:
	uv venv
	@echo "Virtual environment created. Activate with: source .venv/bin/activate"

# Installation targets
install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

sync:
	uv pip sync

# Testing targets
test:
	uv run pytest -v

test-cov:
	uv run pytest --cov=src/structured_logger --cov-report=term-missing --cov-report=html -v

test-unit:
	uv run pytest -m "unit" -v -s

test-integration:
	uv run pytest -m "integration" -v -s

test-sentry:
	uv run pytest -m "sentry" -v -s

test-env:
	uv run pytest tests/test_env_config.py -v -s

test-format:
	uv run pytest tests/test_format_validation.py -v -s

test-simple:
	uv run pytest tests/simple_format_test.py -v -s

test-demo:
	uv run python tests/simple_format_test.py

# Code quality targets
lint:
	uv run flake8 src/structured_logger tests --count --select=E9,F63,F7,F82 --show-source --statistics

format:
	uv run black src/structured_logger tests

format-check:
	uv run black --check src/structured_logger tests

# Combined check target
check: format-check lint test

# Build and publish targets
build:
	uv run python -m build

publish: build
	uv run twine upload dist/*

# Cleaning targets
clean: clean-pyc clean-build clean-test

clean-pyc:
	find . -path "./.venv" -prune -o -name "*.pyc" -print0 | xargs -0 rm -f
	find . -path "./.venv" -prune -o -name "*.pyo" -print0 | xargs -0 rm -f
	find . -path "./.venv" -prune -o -name "*~" -print0 | xargs -0 rm -f
	find . -path "./.venv" -prune -o -type d -name "__pycache__" -print0 | xargs -0 rm -rf

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -f .coverage

clean-test:
	rm -rf .pytest_cache/
	rm -f .tox/
	rm -rf htmlcov/
	rm -f coverage.xml

clean-all: clean
	rm -rf .venv/
	rm -f uv.lock
