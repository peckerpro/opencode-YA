from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ya.skills.loader import SkillLoader
from ya.skills.models import SkillStatus
from ya.skills.registry import SkillRegistry


class TestSkillLoader:
    def test_parse_frontmatter(self) -> None:
        content = """---
name: my-skill
version: "1.0"
description: A test skill
triggers:
  - test
  - deploy
permissions:
  - tool.execute.safe
---
# Skill Content
This is the skill body.
"""
        loader = SkillLoader()
        meta = loader.parse_skill_md(content)
        assert meta.name == "my-skill"
        assert meta.version == "1.0"
        assert "test" in meta.triggers
        assert "tool.execute.safe" in meta.required_permissions

    def test_parse_minimal(self) -> None:
        loader = SkillLoader()
        meta = loader.parse_skill_md("Just some text without frontmatter")
        assert meta.name == ""

    def test_load_from_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="ya-skill-") as tmp:
            skill_dir = Path(tmp) / "my-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("""---
name: test-skill
version: "0.1"
description: Loaded from path
---
Content here.
""", encoding="utf-8")

            loader = SkillLoader()
            meta = loader.load_from_path(skill_dir)
            assert meta is not None
            assert meta.name == "test-skill"


class TestSkillRegistry:
    @pytest.fixture
    def registry(self) -> SkillRegistry:
        with tempfile.TemporaryDirectory(prefix="ya-skills-") as tmp:
            r = SkillRegistry(Path(tmp))
            r.initialize()
            yield r

    def test_install_local_skill(self, registry: SkillRegistry) -> None:
        with tempfile.TemporaryDirectory(prefix="ya-src-") as src_tmp:
            skill_dir = Path(src_tmp) / "demo-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("""---
name: demo
version: "1.0"
description: Demo skill
---
Content.
""", encoding="utf-8")

            meta = registry.install_local(skill_dir)
            assert meta.name == "demo"
            assert meta.status == SkillStatus.DISABLED

    def test_enable_disable(self, registry: SkillRegistry) -> None:
        with tempfile.TemporaryDirectory(prefix="ya-src-") as src_tmp:
            skill_dir = Path(src_tmp) / "toggle-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("""---
name: toggle
version: "1.0"
---
Body.
""", encoding="utf-8")

            registry.install_local(skill_dir)
            registry.enable("toggle")
            assert registry.get("toggle").status == SkillStatus.ENABLED

            registry.disable("toggle")
            assert registry.get("toggle").status == SkillStatus.DISABLED

    def test_remove_skill(self, registry: SkillRegistry) -> None:
        with tempfile.TemporaryDirectory(prefix="ya-src-") as src_tmp:
            skill_dir = Path(src_tmp) / "rm-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("""---
name: rm-me
version: "1.0"
---
""", encoding="utf-8")

            registry.install_local(skill_dir)
            registry.remove("rm-me")
            assert registry.get("rm-me") is None

    def test_list_empty(self, registry: SkillRegistry) -> None:
        assert registry.list_all() == []

    def test_duplicate_install_raises(self, registry: SkillRegistry) -> None:
        with tempfile.TemporaryDirectory(prefix="ya-src-") as src_tmp:
            skill_dir = Path(src_tmp) / "dup-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("""---
name: dup
version: "1.0"
---
""", encoding="utf-8")

            registry.install_local(skill_dir)
            with pytest.raises(ValueError, match="already installed"):
                registry.install_local(skill_dir)
