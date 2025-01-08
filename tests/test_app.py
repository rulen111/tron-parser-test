from typing import Any
from unittest.mock import patch
import pytest

from src.models import WalletQuery
from src.tronpy_client import update_query

pytestmark = pytest.mark.anyio


async def test_create_get(test_client, random_query):
    with patch("fastapi.BackgroundTasks.add_task") as mock:
        def side_effect(*args, **kwargs) -> None:
            return None
        mock.side_effect = side_effect

        response = await test_client.post("/queries", json=random_query)
        query_id = response.json()["query_id"]
        assert response.status_code == 200
        assert mock.called is True

    response = await test_client.get(f"/queries/{query_id}")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["address"] == random_query["address"]


async def test_get_not_found(test_client, random_query):
    response = await test_client.get(f"/queries/{random_query['query_id']}")
    assert response.status_code == 404
    response_json = response.json()
    assert response_json["detail"] == "Query not found"


async def test_update_query(
        monkeypatch,
        random_query_db,
        test_db_session,
):
    async def parse_wallet_mock(*args, **kwargs) -> dict[str, Any]:
        return {
            "balance": random_query_db.balance,
            "bandwidth": random_query_db.bandwidth,
            "energy": random_query_db.energy,
        }
    monkeypatch.setattr("src.tronpy_client.parse_wallet", parse_wallet_mock)

    test_db_session.add(random_query_db)
    await test_db_session.commit()
    await test_db_session.refresh(random_query_db)

    await update_query(random_query_db, test_db_session)

    query_read = await test_db_session.get(WalletQuery, random_query_db.query_id)
    assert query_read
    assert random_query_db == query_read
