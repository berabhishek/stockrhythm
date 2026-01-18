.PHONY: help lint lint-fix lint-stats doctor test check format install-pre-commit

help:
	@echo "StockRhythm Development Commands"
	@echo "=================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install-deps      - Sync dependencies with uv"
	@echo "  make install-pre-commit - Install git pre-commit hooks"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint              - Run linter (check for issues)"
	@echo "  make lint-fix          - Auto-fix linting issues"
	@echo "  make lint-stats        - Show detailed linting statistics"
	@echo "  make format            - Format code with ruff"
	@echo "  make doctor            - Run pre-flight health check"
	@echo ""
	@echo "Testing:"
	@echo "  make test              - Run all tests"
	@echo "  make test-unit         - Run unit tests only"
	@echo "  make test-integration  - Run integration tests only"
	@echo "  make test-coverage     - Run tests with coverage report"
	@echo ""
	@echo "Checks:"
	@echo "  make check             - Run doctor + lint + tests"
	@echo ""

install-deps:
	@echo "Installing dependencies..."
	uv sync

install-pre-commit:
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install
	@echo "Pre-commit hooks installed!"

lint:
	@echo "Running linter..."
	stockrhythm lint

lint-fix:
	@echo "Running linter with --fix..."
	stockrhythm lint --fix

lint-stats:
	@echo "Running linter with statistics..."
	stockrhythm lint --stats

format:
	@echo "Formatting code with ruff..."
	uv run ruff format .

doctor:
	@echo "Running pre-flight health check..."
	stockrhythm doctor --verbose

test:
	@echo "Running all tests..."
	uv run pytest tests/ -v

test-unit:
	@echo "Running unit tests..."
	uv run pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	uv run pytest tests/integration/ -v

test-coverage:
	@echo "Running tests with coverage..."
	uv run pytest tests/ --cov=packages --cov=apps --cov-report=html --cov-report=term

check: doctor lint test
	@echo ""
	@echo "✓ All checks passed!"
