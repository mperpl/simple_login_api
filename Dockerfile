    FROM astral/uv:python3.13-bookworm-slim

    WORKDIR /app

    COPY pyproject.toml uv.lock ./

    RUN uv sync --frozen --no-dev

    COPY . .

    EXPOSE 8000

    CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "8000", "--host", "0.0.0.0"]