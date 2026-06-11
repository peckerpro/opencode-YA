from __future__ import annotations

import uuid
from pathlib import Path

from ya.adapters.llm.minimax import MiniMaxProvider
from ya.adapters.stores.sqlite import SqliteSessionStore
from ya.application.chat import AgentLoop, AgentLoopConfig
from ya.config.paths import resolve_paths
from ya.config.settings import load_settings
from ya.domain.sessions.models import Session
from ya.tools.builtin.utc_time import UtcTimeTool
from ya.tools.policy import PermissionPolicy
from ya.tools.registry import ToolRegistry


class CLIService:
    def __init__(self, settings_path: Path | None = None) -> None:
        self._settings = load_settings()

    async def run_prompt(
        self,
        prompt: str,
        session_id: str = "",
        model: str = "",
        max_steps: int = 10,
    ) -> dict[str, object]:
        settings = self._settings
        api_key = settings.minimax_api_key
        if api_key is None:
            return {"error": "MINIMAX_API_KEY not set"}

        paths = resolve_paths(settings)
        paths.state_db.parent.mkdir(parents=True, exist_ok=True)

        provider = MiniMaxProvider(
            api_key=api_key.get_secret_value(),
            base_url=settings.minimax_base_url,
            model=model or settings.ya_llm_model,
        )
        registry = ToolRegistry()
        registry.register(UtcTimeTool())
        policy = PermissionPolicy()
        store = SqliteSessionStore(paths.state_db)
        await store.initialize()

        sid = session_id or uuid.uuid4().hex[:12]
        sess = await store.get_session(sid)
        if sess is None:
            sess = Session(id=sid, title=f"Run: {prompt[:50]}")
            await store.create_session(sess)

        loop = AgentLoop(provider=provider, store=store, registry=registry, policy=policy,  # type: ignore[arg-type]
                         config=AgentLoopConfig(max_steps=max_steps))
        run_result = await loop.run(sess, prompt)

        messages = await store.get_messages(sess.id)
        assistant_msgs = [m for m in messages if m.role.value == "assistant"]
        tool_msgs = [m for m in messages if m.role.value == "tool"]

        await store.close()

        return {
            "session_id": sess.id,
            "run_status": run_result.status.value,
            "response": assistant_msgs[-1].content if assistant_msgs else "",
            "tool_calls": [{"name": m.name, "result": m.content} for m in tool_msgs],
            "message_count": len(messages),
        }
