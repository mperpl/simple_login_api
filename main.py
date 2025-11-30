from fastapi import FastAPI
from routers import users, auth
from database import create_db_tables

app = FastAPI()

create_db_tables()
app.include_router(users.router)
app.include_router(auth.router)