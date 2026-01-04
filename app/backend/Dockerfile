FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS base
WORKDIR /project
ENV UV_COMPILE_BYTECODE=1
COPY pyproject.toml uv.lock ./

FROM base AS dev
RUN uv sync --frozen
COPY . .
CMD ["uv", "run", "fastapi", "dev", "app/backend/main.py", "--host", "0.0.0.0", "--port", "8000"]