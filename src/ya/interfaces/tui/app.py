from __future__ import annotations

import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def _render(console: Console, messages: list[tuple[str, str]]) -> None:
    table = Table(title="YA TUI v0.5")
    table.add_column("Role", style="bold", width=10)
    table.add_column("Message", max_width=80)
    for role, text in messages[-20:]:
        style = "cyan" if role == "user" else "green" if role == "assistant" else "yellow"
        table.add_row(f"[{style}]{role}[/{style}]", text[:200])
    console.print(table)


async def _chat_loop(console: Console) -> None:
    messages: list[tuple[str, str]] = []
    console.clear()
    console.print(Panel("[bold blue]YA TUI v0.5[/bold blue] /exit=quit /help=commands /clear=clear"))

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
            messages.append(("system", "/exit quit, /help this, /clear screen"))
            _render(console, messages)
            continue
        if ui == "/clear":
            messages.clear()
            _render(console, messages)
            continue

        messages.append(("user", ui))

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
                            messages.append(("assistant", (m.content or "")[:300]))
                        elif m.role.value == "tool":
                            messages.append(("tool", f"🔧 {m.name}: {m.content}"))
            finally:
                await c.close()
        except Exception as e:
            messages.append(("error", str(e)))

        _render(console, messages)


def main() -> None:
    asyncio.run(_chat_loop(Console()))
