from __future__ import annotations

import uuid

from ya.adapters.llm.minimax import MiniMaxProvider
from ya.adapters.memory.markdown import MarkdownMemoryStore
from ya.adapters.parsers.text import TextParser
from ya.adapters.stores.sqlite import SqliteSessionStore
from ya.adapters.stores.vector import VectorStore
from ya.application.chat import AgentLoop, AgentLoopConfig
from ya.application.cron_service import CronService
from ya.application.memory_service import MemoryService
from ya.application.rag import RAGService
from ya.config.paths import resolve_paths
from ya.config.settings import load_settings
from ya.domain.sessions.models import Session
from ya.ports.embeddings import Embedder
from ya.scheduler.store import SchedulerStore
from ya.tools.builtin.utc_time import UtcTimeTool
from ya.tools.policy import PermissionPolicy
from ya.tools.registry import ToolRegistry


class ServiceContainer:
    def __init__(self) -> None:
        self._settings = load_settings()
        self._paths = resolve_paths(self._settings)
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return

        self._paths.state_db.parent.mkdir(parents=True, exist_ok=True)
        self.session_store = SqliteSessionStore(self._paths.state_db)
        await self.session_store.initialize()

        self.cron_store = SchedulerStore(str(self._paths.cron / "scheduler.db"))
        await self.cron_store.initialize()

        self.memory_store = MarkdownMemoryStore(self._paths.memory)

        self.parser = TextParser()
        self.vector_store = VectorStore(self._paths.rag / "vectors.db")
        self.vector_store.initialize()

        self.provider: MiniMaxProvider | None = None

        api_key = self._settings.minimax_api_key
        if api_key:
            self.provider = MiniMaxProvider(
                api_key=api_key.get_secret_value(),
                base_url=self._settings.minimax_base_url,
                model=self._settings.ya_llm_model,
            )
        else:
            self.provider = None

        embedder: Embedder = _NoopEmbedder()
        if self._settings.volcengine_api_key:
            try:
                from ya.adapters.embeddings.volcengine import VolcengineEmbedder
                embedder = VolcengineEmbedder(
                    api_key=self._settings.volcengine_api_key.get_secret_value(),
                    base_url=self._settings.volcengine_base_url,
                    model=self._settings.volcengine_embedding_model,
                )
            except Exception:
                pass

        self.registry = ToolRegistry()
        self.registry.register(UtcTimeTool())

        self.policy = PermissionPolicy()

        self.rag_service = RAGService(embedder, self.vector_store, self.parser)
        self.cron_service = CronService(self.cron_store)
        self.memory_service = MemoryService(self.memory_store)
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
            provider=self.provider,  # type: ignore[arg-type]
            store=self.session_store,
            registry=self.registry,
            policy=self.policy,
            config=AgentLoopConfig(max_steps=max_steps),
        )

    async def get_or_create_session(self, session_id: str = "", title: str = "") -> Session:
        sid = session_id or uuid.uuid4().hex[:12]
        sess = await self.session_store.get_session(sid)
        if sess is None:
            sess = Session(id=sid, title=title or f"Session {sid[:8]}")
            await self.session_store.create_session(sess)
        return sess


class _NoopEmbedder:
    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 128 for _ in texts]
    async def embed_query(self, text: str) -> list[float]:
        return [0.0] * 128
