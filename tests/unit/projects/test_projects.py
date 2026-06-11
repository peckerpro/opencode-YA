from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from ya.domain.projects.models import Project, ProjectService


class TestProjectService:
    @pytest.fixture
    def service(self) -> ProjectService:
        with tempfile.TemporaryDirectory(prefix="ya-projects-") as tmp:
            yield ProjectService(Path(tmp) / "projects")

    def test_create_project(self, service: ProjectService) -> None:
        project = Project(id="p1", name="YA Development", owner="user")
        result = service.create(project)
        assert result.name == "YA Development"

    def test_get_project(self, service: ProjectService) -> None:
        service.create(Project(id="p1", name="Test"))
        p = service.get("p1")
        assert p is not None
        assert p.name == "Test"

    def test_get_nonexistent(self, service: ProjectService) -> None:
        assert service.get("nonexistent") is None

    def test_list_projects(self, service: ProjectService) -> None:
        service.create(Project(id="p1", name="First"))
        service.create(Project(id="p2", name="Second"))
        projects = service.list_all()
        assert len(projects) == 2

    def test_duplicate_raises(self, service: ProjectService) -> None:
        service.create(Project(id="p1", name="First"))
        with pytest.raises(ValueError, match="already exists"):
            service.create(Project(id="p1", name="Duplicate"))

    def test_archive_project(self, service: ProjectService) -> None:
        service.create(Project(id="p1", name="Active"))
        archived = service.archive("p1")
        assert archived is not None
        assert archived.status == "archived"

        retrieved = service.get("p1")
        assert retrieved is not None
        assert retrieved.status == "archived"

    def test_chinese_project_name(self, service: ProjectService) -> None:
        project = Project(id="proj-cn", name="我的项目", owner="用户")
        service.create(project)
        p = service.get("proj-cn")
        assert p is not None
        assert p.name == "我的项目"
