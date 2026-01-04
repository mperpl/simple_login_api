from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from backend.config import settings


SQLALCHEMY_DATABASE_URL = settings.DB_URL
engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = async_sessionmaker(
    expire_on_commit=False, bind=engine, class_=AsyncSession
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as session:
        yield session


async def create_db_tables():
    async with engine.begin() as con:
        await con.run_sync(Base.metadata.create_all)


DB_SESSION = Annotated[AsyncSession, Depends(get_db)]
