from __future__ import annotations

import pytest

from ya.adapters.parsers.media import ImageParser, MediaParser
from ya.domain.instructions.approval import ApprovalInbox, ApprovalItem
from ya.domain.instructions.summarize import SummarizationService


class TestImageParser:
    @pytest.mark.asyncio
    async def test_parse_image_bytes(self) -> None:
        parser = ImageParser()
        doc = await parser.parse("photo.png", b"fake-image-data")
        assert doc.parser_name == "image"
        assert len(doc.blocks) == 1
        assert doc.blocks[0].block_type == "image"

    @pytest.mark.asyncio
    async def test_parse_image_content_hash(self) -> None:
        parser = ImageParser()
        doc = await parser.parse("test.jpg", b"some bytes")
        assert "content_hash" in doc.metadata
        assert len(doc.metadata["content_hash"]) == 16


class TestMediaParser:
    @pytest.mark.asyncio
    async def test_routes_to_image_parser(self) -> None:
        parser = MediaParser()
        doc = await parser.parse("test.png", b"data")
        assert doc.parser_name == "image"

    @pytest.mark.asyncio
    async def test_unsupported_format(self) -> None:
        parser = MediaParser()
        doc = await parser.parse("video.mp4", b"data")
        assert doc.parser_name == "media"
        assert len(doc.warnings) >= 1


class TestSummarizationService:
    def test_generate_summary(self) -> None:
        service = SummarizationService()
        sessions = [
            {"id": "s1", "title": "Dev Chat", "status": "active", "message_count": 42},
            {"id": "s2", "title": "Blocked", "status": "blocked", "message_count": 5},
        ]
        summary = service.generate_global_summary(sessions, memory_count=10, task_count=3, cron_count=1)
        assert summary.total_sessions == 2
        assert summary.active_sessions == 1
        assert summary.total_memories == 10
        assert len(summary.attention_items) >= 1

    def test_idle_attention(self) -> None:
        service = SummarizationService()
        summary = service.generate_global_summary([])
        assert len(summary.attention_items) >= 1
        assert "idle" in summary.attention_items[0].lower()


class TestApprovalInbox:
    @pytest.fixture
    def inbox(self) -> ApprovalInbox:
        return ApprovalInbox()

    def test_submit_and_approve(self, inbox: ApprovalInbox) -> None:
        cid = inbox.submit(ApprovalItem(capability="git.push", target="repo", requested_by="agent-1"))
        assert inbox.approve(cid)
        items = inbox.list_all()
        assert items[0].status.value == "approved"

    def test_deny(self, inbox: ApprovalInbox) -> None:
        cid = inbox.submit(ApprovalItem(capability="session.delete", target="s1", requested_by="root"))
        assert inbox.deny(cid)

    def test_list_pending(self, inbox: ApprovalInbox) -> None:
        inbox.submit(ApprovalItem(capability="tool.execute.dangerous", target="/tmp", requested_by="a1"))
        inbox.submit(ApprovalItem(capability="memory.sync", target="repo", requested_by="a2"))
        assert len(inbox.list_pending()) == 2

    def test_expire_old(self, inbox: ApprovalInbox) -> None:
        item = ApprovalItem(
            capability="test", target="x", requested_by="a1",
            created_at="2020-01-01T00:00:00+00:00",
        )
        inbox.submit(item)
        count = inbox.expire_old()
        assert count == 1
