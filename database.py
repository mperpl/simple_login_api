from typing import Annotated
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

SQLALCHEMY_DATABASE_URL = 'sqlite:///./auth_users.db'
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
class Base(DeclarativeBase):
    pass

def get_db():
   db = SessionLocal()
   try:
       yield db
   finally:
       db.close()

DB_SESSION = Annotated[Session, Depends(get_db)]

def create_db_tables():
    Base.metadata.create_all(bind=engine)