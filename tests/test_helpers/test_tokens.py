from datetime import timedelta
import uuid
from fastapi import HTTPException
import pytest
import jwt
from app.database import models
from app.helpers.tokens import create_access_token, get_refresh_token_payload
from app.config import settings


def test_create_access_token_logic():
    data = {"sub": "1", "version": "v1"}
    access_token = create_access_token(data, is_refresh_token=False)

    decoded_access = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert decoded_access["sub"] == "1"
    assert "exp" in decoded_access
    assert "jti" not in decoded_access

    refresh_token = create_access_token(data, is_refresh_token=True)
    decoded_refresh = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    assert decoded_refresh["sub"] == "1"
    assert "jti" in decoded_refresh


@pytest.mark.asyncio
async def test_get_refresh_token_payload_success(session):
    user_uuid = uuid.uuid4()
    user = models.User(
        username="refresh_user", 
        email="refresh@test.com", 
        password="hash", 
        token_version=user_uuid
    )
    session.add(user)
    await session.commit()

    payload_data = {"sub": str(user.id), "version": str(user_uuid)}
    refresh_token = create_access_token(payload_data, is_refresh_token=True)

    payload = await get_refresh_token_payload(refresh_token, session)
    
    assert payload["sub"] == str(user.id)
    assert payload["version"] == str(user_uuid)
    assert "jti" in payload

@pytest.mark.asyncio
async def test_get_refresh_token_payload_invalid_version(session):
    user_uuid = uuid.uuid4()
    user = models.User(username="u", email="e@e.com", password="p", token_version=user_uuid)
    session.add(user)
    await session.commit()

    token = create_access_token({"sub": str(user.id), "version": str(user_uuid)}, is_refresh_token=True)

    user.token_version = uuid.uuid4()
    await session.commit()

    with pytest.raises(HTTPException) as exc:
        await get_refresh_token_payload(token, session)
    
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid or expired refresh token"

@pytest.mark.asyncio
async def test_get_refresh_token_payload_missing_jti(session):
    token = create_access_token({"sub": "1", "version": "v1"}, is_refresh_token=False)

    with pytest.raises(HTTPException) as exc:
        await get_refresh_token_payload(token, session)
    
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_access_token_expired():
    data = {"sub": "1", "version": "v1"}
    expired_token = create_access_token(
        data, 
        is_refresh_token=False, 
        access_token_delta_m=timedelta(minutes=-5)
    )
    
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(expired_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

@pytest.mark.asyncio
async def test_get_refresh_token_payload_expired(session):
    data = {"sub": "1", "version": "v1"}
    expired_refresh_token = create_access_token(data, is_refresh_token=True, refresh_token_delta_d=timedelta(days=-1))    
    with pytest.raises(HTTPException) as exc:
        await get_refresh_token_payload(expired_refresh_token, session)
    
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid or expired refresh token"