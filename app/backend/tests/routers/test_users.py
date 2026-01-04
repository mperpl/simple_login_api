import pytest

payload1 = {"username": "test", "email": "test@jomama.com", "password": "pwd"}
payload2 = {"username": "admin", "email": "git@gites.com", "password": "ok123"}


# GET ENDPOINTS
@pytest.mark.asyncio
async def test_get_all_empty(client):
    response = await client.get("/users/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_all(client):
    await client.post("/users/", json=payload1)
    await client.post("/users/", json=payload2)
    response = await client.get("/users/")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
    assert payload1["username"] == data[0]["username"]
    assert payload1["email"] == data[0]["email"]
    assert payload2["username"] == data[1]["username"]
    assert payload2["email"] == data[1]["email"]


@pytest.mark.asyncio
async def test_get_one_empty(client):
    response = await client.get("/users/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_one(client):
    await client.post("/users/", json=payload1)
    response = await client.get("/users/")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 1
    assert payload1["username"] == data[0]["username"]
    assert payload1["email"] == data[0]["email"]


# POST ENDPOINTS
@pytest.mark.asyncio
async def test_create(client):
    response = await client.post("/users/", json=payload1)
    data = response.json()
    assert response.status_code == 201
    assert data["username"] == payload1["username"]
    assert data["email"] == payload1["email"]


async def test_create_existing(client):
    await client.post("/users/", json=payload1)
    response = await client.post("/users/", json=payload1)
    assert response.status_code == 226
    assert response.json() == {"detail": "User already exists"}


# PUT ENDPOINTS
@pytest.mark.asyncio
async def test_change_password_logged_out(client):
    response = await client.put("/users/1")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


async def test_change_password_others_missing(auth_client):
    response = await auth_client.put(
        "/users/2", json={"old_password": "mper123", "new_password": "mper321"}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authorized"}


async def test_change_password_others(client, auth_client):
    await client.post(
        "/users/",
        json={"username": "mper", "email": "mper@mper.com", "password": "mper"},
    )
    await client.post(
        "/auth/login", data={"username": "mper@mper.com", "password": "mper"}
    )
    response = await auth_client.put(
        "/users/2", json={"old_password": "mper", "new_password": "123"}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authorized"}


async def test_change_password_self_bad(auth_client):
    response = await auth_client.put(
        "/users/1", json={"old_password": "mper123", "new_password": "mper321"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect old password"}


async def test_change_password_self_good(auth_client):
    response = await auth_client.put(
        "/users/1", json={"old_password": "password123", "new_password": "mper321"}
    )
    assert response.status_code == 202


# DELETE ENDPOINTS
@pytest.mark.asyncio
async def test_delete_loggedout(client):
    response = await client.delete("/users/1")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_delete_other_missing(auth_client):
    response = await auth_client.delete("/users/2")
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authorized"}


@pytest.mark.asyncio
async def test_delete_self(auth_client):
    response = await auth_client.delete("/users/1")
    assert response.status_code == 204
