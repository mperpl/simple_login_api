from datetime import datetime, timezone
from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from sqlalchemy import delete, select
from app.database.database import DB_SESSION
import app.database.models as models
import app.database.schemas as schemas
from app.helpers.get_current_user import CURRENT_USER
from app.helpers.tokens import create_access_token, get_refresh_token_payload
from app.helpers.credentials import verify_password
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.Tokens, status_code=status.HTTP_200_OK)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB_SESSION
):
    user = await db.scalar(
        select(models.User).where(models.User.email == form_data.username)
    )
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    user.token_version = uuid.uuid4()
    db.add(user)

    await db.execute(
        delete(models.RefreshToken).where(models.RefreshToken.user_id == user.id)
    )

    token_data = {"sub": str(user.id), "version": str(user.token_version)}
    access_token = create_access_token(token_data)
    refresh_token = create_access_token(token_data, is_refresh_token=True)

    refresh_payload = jwt.decode(
        refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    db.add(
        models.RefreshToken(
            jti=refresh_payload["jti"],
            user_id=user.id,
            expires_at=datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc),
        )
    )

    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=schemas.Tokens, status_code=status.HTTP_200_OK)
async def refresh(data: schemas.RefreshRequest, db: DB_SESSION):
    payload = await get_refresh_token_payload(data.refresh_token, db)
    jti = payload["jti"]
    user_id = int(payload["sub"])

    existing = await db.scalar(
        select(models.RefreshToken).where(
            models.RefreshToken.jti == jti, models.RefreshToken.user_id == user_id
        )
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked or invalid"
        )

    await db.delete(existing)
    user = await db.get(models.User, user_id)
    user_data = {"sub": str(user_id), "version": str(user.token_version)}

    access_token = create_access_token(user_data)
    new_refresh_token = create_access_token(user_data, is_refresh_token=True)

    new_payload = jwt.decode(
        new_refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    new_jti = new_payload["jti"]
    exp_timestamp = new_payload["exp"]
    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

    db.add(models.RefreshToken(jti=new_jti, user_id=user_id, expires_at=expires_at))
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(current_user: CURRENT_USER, db: DB_SESSION):
    await db.execute(
        delete(models.RefreshToken).where(
            models.RefreshToken.user_id == current_user.id
        )
    )
    current_user.token_version = uuid.uuid4()
    db.add(current_user)
    await db.refresh(current_user)
    await db.commit()

    return {"detail": "Successfully logged out"}
