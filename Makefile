.PHONY: test install dev clean lint typecheck coverage help all

help:
	@echo "Available targets:"
	@echo "  test       - Run test suite with pytest"
	@echo "  coverage   - Run tests with coverage report"
	@echo "  lint       - Run ruff linter"
	@echo "  typecheck  - Run mypy type checker"
	@echo "  all        - Run tests, lint, and typecheck"
	@echo "  clean      - Remove build artifacts and cache files"

test:
	uv run pytest

coverage:
	uv run pytest --cov=argdec --cov-report=term-missing --cov-report=html

lint:
	uv run ruff check --fix .

typecheck:
	uv run mypy argdec.py

all: test lint typecheck

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache htmlcov .coverage .venv
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
