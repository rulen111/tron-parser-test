import asyncio
import os
from typing import AsyncIterator

from tronpy import AsyncTron
from tronpy.providers import HTTPProvider

from models import PydWalletQuery


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


async def parse_address(address: str, tr_client: AsyncTron) -> PydWalletQuery:
    balance, bandwidth, resource = await asyncio.gather(
        tr_client.get_account_balance(address),
        tr_client.get_bandwidth(address),
        tr_client.get_account_resource(address),
    )

    query = PydWalletQuery(
        address=address,
        balance=balance,
        bandwidth=bandwidth,
        energy=resource.get("TotalEnergyLimit", None),
    )

    return query
