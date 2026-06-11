from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from ya.interfaces.api.app import app


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestFastAPI:
    @pytest.mark.asyncio
    async def test_health(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_tools_endpoint(self, client: AsyncClient) -> None:
        response = await client.get("/api/tools")
        assert response.status_code == 200
        tools = response.json()
        assert len(tools) >= 1
        assert tools[0]["name"] == "utc_time"

    @pytest.mark.asyncio
    async def test_config_endpoint(self, client: AsyncClient) -> None:
        response = await client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert "llm_provider" in data
        assert "llm_model" in data

    @pytest.mark.asyncio
    async def test_docs_available(self, client: AsyncClient) -> None:
        response = await client.get("/docs")
        assert response.status_code == 200
