FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY shared ./shared
COPY servers ./servers
COPY tests ./tests
COPY .env.example ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

EXPOSE 8001

CMD ["uv", "run", "python", "-m", "servers.scraper_server.server"]

