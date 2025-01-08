import decimal
import os
import random
from typing import AsyncIterator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from tronpy import AsyncTron
from tronpy.providers import HTTPProvider

from src import models
from src.db import get_session
from src.main import app
from src.models import WalletQuery

engine = create_async_engine(
    os.getenv("TEST_DB_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/test_tronparser")
)


@pytest.fixture(scope="module")
async def async_engine():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def test_db_session(async_engine) -> AsyncIterator[AsyncSession]:
    async_session = async_sessionmaker(async_engine, expire_on_commit=False)
    async with async_session() as session:
        await session.begin()

        yield session

        await session.rollback()


@pytest.fixture(scope="function")
async def test_client(test_db_session) -> AsyncIterator[AsyncClient]:
    async def override_get_session():
        yield test_db_session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url=os.getenv("TEST_APP_BASE_URL", "http://test"),
    ) as async_client:
        yield async_client


@pytest.fixture(scope="function")
async def test_tronpy_client() -> AsyncIterator[AsyncTron]:
    api_key = os.getenv("TRONPY_TEST_API_KEY", None)
    timeout = float(os.getenv("TRONPY_TEST_TIMEOUT", 10.))
    provider = HTTPProvider(
        timeout=timeout,
        api_key=api_key
    ) if api_key else None

    network = os.getenv("TRONPY_TEST_NETWORK", "nile")
    async with AsyncTron(network=network, provider=provider) as client:
        yield client


@pytest.fixture(scope="function")
async def random_query(test_tronpy_client) -> dict[str, str]:
    address = test_tronpy_client.generate_address().get("base58check_address")
    return {
        "query_id": random.randint(1, 1000),
        "address": address,
    }


@pytest.fixture(scope="function")
async def random_query_db(test_tronpy_client) -> WalletQuery:
    address = test_tronpy_client.generate_address().get("base58check_address")
    query = WalletQuery(
        address=address,
        balance=decimal.Decimal("5148.03202"),
        bandwidth=600,
        energy=180000000000,
    )

    return query
