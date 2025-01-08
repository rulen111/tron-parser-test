import pytest

pytestmark = pytest.mark.anyio


async def test_create_get(test_client, random_query):
    response = await test_client.post("/queries", json=random_query)
    assert response.status_code == 200

    response = await test_client.get(f"/queries/{random_query['query_id']}")
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["query_id"] == random_query["query_id"]
    assert response_json["address"] == random_query["address"]


async def test_get_not_found(test_client, random_query):
    response = await test_client.get(f"/queries/{random_query['query_id']}")
    assert response.status_code == 404
    response_json = response.json()
    assert response_json["detail"] == "Query not found"
