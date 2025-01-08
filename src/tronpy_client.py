import asyncio
import logging
import os
from typing import AsyncIterator, Optional, Any

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from tronpy import AsyncTron
from tronpy.exceptions import AddressNotFound, BadAddress
from tronpy.providers import HTTPProvider

from db import get_session
from models import WalletQuery


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
        address: str,
        tr_client: AsyncTron,
) -> dict[str, Any]:
    result = dict()

    try:
        balance, bandwidth, resource = await asyncio.gather(
            tr_client.get_account_balance(address),
            tr_client.get_bandwidth(address),
            tr_client.get_account_resource(address),
        )
    except AddressNotFound:
        logging.warning(f"Address {address} not found")
    except BadAddress:
        logging.warning(f"Address {address} is incorrect")
    except Exception as err:
        logging.warning(f"Address {address} unknown error. {err}")
    else:
        result.update({
            "balance": balance,
            "bandwidth": bandwidth,
            "energy": resource.get("TotalEnergyLimit")
        })

    return result


async def update_db_entry(
        query_id: int,
        data: dict[str, Any],
        db_session: AsyncSession,
) -> None:

    stmt = (
        update(WalletQuery)
        .where(WalletQuery.query_id == query_id)
        .values(**data)
    )

    await db_session.execute(stmt)
    await db_session.commit()


async def process_query(
        query: WalletQuery,
) -> None:
    query_id, address = query.query_id, query.address

    tr_client = await anext(get_client())
    data = await parse_wallet(address, tr_client)

    if data:
        db_session = await anext(get_session())
        await update_db_entry(query_id, data, db_session)

