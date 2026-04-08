start:
	docker compose up -d

stop:
	docker compose down

logs:
	docker compose logs -f

test:
	uv run pytest

lint:
	uv run ruff check . && uv run black --check .

start-local:
	honcho start

