import pytest_asyncio
from app.core.config import settings
from app.core.database import get_prod_session, get_session
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

TEST_DATABASE_URL = settings.database_url_test

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    # Skip drop_all — test DB is recreated fresh by create_all on the next run.


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db_session(setup_db):
    async with TestSessionLocal() as session:
        yield session
        await session.close()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def client(db_session: AsyncSession):
    async def override_get_session():
        yield db_session

    # Override both session deps so auth endpoints (which use get_prod_session)
    # also hit the test DB.
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_prod_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def anon_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
