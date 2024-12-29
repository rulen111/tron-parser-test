import asyncio
import os
from typing import AsyncIterator

from sqlalchemy import update
from tronpy import AsyncTron
from tronpy.providers import HTTPProvider

from app.db.db import get_session
from app.db.models import WalletQuery


async def get_client() -> AsyncIterator[AsyncTron]:
    api_key = os.getenv("TRONPY_API_KEY", None)
    timeout = float(os.getenv("TRONPY_TIMEOUT", 10.))
    provider = HTTPProvider(
        timeout=timeout,
        api_key=api_key
    ) if api_key else None

    network = os.getenv("TRONPY_NETWORK", "mainnet")
    async with AsyncTron(network=network, provider=provider) as client:
        yield client


async def parse_and_write(query: WalletQuery) -> None:
    query_id, address = query.query_id, query.address
    db_session = await anext(get_session())

    tr_client = await anext(get_client())
    balance, bandwidth, resource = await asyncio.gather(
        tr_client.get_account_balance(address),
        tr_client.get_bandwidth(address),
        tr_client.get_account_resource(address),
    )

    stmt = (
        update(WalletQuery)
        .where(WalletQuery.query_id == query_id)
        .values(
            balance=balance,
            bandwidth=bandwidth,
            energy=resource.get("TotalEnergyLimit", None),
        )
    )
    await db_session.execute(stmt)
    await db_session.commit()
