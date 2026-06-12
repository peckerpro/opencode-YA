from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ya.interfaces.api.root import router as root_router

STATIC_DIR = Path(__file__).parent.parent / "web" / "static"


class ChatRequest(BaseModel):
    message: str = ""


def create_app() -> FastAPI:
    app = FastAPI(
        title="YA API",
        version="0.1.0",
        docs_url="/docs",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(root_router)

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

        from fastapi.responses import FileResponse

        @app.get("/")
        async def index() -> FileResponse:
            return FileResponse(str(STATIC_DIR / "index.html"))

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/api/tools")
    async def list_tools() -> list[dict[str, object]]:
        from ya.tools.builtin.utc_time import UtcTimeTool
        from ya.tools.registry import ToolRegistry

        registry = ToolRegistry()
        registry.register(UtcTimeTool())

        return [
            {
                "name": d.name,
                "description": d.description,
                "source": d.source,
                "risk": d.risk,
                "enabled": d.enabled,
            }
            for d in registry.list_definitions()
        ]

    @app.get("/api/config")
    async def get_config() -> dict[str, object]:
        from ya.config.settings import load_settings
        settings = load_settings()
        return {
            "llm_provider": settings.ya_llm_provider,
            "llm_model": settings.ya_llm_model,
            "minimax_configured": settings.minimax_api_key is not None,
        }

    @app.get("/api/memory")
    async def list_memories() -> dict[str, object]:
        return {"memories": [], "total": 0}

    @app.get("/api/cron/jobs")
    async def list_cron_jobs() -> dict[str, object]:
        return {"jobs": [], "total": 0}

    @app.post("/api/cron/jobs")
    async def create_cron_job() -> dict[str, str]:
        return {"status": "created"}

    @app.post("/api/rag/query")
    async def rag_query(query: str = "") -> dict[str, object]:
        return {"results": [], "query": query}

    @app.post("/api/chat")
    async def api_chat(req: ChatRequest) -> dict[str, object]:
        from ya.application.container import ServiceContainer
        c = ServiceContainer()
        await c.initialize()
        try:
            loop = c.create_agent_loop(max_steps=5)
            if loop is None:
                return {"response": "LLM not configured", "tool_calls": []}
            sess = await c.get_or_create_session()
            message = req.message.strip()
            if not message:
                return {"response": "Please enter a message.", "tool_calls": []}
            await loop.run(sess, message)
            msgs = await c.session_store.get_messages(sess.id)
            assistant = [m for m in msgs if m.role.value == "assistant"]
            tools = [m for m in msgs if m.role.value == "tool"]
            return {
                "response": assistant[-1].content if assistant else "",
                "session_id": sess.id,
                "tool_calls": [{"name": m.name, "result": m.content} for m in tools],
            }
        finally:
            await c.close()

    return app


app = create_app()
