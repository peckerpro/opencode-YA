from __future__ import annotations

import asyncio

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table


class TUI:
    def __init__(self) -> None:
        self.console = Console()
        self.messages: list[tuple[str, str]] = []
        self.status = {"llm": "checking...", "tools": "0", "sessions": "0"}

    def render(self) -> Layout:
        layout = Layout()
        layout.split_column(Layout(name="top", size=3), Layout(name="body"), Layout(name="bottom", size=3))
        layout["body"].split_row(Layout(name="chat", ratio=2), Layout(name="side", ratio=1))
        layout["top"].update(Panel("[bold blue]YA TUI v0.5[/bold blue]  /exit=quit"))
        layout["bottom"].update(Panel("[dim]Type message...[/dim]"))

        lines: list[str] = []
        for role, text in self.messages[-15:]:
            prefix = "[cyan]You:[/cyan]" if role == "user" else "[green]YA:[/green]"
            lines.append(f"{prefix} {text[:120]}")
        layout["chat"].update(Panel("\n".join(lines) or "[dim]Start typing...[/dim]", title="Chat"))

        t = Table(title="Status")
        t.add_column("C")
        t.add_column("S")
        for k, v in self.status.items():
            t.add_row(k, v)
        layout["side"].update(Panel(t))
        return layout

    async def run(self) -> None:
        self.console.clear()
        self.status["llm"] = "[green]connected[/green]"
        self.status["tools"] = "[green]1[/green]"

        with Live(self.render(), console=self.console, refresh_per_second=4, screen=True) as live:
            while True:
                try:
                    ui = await asyncio.get_event_loop().run_in_executor(None, input, "\n> ")
                except (EOFError, KeyboardInterrupt):
                    break
                if not ui.strip():
                    continue
                if ui == "/exit":
                    break

                self.messages.append(("user", ui))
                if len(self.messages) > 50:
                    self.messages = self.messages[-50:]
                live.update(self.render())

                try:
                    from ya.application.container import ServiceContainer
                    c = ServiceContainer()
                    await c.initialize()
                    try:
                        loop = c.create_agent_loop(max_steps=5)
                        if loop:
                            sess = await c.get_or_create_session()
                            await loop.run(sess, ui)
                            msgs = await c.session_store.get_messages(sess.id)
                            for m in msgs:
                                if m.role.value == "assistant":
                                    self.messages.append(("assistant", (m.content or "")[:300]))
                                elif m.role.value == "tool":
                                    self.messages.append(("tool", f"tool: {m.name} → {m.content}"))
                    finally:
                        await c.close()
                except Exception as e:
                    self.messages.append(("error", str(e)))
                live.update(self.render())


def main() -> None:
    asyncio.run(TUI().run())
