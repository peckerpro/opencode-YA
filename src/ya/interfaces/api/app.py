from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ya.interfaces.api.root import router as root_router


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

    return app


app = create_app()
