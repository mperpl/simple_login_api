from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from backend.database import models
from backend.database.database import DB_SESSION
from backend.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: DB_SESSION
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        id = payload.get("sub")
        token_version = payload.get("version")
        if id is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = await db.get(models.User, int(id))
    if not user or token_version != str(user.token_version):
        raise credentials_exception

    return user


CURRENT_USER = Annotated[models.User, Depends(get_current_user)]
