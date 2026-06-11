from __future__ import annotations

import pytest

from ya.adapters.parsers.text import MarkdownParser, TextParser


class TestTextParser:
    @pytest.mark.asyncio
    async def test_parse_plain_text(self) -> None:
        parser = TextParser()
        doc = await parser.parse("test.txt", b"Hello world\nHow are you?")
        assert doc.source == "test.txt"
        assert len(doc.blocks) == 2
        assert doc.blocks[0].content == "Hello world"
        assert doc.parser_name == "text"

    @pytest.mark.asyncio
    async def test_parse_string_content(self) -> None:
        parser = TextParser()
        doc = await parser.parse("test.txt", "Line 1\nLine 2")
        assert len(doc.blocks) == 2

    @pytest.mark.asyncio
    async def test_parse_empty(self) -> None:
        parser = TextParser()
        doc = await parser.parse("empty.txt", b"")
        assert len(doc.blocks) == 0

    @pytest.mark.asyncio
    async def test_parse_chinese(self) -> None:
        parser = TextParser()
        doc = await parser.parse("test.txt", "你好世界\n这是第二行")
        assert len(doc.blocks) == 2
        assert doc.blocks[0].content == "你好世界"


class TestMarkdownParser:
    @pytest.mark.asyncio
    async def test_parse_headings(self) -> None:
        parser = MarkdownParser()
        doc = await parser.parse("test.md", b"# Title\nSome content")
        assert doc.parser_name == "markdown"
        assert len(doc.blocks) == 2
        assert doc.blocks[0].block_type == "heading"
        assert doc.blocks[0].content == "Title"

    @pytest.mark.asyncio
    async def test_parse_code_block(self) -> None:
        parser = MarkdownParser()
        content = b"# Example\n```python\nprint('hello')\n```\nMore text"
        doc = await parser.parse("test.md", content)
        code_blocks = [b for b in doc.blocks if b.block_type == "code"]
        assert len(code_blocks) == 1
        assert "print('hello')" in code_blocks[0].content

    @pytest.mark.asyncio
    async def test_sections_tracking(self) -> None:
        parser = MarkdownParser()
        content = b"# Section A\nContent A\n# Section B\nContent B"
        doc = await parser.parse("test.md", content)
        sections = {b.section for b in doc.blocks if b.section}
        assert "Section A" in sections
        assert "Section B" in sections

    @pytest.mark.asyncio
    async def test_empty_markdown(self) -> None:
        parser = MarkdownParser()
        doc = await parser.parse("empty.md", b"")
        assert len(doc.blocks) == 0
