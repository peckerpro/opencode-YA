from __future__ import annotations

import asyncio

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table

console = Console()


class YA_TUI:
    def __init__(self) -> None:
        self._messages: list[tuple[str, str]] = []
        self._running = True

    def add_message(self, role: str, content: str) -> None:
        self._messages.append((role, content))
        if len(self._messages) > 50:
            self._messages = self._messages[-50:]

    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="input", size=3),
        )
        layout["body"].split_row(
            Layout(name="chat", ratio=2),
            Layout(name="sidebar", ratio=1),
        )
        return layout

    def _render_header(self) -> Panel:
        return Panel("YA TUI v0.3 — Type /help for commands, /exit to quit", style="bold blue")

    def _render_chat(self) -> Panel:
        lines: list[str] = []
        for role, content in self._messages[-20:]:
            prefix = "You" if role == "user" else "YA"
            lines.append(f"[bold]{prefix}:[/bold] {content[:100]}")
        return Panel("\n".join(lines) or "[dim]Start typing...[/dim]", title="Chat")

    def _render_sidebar(self) -> Panel:
        table = Table(title="System")
        table.add_column("Component")
        table.add_column("Status")
        table.add_row("LLM", "[yellow]not configured[/yellow]")
        table.add_row("Tools", "[green]1 registered[/green]")
        table.add_row("Memory", "[dim]0 entries[/dim]")
        return Panel(table, title="Status")

    def _render_input(self) -> Panel:
        return Panel("Type message and press Enter...", style="dim")

    async def run(self) -> None:
        console.print("[bold blue]YA TUI v0.3[/bold blue]")
        console.print("Type /exit to quit, /help for commands")
        console.print("[dim]Note: Full TUI requires real LLM integration[/dim]")


def main() -> None:
    tui = YA_TUI()
    asyncio.run(tui.run())


if __name__ == "__main__":
    main()
