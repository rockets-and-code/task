.PHONY: help install run test db db-down clean

help:
	@echo "make install  - create .venv and install the package"
	@echo "make run      - run the pricing engine"
	@echo "make test     - run the test suite"
	@echo "make db       - start the optional Postgres (localhost:5433)"

install:
	python3 -m venv .venv
	./.venv/bin/pip install --quiet --upgrade pip
	./.venv/bin/pip install --quiet -e ".[dev]"
	@echo "done. now run: make test"

run:
	./.venv/bin/python -m tariff_engine.cli

test:
	./.venv/bin/pytest -q

db:
	docker compose up -d

db-down:
	docker compose down -v

clean:
	rm -rf .venv .pytest_cache **/__pycache__
