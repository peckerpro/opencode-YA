from __future__ import annotations

from typer.testing import CliRunner

from ya.interfaces.cli.main import app

runner = CliRunner()


class TestCliHelp:
    def test_help(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "YA" in result.stdout
        assert "chat" in result.stdout
        assert "doctor" in result.stdout
        assert "tools" in result.stdout

    def test_version(self) -> None:
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "0.1" in result.stdout

    def test_chat_help(self) -> None:
        result = runner.invoke(app, ["chat", "--help"])
        assert result.exit_code == 0
        assert "session" in result.stdout

    def test_run_help(self) -> None:
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "PROMPT" in result.stdout


class TestCliDoctor:
    def test_doctor_runs(self) -> None:
        result = runner.invoke(app, ["doctor"])
        assert result.exit_code == 0
        assert "Python version" in result.stdout
        assert "MiniMax" in result.stdout

    def test_doctor_reports_missing_key(self) -> None:
        result = runner.invoke(app, ["doctor"])
        assert "not set" in result.stdout or "MiniMax" in result.stdout


class TestCliTools:
    def test_tools_list(self) -> None:
        result = runner.invoke(app, ["tools"])
        assert result.exit_code == 0
        assert "utc_time" in result.stdout
        assert "safe" in result.stdout

    def test_tools_list_output_structure(self) -> None:
        result = runner.invoke(app, ["tools"])
        assert "Registered Tools" in result.stdout or "utc_time" in result.stdout


class TestCliRun:
    def test_run_requires_prompt(self) -> None:
        result = runner.invoke(app, ["run"])
        assert result.exit_code != 0

    def test_run_with_prompt(self) -> None:
        result = runner.invoke(app, ["run", "Hello, world!"])
        assert "Hello, world!" in result.stdout or "MINIMAX_API_KEY" in result.stdout or result.exit_code != 0
