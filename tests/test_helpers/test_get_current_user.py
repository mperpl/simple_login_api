import uuid
import pytest
import jwt
from fastapi import HTTPException
from app.helpers.get_current_user import get_current_user
from app.database import models
from app.config import settings

@pytest.mark.asyncio
async def test_get_current_user_valid(session):
    user = models.User(
        username="test", 
        email="test@test.com", 
        password="hash", 
        token_version=uuid.uuid4()
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    payload = {"sub": str(user.id), "version": str(user.token_version)}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    result = await get_current_user(token=token, db=session)

    assert result.id == user.id
    assert result.email == user.email


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(session):
    token = "not-a-real-token"
    
    with pytest.raises(HTTPException) as e:
        await get_current_user(token=token, db=session)
    
    assert e.value.status_code == 401
    assert e.value.detail == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_current_user_token_version_mismatch(session):
    user = models.User(username="t", email="e@e.com", password="p", token_version=uuid.uuid4())
    session.add(user)
    await session.commit()

    token = jwt.encode({"sub": str(user.id), "version": str(user.token_version)}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    user.token_version = uuid.uuid4()
    await session.commit()

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=token, db=session)
    
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_protected_route_fails_after_version_change(auth_client, session):
    response = await auth_client.get("/users/1")
    assert response.status_code == 200

    await session.execute(
        models.User.__table__.update()
        .where(models.User.id == 1)
        .values(token_version=uuid.uuid4())
    )
    await session.commit()

    response = await auth_client.put('/users/1', json={
        'old_password': 'password123', 
        'new_password': 'newpassword123'
    })

    assert response.status_code == 401
    assert response.json() == {"detail": "Could not validate credentials"}