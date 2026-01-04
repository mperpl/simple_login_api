from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import StaticPool, text
from app.database.database import Base, get_db
from app.main import app


SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
testing_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = async_sessionmaker(
    expire_on_commit=False, bind=testing_engine, class_=AsyncSession
)


async def get_test_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = get_test_db


@pytest.fixture(scope="session", autouse=True)
async def create_db_tables():
    async with testing_engine.begin() as con:
        await con.run_sync(Base.metadata.create_all)
    yield
    await testing_engine.dispose()


@pytest.fixture(autouse=True)
async def reset_db():
    async with testing_engine.begin() as con:
        await con.execute(text("DELETE FROM refresh_tokens"))
        await con.execute(text("DELETE FROM users"))
    yield


@pytest.fixture
async def session():
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def client():
    async with LifespanManager(app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app), base_url="http://test"
        ) as ac:
            yield ac


@pytest.fixture
async def auth_client(client):
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123",
    }
    await client.post("/users/", json=user_data)

    login_res = await client.post(
        "/auth/login", data={"username": "test@example.com", "password": "password123"}
    )
    token = login_res.json()["access_token"]

    client.headers.update({"Authorization": f"Bearer {token}"})
    yield client
