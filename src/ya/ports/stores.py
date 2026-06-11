from __future__ import annotations

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from ya.domain.agents.models import AgentEvent, Run
from ya.domain.messages.models import Message
from ya.domain.sessions.models import Session


@runtime_checkable
class SessionStore(Protocol):
    @abstractmethod
    async def create_session(self, session: Session) -> None: ...

    @abstractmethod
    async def get_session(self, session_id: str) -> Session | None: ...

    @abstractmethod
    async def list_sessions(self) -> list[Session]: ...

    @abstractmethod
    async def update_session(self, session: Session) -> None: ...

    @abstractmethod
    async def append_message(self, session_id: str, message: Message) -> None: ...

    @abstractmethod
    async def get_messages(self, session_id: str) -> list[Message]: ...

    @abstractmethod
    async def create_run(self, run: Run) -> None: ...

    @abstractmethod
    async def update_run(self, run: Run) -> None: ...

    @abstractmethod
    async def get_run(self, run_id: str) -> Run | None: ...

    @abstractmethod
    async def append_event(self, run_id: str, event: AgentEvent) -> None: ...
