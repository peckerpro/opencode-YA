from __future__ import annotations

import asyncio
import uuid
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel

if TYPE_CHECKING:
    pass


async def _chat_loop(console: Console) -> None:
    from ya.application.container import ServiceContainer
    c = ServiceContainer()
    await c.initialize()
    sid = ""
    console.clear()
    console.print(Panel("[bold blue]YA TUI v0.5[/bold blue]  /help"))

    try:
        while True:
            try:
                ui = await asyncio.get_event_loop().run_in_executor(None, input, "\n> ")
            except (EOFError, KeyboardInterrupt):
                break
            ui = ui.strip()
            if not ui:
                continue
            if ui == "/exit":
                break
            if ui == "/help":
                console.print("[dim]/sessions /new /resume <id> /status /help /exit[/dim]")
                continue
            if ui == "/sessions":
                sessions = await c.session_store.list_sessions()
                for s in sessions[:10]:
                    m = " ←" if s.id.startswith(sid) else ""
                    console.print(f"  [{s.status.value}] {s.id[:8]} — {s.title[:30]}{m}")
                continue
            if ui == "/new":
                sid = uuid.uuid4().hex[:8]
                console.print(f"[green]New: {sid}[/green]")
                continue
            if ui == "/status":
                console.print(f"[dim]Session: {sid or 'none'}[/dim]")
                continue
            if ui.startswith("/resume "):
                sid = ui.split(maxsplit=1)[1].strip()
                console.print(f"[green]Resumed: {sid}[/green]")
                continue

            console.print(f"\n[bold cyan]You:[/bold cyan] {ui}")
            try:
                loop = c.create_agent_loop(max_steps=5)
                if loop:
                    sess = await c.get_or_create_session(sid)
                    if not sid:
                        sid = sess.id[:8]
                        console.print(f"[dim]Session: {sid}[/dim]")
                    await loop.run(sess, ui)
                    msgs = await c.session_store.get_messages(sess.id)  # type: ignore[union-attr]
                    for m in msgs:  # type: ignore[union-attr]
                        if m.role.value == "assistant":
                            text = m.content or ""
                            # Strip thinking tags for display
                            import re
                            text = re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()
                            if text:
                                console.print(f"\n[bold green]YA:[/bold green] {text}")
                        elif m.role.value == "tool":
                            console.print(f"\n[dim yellow]🔧 {m.name}: {m.content}[/dim yellow]")
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]")
    finally:
        await c.close()


def main() -> None:
    asyncio.run(_chat_loop(Console()))
