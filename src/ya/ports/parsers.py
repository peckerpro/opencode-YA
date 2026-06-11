from __future__ import annotations

from abc import abstractmethod
from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class ParsedBlock(BaseModel):
    block_type: str = "text"
    content: str = ""
    page: int | None = None
    section: str | None = None


class ParsedDocument(BaseModel):
    source: str = ""
    blocks: list[ParsedBlock] = []
    metadata: dict[str, str] = {}
    parser_name: str = ""
    parser_version: str = ""
    warnings: list[str] = []


@runtime_checkable
class DocumentParser(Protocol):
    @abstractmethod
    async def parse(self, source: str, content: bytes | str) -> ParsedDocument: ...
