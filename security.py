from datetime import datetime, timedelta, timezone
from typing import Annotated
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from pwdlib import PasswordHash
from sqlalchemy import select

from database import DB_SESSION
import models

password_hash = PasswordHash.recommended()
def hash_password(password: str) -> str:
    return password_hash.hash(password)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

# Yes, should be an enviromental variable
SECRET_KEY = 'skibiditoiletsigmagrind'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
def create_access_token(data: dict, is_refresh_token: bool = False, access_token_delta_m: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), refresh_token_delta_d: timedelta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)):
    to_encode = data.copy()

    if not is_refresh_token:
        expire = datetime.now(timezone.utc) + access_token_delta_m
        to_encode.update({"exp": expire})
    else:
        expire = datetime.now(timezone.utc) + refresh_token_delta_d
        to_encode.update({"exp": expire, 'jti': str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DB_SESSION):
    def credentials_exception():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id = payload.get("sub")
        token_version = payload.get('version')

        if id is None:
            raise credentials_exception()
    except jwt.InvalidTokenError:
        raise credentials_exception()
    
    user = db.get(models.User, int(id))
    if user is None or token_version is None or token_version != str(user.token_version):
        raise credentials_exception()
    
    return user
CURRENT_USER = Annotated[models.User, Depends(get_current_user)]

def get_refresh_token_payload(token: str, db: DB_SESSION):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        raise credentials_exception

    jti = payload.get("jti")
    user_id = payload.get("sub")
    version = payload.get("version")

    if not jti or not user_id:
        raise credentials_exception

    user = db.get(models.User, int(user_id))
    if not user or version != str(user.token_version):
        raise credentials_exception

    return payload