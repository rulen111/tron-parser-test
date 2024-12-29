from contextlib import asynccontextmanager
from typing import Optional, Type, Sequence

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tronpy import AsyncTron

from tronpy_client import get_client, parse_address
from db import init_db, get_session
from models import WalletQuery, PydWalletQuery, PydWalletQueryBase


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/queries")
async def get_queries(
        skip: Optional[int] = 0,
        limit: Optional[int] = 10,
        db_session: AsyncSession = Depends(get_session),
) -> Sequence[PydWalletQuery]:
    stmt = select(WalletQuery)
    result = list((await db_session.execute(stmt)).scalars().all())

    return result[skip: skip + limit]


@app.get("/queries/{query_id}")
async def get_queries(
        query_id: int,
        db_session: AsyncSession = Depends(get_session),
) -> Type[PydWalletQuery]:
    query = await db_session.get(PydWalletQuery, query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    return query


@app.post("/queries")
async def create_query(
        req: PydWalletQueryBase,
        db_session: AsyncSession = Depends(get_session),
        tr_client: AsyncTron = Depends(get_client),
) -> PydWalletQuery:
    address = req.address
    query = await parse_address(address, tr_client)

    query_db = WalletQuery(**query.model_dump())
    db_session.add(query_db)
    await db_session.commit()

    return query
