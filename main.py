from contextlib import asynccontextmanager
import sys
from fastapi import FastAPI
from routers import users, auth
from database.database import create_db_tables, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    if "pytest" not in sys.modules:
        await create_db_tables()
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.include_router(users.router)
app.include_router(auth.router)