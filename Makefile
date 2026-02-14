.PHONY: help test lint mypy pylint ruff format check clean install

help:
	@echo "Available targets:"
	@echo "  make install   - Install package in development mode"
	@echo "  make test      - Run tests with coverage (≥87%)"
	@echo "  make lint      - Run all linters (mypy + pylint + ruff)"
	@echo "  make mypy      - Run mypy type checker"
	@echo "  make pylint    - Run pylint code checker"
	@echo "  make ruff      - Run ruff linter"
	@echo "  make format    - Auto-format code"
	@echo "  make check     - Run tests + linting (CI)"
	@echo "  make clean     - Remove cache files"

install:
	pip install -e .

test:
	pytest --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=87

mypy:
	@echo "Running mypy (strict type checking)..."
	@mypy

pylint:
	@echo "Running pylint..."
	@pylint netcheck.py orchestrator.py display.py export.py models.py enums.py config.py colors.py logging_config.py network/ utils/ || (echo "Pylint found issues!" && exit 1)
	@echo "✓ Pylint passed!"

ruff:
	@echo "Running ruff..."
	@ruff check .

lint: mypy pylint ruff
	@echo ""
	@echo "================================================"
	@echo "✓ All linters passed! Code is clean."
	@echo "================================================"

format:
	ruff format .

check: test lint
	@echo "All checks passed!"

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info
