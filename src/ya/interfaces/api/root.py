from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/root", tags=["root"])

_sessions: dict[str, dict[str, object]] = {}


@router.get("/sessions")
async def list_sessions() -> list[dict[str, object]]:
    return list(_sessions.values())


@router.post("/sessions")
async def create_session(title: str = "") -> dict[str, object]:
    import uuid
    sid = uuid.uuid4().hex[:8]
    session: dict[str, object] = {
        "id": sid,
        "title": title or f"Session {sid}",
        "status": "active",
        "created_at": "",
        "last_activity": "",
    }
    _sessions[sid] = session
    return session


@router.get("/sessions/{session_id}")
async def inspect_session(session_id: str) -> dict[str, object]:
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return _sessions[session_id]


@router.post("/sessions/{session_id}/pause")
async def pause_session(session_id: str) -> dict[str, str]:
    if session_id not in _sessions:
        raise HTTPException(status_code=404)
    _sessions[session_id]["status"] = "paused"
    return {"status": "paused"}


@router.post("/sessions/{session_id}/resume")
async def resume_session(session_id: str) -> dict[str, str]:
    if session_id not in _sessions:
        raise HTTPException(status_code=404)
    _sessions[session_id]["status"] = "active"
    return {"status": "active"}


@router.post("/sessions/{session_id}/archive")
async def archive_session(session_id: str) -> dict[str, str]:
    if session_id not in _sessions:
        raise HTTPException(status_code=404)
    _sessions[session_id]["status"] = "archived"
    return {"status": "archived"}


@router.post("/sessions/{session_id}/close")
async def close_session(session_id: str) -> dict[str, str]:
    if session_id not in _sessions:
        raise HTTPException(status_code=404)
    _sessions[session_id]["status"] = "closed"
    return {"status": "closed"}


@router.post("/sessions/{session_id}/instructions")
async def send_instruction(session_id: str, content: str = "") -> dict[str, object]:
    if session_id not in _sessions:
        raise HTTPException(status_code=404)
    return {
        "session_id": session_id,
        "instruction_id": "inst-001",
        "content": content,
        "status": "queued",
    }


@router.get("/status")
async def root_status() -> dict[str, object]:
    return {
        "active_sessions": len(_sessions),
        "total_memories": 0,
        "active_jobs": 0,
        "tools_registered": 1,
    }


@router.get("/active-agents")
async def active_agents() -> list[dict[str, str]]:
    return []


@router.get("/approvals")
async def list_approvals() -> dict[str, object]:
    return {"pending": [], "total": 0}


@router.post("/approvals/{approval_id}/approve")
async def approve(approval_id: str) -> dict[str, str]:
    return {"status": "approved"}


@router.post("/approvals/{approval_id}/deny")
async def deny(approval_id: str) -> dict[str, str]:
    return {"status": "denied"}


@router.get("/summarize-all")
async def summarize_all() -> dict[str, object]:
    return {
        "total_sessions": 0,
        "active_sessions": 0,
        "attention_items": [],
    }
