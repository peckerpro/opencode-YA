from __future__ import annotations

from pathlib import Path

import yaml

from ya.skills.models import SkillMetadata


class SkillLoader:
    def load_from_path(self, path: Path) -> SkillMetadata | None:
        skill_md = path / "SKILL.md" if path.is_dir() else path
        if not skill_md.exists():
            return None

        content = skill_md.read_text(encoding="utf-8")
        return self.parse_skill_md(content, str(path))

    def parse_skill_md(self, content: str, source_path: str = "") -> SkillMetadata:
        meta = SkillMetadata(path=source_path)

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm_data = yaml.safe_load(parts[1]) or {}
                meta.name = fm_data.get("name", meta.name)
                meta.version = fm_data.get("version", meta.version)
                meta.description = fm_data.get("description", meta.description)
                meta.author = fm_data.get("author", meta.author)
                meta.license = fm_data.get("license", meta.license)
                meta.triggers = fm_data.get("triggers", meta.triggers)
                meta.required_permissions = fm_data.get("permissions", meta.required_permissions)

        return meta
