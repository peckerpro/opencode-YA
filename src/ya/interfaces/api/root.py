from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/root", tags=["root"])


@router.get("/sessions")
async def list_sessions() -> list[dict[str, object]]:
    return [
        {
            "id": "example-session-1",
            "title": "Example Session",
            "status": "active",
            "last_activity": "2026-06-11T00:00:00Z",
        }
    ]


@router.get("/sessions/{session_id}")
async def inspect_session(session_id: str) -> dict[str, object]:
    return {
        "id": session_id,
        "title": "Session Detail",
        "status": "active",
        "message_count": 0,
    }


@router.get("/status")
async def root_status() -> dict[str, object]:
    return {
        "active_sessions": 0,
        "total_memories": 0,
        "active_jobs": 0,
        "tools_registered": 1,
    }
