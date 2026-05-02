import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_health(anon_client: AsyncClient):
    response = await anon_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
