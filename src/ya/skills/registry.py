from __future__ import annotations

import hashlib
from pathlib import Path

from ya.skills.loader import SkillLoader
from ya.skills.models import SkillMetadata, SkillSource, SkillStatus


class SkillRegistry:
    def __init__(self, skills_dir: Path) -> None:
        self._dir = skills_dir
        self._loader = SkillLoader()
        self._skills: dict[str, SkillMetadata] = {}

    def initialize(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        self._scan_installed()

    def _scan_installed(self) -> None:
        if not self._dir.exists():
            return
        for entry in self._dir.iterdir():
            if entry.is_dir():
                meta = self._loader.load_from_path(entry)
                if meta and meta.name:
                    self._skills[meta.name] = meta

    def list_all(self) -> list[SkillMetadata]:
        return sorted(self._skills.values(), key=lambda s: s.name)

    def get(self, name: str) -> SkillMetadata | None:
        return self._skills.get(name)

    def install_local(self, source_path: Path) -> SkillMetadata:
        meta = self._loader.load_from_path(source_path)
        if meta is None or not meta.name:
            raise ValueError(f"No valid SKILL.md found in {source_path}")

        meta.source = SkillSource.LOCAL
        meta.status = SkillStatus.DISABLED
        meta.source_hash = self._hash_path(source_path)

        dest = self._dir / meta.name
        if dest.exists():
            raise ValueError(f"Skill '{meta.name}' already installed")

        self._copy_tree(source_path, dest)
        self._skills[meta.name] = meta
        return meta

    def enable(self, name: str) -> None:
        meta = self._skills.get(name)
        if meta is None:
            raise KeyError(f"Skill '{name}' not found")
        meta.status = SkillStatus.ENABLED

    def disable(self, name: str) -> None:
        meta = self._skills.get(name)
        if meta is None:
            raise KeyError(f"Skill '{name}' not found")
        meta.status = SkillStatus.DISABLED

    def remove(self, name: str) -> None:
        meta = self._skills.get(name)
        if meta is None:
            raise KeyError(f"Skill '{name}' not found")
        dest = self._dir / name
        if dest.exists():
            import shutil
            shutil.rmtree(dest)
        del self._skills[name]

    @staticmethod
    def _hash_path(path: Path) -> str:
        if path.is_file():
            return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        return "dir"

    @staticmethod
    def _copy_tree(src: Path, dst: Path) -> None:
        import shutil
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(src, dst)
