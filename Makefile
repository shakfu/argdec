.PHONY: test coverage lint typecheck all clean build check publish publish-test help

all: test lint typecheck build check

help:
	@echo "Available targets:"
	@echo "  test         - Run test suite with pytest"
	@echo "  coverage     - Run tests with coverage report"
	@echo "  lint         - Run ruff linter"
	@echo "  typecheck    - Run mypy type checker"
	@echo "  all          - Run tests, lint, and typecheck"
	@echo "  build        - Build distribution packages"
	@echo "  check        - Check distribution with twine"
	@echo "  publish-test - Upload to TestPyPI"
	@echo "  publish      - Upload to PyPI"
	@echo "  clean        - Remove build artifacts and cache files"

test:
	uv run pytest

coverage:
	uv run pytest --cov=argdec --cov-report=term-missing --cov-report=html

lint:
	uv run ruff check --fix .

typecheck:
	uv run mypy argdec.py

build: clean
	uv build

check: build
	uv run twine check dist/*

publish-test: check
	uv run twine upload --repository testpypi dist/*

publish: check
	uv run twine upload dist/*

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache htmlcov .coverage .venv dist
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
