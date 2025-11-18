.PHONY: help install dev-install format lint test docker-build docker-up docker-down migrate db-upgrade db-downgrade clean

help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  dev-install  - Install development dependencies"
	@echo "  format       - Format code with black"
	@echo "  lint         - Lint code with ruff and mypy"
	@echo "  test         - Run tests"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up    - Start Docker containers"
	@echo "  docker-down  - Stop Docker containers"
	@echo "  migrate      - Create new migration"
	@echo "  db-upgrade   - Apply migrations"
	@echo "  db-downgrade - Rollback migration"
	@echo "  clean        - Remove cache files"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

format:
	black app/ tests/
	ruff check --fix app/ tests/

lint:
	black --check app/ tests/
	ruff check app/ tests/
	mypy app/

test:
	pytest tests/ -v

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	alembic revision --autogenerate -m "$(msg)"

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
