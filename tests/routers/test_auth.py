import pytest


@pytest.mark.asyncio
async def test_login_valid(client):
    await client.post('/users/', json={
        'username': 'mper',
        'email': 'mper@mper.com',
        'password': 'mper'
    })
    response = await client.post('/auth/login', data={'username': 'mper@mper.com', 'password': 'mper'})
    data = response.json()

    assert response.status_code == 200
    assert {"access_token", "refresh_token", "token_type"}.issubset(data.keys())


@pytest.mark.asyncio
async def test_login_invalid(client):
    await client.post('/users/', json={
        'username': 'mper',
        'email': 'mper@mper.com',
        'password': 'mper'
    })
    response = await client.post('/auth/login', data={'username': 'mper@mper.com', 'password': 'mpe'})
    data = response.json()
    assert response.status_code == 401
    assert data == {"detail": "Incorrect email or password"}


@pytest.mark.asyncio
async def test_refresh_valid(client):
    await client.post('/users/', json={
        'username': 'mper',
        'email': 'mper@mper.com',
        'password': 'mper'
    })
    login_response = await client.post('/auth/login', data={'username': 'mper@mper.com', 'password': 'mper'})
    login_data = login_response.json()

    refresh_response = await client.post('/auth/refresh', json={'refresh_token': login_data['refresh_token']})
    refresh_data = refresh_response.json()

    assert refresh_response.status_code == 200
    assert {"access_token", "refresh_token", "token_type"}.issubset(refresh_data.keys())


@pytest.mark.asyncio
async def test_refresh_invalid(client):
    refresh_response = await client.post('/auth/refresh', json={'refresh_token': 'badtoken'})
    refresh_data = refresh_response.json()

    assert refresh_response.status_code == 401
    assert refresh_data == {"detail": "Invalid or expired refresh token"}


@pytest.mark.asyncio
async def test_logout_logged_out(client):
    response = await client.post('auth/logout')

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_logout(auth_client):
    response = await auth_client.post('auth/logout')

    assert response.status_code == 200
    assert response.json() == {"detail": "Successfully logged out"}