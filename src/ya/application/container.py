from __future__ import annotations

import uuid

from ya.adapters.llm.minimax import MiniMaxProvider
from ya.adapters.memory.markdown import MarkdownMemoryStore
from ya.adapters.stores.sqlite import SqliteSessionStore
from ya.application.chat import AgentLoop
from ya.application.cron_service import CronService
from ya.application.memory_service import MemoryService
from ya.config.paths import resolve_paths
from ya.config.settings import load_settings
from ya.domain.sessions.models import Session
from ya.scheduler.store import SchedulerStore
from ya.tools.builtin import agent_tools
from ya.tools.policy import PermissionPolicy


class ServiceContainer:
    def __init__(self) -> None:
        self._settings = load_settings()
        self._paths = resolve_paths(self._settings)

    async def initialize(self) -> None:
        self._paths.state_db.parent.mkdir(parents=True, exist_ok=True)

        self.session_store = SqliteSessionStore(self._paths.state_db)
        await self.session_store.initialize()

        self.memory_store = MarkdownMemoryStore(self._paths.memory)
        self.memory_service = MemoryService(self.memory_store, memory_repo_path=self._paths.memory)

        self.cron_store = SchedulerStore(str(self._paths.cron / "scheduler.db"))
        await self.cron_store.initialize()
        self.cron_service = CronService(self.cron_store)

        # Wire memory service to tools
        agent_tools.set_memory_service(self.memory_service)
        agent_tools.set_session_store(self.session_store)

        api_key = self._settings.minimax_api_key
        self.provider = MiniMaxProvider(
            api_key=api_key.get_secret_value() if api_key else "",
            base_url=self._settings.minimax_base_url,
            model=self._settings.ya_llm_model,
        ) if api_key else None

        self.policy = PermissionPolicy()
        self._initialized = True

    async def close(self) -> None:
        if hasattr(self, "session_store"):
            await self.session_store.close()
        if hasattr(self, "cron_store"):
            await self.cron_store.close()

    def create_agent_loop(self, max_steps: int = 10) -> AgentLoop | None:
        if self.provider is None:
            return None
        return AgentLoop(
            provider=self.provider,
            store=self.session_store,
            policy=self.policy,
            max_steps=max_steps,
        )

    async def get_or_create_session(self, session_id: str = "", title: str = "") -> Session:
        sid = session_id or uuid.uuid4().hex[:12]
        sess = await self.session_store.get_session(sid)
        if sess is None:
            sess = Session(id=sid, title=title or f"Session {sid[:8]}")
            await self.session_store.create_session(sess)
        return sess
