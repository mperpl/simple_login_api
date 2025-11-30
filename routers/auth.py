from datetime import datetime, timezone
from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from sqlalchemy import delete, select
from database import DB_SESSION
import models
import schemas
from security import ALGORITHM, SECRET_KEY, create_access_token, get_refresh_token_payload, verify_password

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

@router.post('/login', response_model=schemas.Tokens)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB_SESSION):
    user = db.scalar(select(models.User).where(models.User.email == form_data.username))
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail='Incorrect email or password')

    user.token_version = uuid.uuid4()
    db.add(user)

    db.execute(delete(models.RefreshToken).where(models.RefreshToken.user_id == user.id))

    token_data = {"sub": str(user.id), "version": str(user.token_version)}
    access_token = create_access_token(token_data)
    refresh_token = create_access_token(token_data, is_refresh_token=True)

    refresh_payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    db.add(models.RefreshToken(
        jti=refresh_payload["jti"],
        user_id=user.id,
        expires_at=datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)
    ))

    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }



@router.post('/refresh', response_model=schemas.Tokens)
def refresh(data: schemas.RefreshRequest, db: DB_SESSION):

    payload = get_refresh_token_payload(data.refresh_token, db)

    jti = payload["jti"]
    user_id = int(payload["sub"])

    existing = db.scalar(
        select(models.RefreshToken).where(
            models.RefreshToken.jti == jti,
            models.RefreshToken.user_id == user_id
        )
    )

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked or invalid."
        )

    db.delete(existing)

    user = db.get(models.User, user_id)
    user_data = {"sub": str(user_id), "version": str(user.token_version)}

    access_token = create_access_token(user_data)
    new_refresh_token = create_access_token(user_data, is_refresh_token=True)

    new_payload = jwt.decode(new_refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    new_jti = new_payload["jti"]
    exp_timestamp = new_payload["exp"]
    expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

    db.add(
        models.RefreshToken(
            jti=new_jti,
            user_id=user_id,
            expires_at=expires_at
        )
    )

    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }