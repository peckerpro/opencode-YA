from __future__ import annotations

import asyncio

from rich.console import Console
from rich.panel import Panel


async def _chat_loop(console: Console) -> None:
    console.clear()
    console.print(Panel("[bold blue]YA TUI v0.5[/bold blue]  /exit=quit  /help=commands  /clear=clear screen"))

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
            console.print("[dim]/exit quit | /clear clear screen[/dim]")
            continue
        if ui == "/clear":
            console.clear()
            console.print(Panel("[bold blue]YA TUI v0.5[/bold blue]"))
            continue

        console.print(f"\n[bold cyan]You:[/bold cyan] {ui}")

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
                            console.print(f"\n[bold green]YA:[/bold green] {(m.content or '')[:500]}")
                        elif m.role.value == "tool":
                            console.print(f"\n[dim yellow]🔧 {m.name}: {m.content}[/dim yellow]")
            finally:
                await c.close()
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")


def main() -> None:
    asyncio.run(_chat_loop(Console()))
