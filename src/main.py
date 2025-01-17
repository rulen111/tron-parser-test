from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.tronpy_client import update_query
from src.db import init_db, get_session
from src.models import WalletQuery, PydWalletQuery, PydWalletQueryBase


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
) -> list[PydWalletQuery]:

    stmt = select(WalletQuery).limit(limit).offset(skip)
    result = list((await db_session.execute(stmt)).scalars().all())

    return [PydWalletQuery.model_validate(query) for query in result]


@app.get("/queries/{query_id}")
async def get_queries(
        query_id: int,
        db_session: AsyncSession = Depends(get_session),
) -> PydWalletQuery:

    query = await db_session.get(WalletQuery, query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")

    return PydWalletQuery.model_validate(query)


@app.post("/queries")
async def create_query(
        req: PydWalletQueryBase,
        background_tasks: BackgroundTasks,
        db_session: AsyncSession = Depends(get_session),
) -> PydWalletQuery:

    address = req.address
    query = WalletQuery(address=address)

    db_session.add(query)
    await db_session.commit()
    await db_session.refresh(query)
    background_tasks.add_task(update_query, query, None, None)

    return PydWalletQuery.model_validate(query)
