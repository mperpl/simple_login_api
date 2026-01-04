from datetime import datetime, timedelta, timezone
import uuid
from fastapi import HTTPException, status
import jwt
from backend.database.database import DB_SESSION
import backend.database.models as models
from backend.config import settings

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(
    data: dict,
    is_refresh_token: bool = False,
    access_token_delta_m: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    refresh_token_delta_d: timedelta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
):
    to_encode = data.copy()

    if not is_refresh_token:
        expire = datetime.now(timezone.utc) + access_token_delta_m
        to_encode.update({"exp": expire})
    else:
        expire = datetime.now(timezone.utc) + refresh_token_delta_d
        to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def get_refresh_token_payload(token: str, db: DB_SESSION):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except jwt.InvalidTokenError:
        raise credentials_exception

    jti = payload.get("jti")
    user_id = payload.get("sub")
    version = payload.get("version")

    if not jti or not user_id or version is None:
        raise credentials_exception
    try:
        target_id = int(user_id)
    except (ValueError, TypeError):
        raise credentials_exception

    user = await db.get(models.User, target_id)
    if not user or str(version) != str(user.token_version):
        raise credentials_exception

    return payload
