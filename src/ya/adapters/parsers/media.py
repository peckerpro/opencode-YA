from __future__ import annotations

import hashlib

from ya.ports.parsers import ParsedBlock, ParsedDocument


class ImageParser:
    def __init__(self) -> None:
        self._parser_name = "image"
        self._parser_version = "0.5.0"

    async def parse(self, source: str, content: bytes | str) -> ParsedDocument:
        raw = content.encode() if isinstance(content, str) else content
        content_hash = hashlib.sha256(raw).hexdigest()[:16]
        size_bytes = len(raw)

        return ParsedDocument(
            source=source,
            blocks=[ParsedBlock(block_type="image", content=f"[Image: {source}] ({size_bytes} bytes, hash: {content_hash})")],
            metadata={"content_hash": content_hash, "size_bytes": str(size_bytes), "media_type": "image"},
            parser_name=self._parser_name,
            parser_version=self._parser_version,
            warnings=[],
        )


class MediaParser:
    def __init__(self) -> None:
        self._parser_name = "media"
        self._parser_version = "0.5.0"
        self._image_parser = ImageParser()

    async def parse(self, source: str, content: bytes | str) -> ParsedDocument:
        ext = source.rsplit(".", 1)[-1].lower() if "." in source else ""

        if ext in ("png", "jpg", "jpeg", "gif", "webp", "bmp"):
            return await self._image_parser.parse(source, content)

        return ParsedDocument(
            source=source,
            blocks=[ParsedBlock(block_type="unknown", content=f"[Unsupported: {source}]")],
            metadata={"media_type": ext},
            parser_name=self._parser_name,
            parser_version=self._parser_version,
            warnings=[f"Unsupported media type: {ext}"],
        )
