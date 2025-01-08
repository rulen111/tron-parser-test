import asyncio
import logging
import os
from typing import AsyncIterator, Optional, Any

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from tronpy import AsyncTron
from tronpy.exceptions import AddressNotFound, BadAddress
from tronpy.providers import HTTPProvider

from src.db import get_session
from src.models import WalletQuery


async def get_client() -> AsyncIterator[AsyncTron]:
    api_key = os.getenv("TRONPY_API_KEY", None)
    timeout = float(os.getenv("TRONPY_TIMEOUT", 10.))
    provider = HTTPProvider(
        timeout=timeout,
        api_key=api_key
    ) if api_key else None

    network = os.getenv("TRONPY_NETWORK", "nile")
    async with AsyncTron(network=network, provider=provider) as client:
        yield client


async def parse_wallet(
        query_id: int,
        address: str,
        tr_client: Optional[AsyncTron] = None,
) -> dict[str, Any]:
    result = dict()

    if not tr_client:
        tr_client = await anext(get_client())

    try:
        balance, bandwidth, resource = await asyncio.gather(
            tr_client.get_account_balance(address),
            tr_client.get_bandwidth(address),
            tr_client.get_account_resource(address),
        )
    except AddressNotFound:
        logging.warning(f"Query #{query_id}: Address {address} not found")
    except BadAddress:
        logging.warning(f"Query #{query_id}: Address {address} is incorrect")
    except Exception as err:
        logging.warning(f"Query #{query_id}: Address {address} unknown error. {err}")
    else:
        result.update({
            "balance": balance,
            "bandwidth": bandwidth,
            "energy": resource.get("TotalEnergyLimit")
        })

    return result


async def update_query(
        query: WalletQuery,
        db_session: Optional[AsyncSession] = None,
        tr_client: Optional[AsyncTron] = None,
) -> None:
    query_id, address = query.query_id, query.address
    if not db_session:
        db_session = await anext(get_session())

    data = await parse_wallet(query_id, address, tr_client)
    if data:
        stmt = (
            update(WalletQuery)
            .where(WalletQuery.query_id == query_id)
            .values(**data)
        )

        await db_session.execute(stmt)
        await db_session.commit()

