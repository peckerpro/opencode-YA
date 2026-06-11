from __future__ import annotations

from ya.ports.parsers import ParsedBlock, ParsedDocument


class TextParser:
    def __init__(self) -> None:
        self._parser_name = "text"
        self._parser_version = "0.1.0"

    async def parse(self, source: str, content: bytes | str) -> ParsedDocument:
        text = content.decode("utf-8") if isinstance(content, bytes) else content
        blocks = []
        for _i, line in enumerate(text.split("\n")):
            stripped = line.rstrip()
            if stripped:
                blocks.append(ParsedBlock(
                    block_type="text",
                    content=stripped,
                    page=None,
                    section=None,
                ))

        return ParsedDocument(
            source=source,
            blocks=blocks,
            metadata={"line_count": str(len(blocks))},
            parser_name=self._parser_name,
            parser_version=self._parser_version,
            warnings=[],
        )


class MarkdownParser:
    def __init__(self) -> None:
        self._parser_name = "markdown"
        self._parser_version = "0.1.0"

    async def parse(self, source: str, content: bytes | str) -> ParsedDocument:
        text = content.decode("utf-8") if isinstance(content, bytes) else content
        blocks: list[ParsedBlock] = []
        current_section = ""
        in_code_block = False
        code_lines: list[str] = []

        for line in text.split("\n"):
            stripped = line.rstrip()

            if stripped.startswith("```"):
                if in_code_block:
                    blocks.append(ParsedBlock(
                        block_type="code",
                        content="\n".join(code_lines),
                        section=current_section,
                    ))
                    code_lines = []
                    in_code_block = False
                else:
                    in_code_block = True
                continue

            if in_code_block:
                code_lines.append(stripped)
                continue

            if stripped.startswith("# "):
                current_section = stripped[2:].strip()
                blocks.append(ParsedBlock(
                    block_type="heading",
                    content=current_section,
                    section=current_section,
                ))
                continue

            if stripped:
                blocks.append(ParsedBlock(
                    block_type="text",
                    content=stripped,
                    section=current_section,
                ))

        return ParsedDocument(
            source=source,
            blocks=blocks,
            metadata={
                "block_count": str(len(blocks)),
                "sections": str(len({b.section for b in blocks if b.section})),
            },
            parser_name=self._parser_name,
            parser_version=self._parser_version,
            warnings=[],
        )
