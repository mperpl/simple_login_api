# SimpleLoginAPI

A minimal FastAPI-based REST API showcasing basic user login, JWT authentication (access + refresh tokens), and simple session handling. Intended as a small learning / starter project.

## Features
- Email + password login
- JWT access & refresh tokens
- Simple user model and DB layer (see app/backend/database)

## Tech
- Python + FastAPI + SQLAlchemy
- Docker / docker-compose
- Tests with pytest

## Quickstart (recommended: Docker)
1. Build & run backend:
   ```sh
   docker compose up backend
   ```
   Backend listens on port 8000.

2. Run the test suite:
   ```sh
   docker compose run --rm tester
   ```

## Run locally
1. Install UV (pip install uv): https://docs.astral.sh/uv/getting-started/installation/
2. Install dependencies:
   ```sh
   uv sync
   ```
3. Start dev server:
   ```sh
   uv run fastapi dev app/backend/main.py
   ```

## Run tests locally
  ```sh
   pytest
   ```

### make sure you are in the virtual enviroment before running commands locally!

## UI for the endpoints
  UI can be found after the project is properly set up and ran. When ready, open up http://localhost:8000/docs#/

## Where to look
- app/backend/routers — application logic
- app/backend/database — DB + models
- app/backend/tests — tests
