from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class Project(BaseModel):
    id: str = ""
    name: str = ""
    description: str = ""
    workspace_id: str = ""
    status: str = "active"
    owner: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class Workspace(BaseModel):
    id: str = ""
    kind: str = "project"
    root_path: str = ""
    task_board_ref: str = ""
    whiteboard_ref: str = ""
    report_root: str = ""


class ProjectService:
    def __init__(self, projects_dir: Path) -> None:
        self._dir = projects_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def create(self, project: Project) -> Project:
        path = self._dir / f"{project.id}.json"
        if path.exists():
            raise ValueError(f"Project '{project.id}' already exists")
        path.write_text(project.model_dump_json(indent=2), encoding="utf-8")
        return project

    def get(self, project_id: str) -> Project | None:
        path = self._dir / f"{project_id}.json"
        if not path.exists():
            return None
        return Project.model_validate_json(path.read_text(encoding="utf-8"))

    def list_all(self) -> list[Project]:
        projects: list[Project] = []
        for f in sorted(self._dir.glob("*.json")):
            with suppress(Exception):
                projects.append(Project.model_validate_json(f.read_text(encoding="utf-8")))
        return projects

    def archive(self, project_id: str) -> Project | None:
        project = self.get(project_id)
        if project is None:
            return None
        project.status = "archived"
        path = self._dir / f"{project_id}.json"
        path.write_text(project.model_dump_json(indent=2), encoding="utf-8")
        return project
