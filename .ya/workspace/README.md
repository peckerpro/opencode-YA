# YA Runtime Workspace

本目录是 YA 运行时 multi-agent 共享区，不是项目架构文档目录。

## Files

- `TASK_BOARD.md`：当前被 YA 管理项目的运行时任务投影。
- `WHITEBOARD.md`：短期共享上下文和假设。
- `TODO.project.md`：尚未形成 task package 的项目候选。
- `TODO.agent.md`：当前 agent 的临时步骤。
- `reports/`：review、test、stage、alignment 和 handoff 报告。

runtime 可创建：

- `events.jsonl`：append-only task events。
- `locks/`：owner/lease locks。
- `handoffs/`：按 task/agent 隔离的交接文件。

## Authority

- 机器状态上线前，本目录 Markdown 由单一 Coordinator/merge owner 管理。
- runtime 上线后，event store 是状态事实源，Markdown 是人类可读投影。
- 根目录 `TASK_BOARD.md` 管理 YA 仓库自身开发，不与本文件自动同步。

## Write Rules

- 一个任务同一时刻一个 owner。
- 每次执行记录 role 和 session/project/workspace scope。
- Session Agent 不跨 session，Project Agent 不跨 project；权限提升必须走 guard/确认。
- 共享文件写入使用 lock/原子替换。
- agent 优先写自己的 report/handoff，再由 merge owner 合并。
- 冲突时保留双方，不允许静默 last-write-wins。
- 所有文件使用 UTF-8；Python I/O 显式 `encoding="utf-8"`。
- 不保存 API key、token、resolved credential 或认证 header。

运行日志、memory、RAG、cron store 和临时文件分别放在 `.ya/logs/`、`.ya/memory/`、`.ya/rag/`、`.ya/cron/`、`.ya/tmp/`。
