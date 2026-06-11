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


class TestRootAPI:
    @pytest.mark.asyncio
    async def test_create_session(self, client: AsyncClient) -> None:
        response = await client.post("/api/root/sessions?title=Test")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test"

    @pytest.mark.asyncio
    async def test_list_sessions(self, client: AsyncClient) -> None:
        response = await client.get("/api/root/sessions")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_session_lifecycle(self, client: AsyncClient) -> None:
        create_resp = await client.post("/api/root/sessions?title=Lifecycle")
        sid = create_resp.json()["id"]

        pause_resp = await client.post(f"/api/root/sessions/{sid}/pause")
        assert pause_resp.json()["status"] == "paused"

        resume_resp = await client.post(f"/api/root/sessions/{sid}/resume")
        assert resume_resp.json()["status"] == "active"

        archive_resp = await client.post(f"/api/root/sessions/{sid}/archive")
        assert archive_resp.json()["status"] == "archived"

    @pytest.mark.asyncio
    async def test_send_instruction(self, client: AsyncClient) -> None:
        create_resp = await client.post("/api/root/sessions?title=Instr")
        sid = create_resp.json()["id"]

        resp = await client.post(f"/api/root/sessions/{sid}/instructions?content=hello")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_session_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/root/sessions/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_root_status(self, client: AsyncClient) -> None:
        response = await client.get("/api/root/status")
        assert response.status_code == 200
        data = response.json()
        assert "active_sessions" in data
