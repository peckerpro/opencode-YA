# YA Task Board

> 权威范围：本文件只维护 YA 仓库自身的开发任务摘要，任务细节以 `plans/v0.1.md` 为准。`.ya/workspace/TASK_BOARD.md` 属于 YA runtime 管理的项目，两者不自动双写。

## Board Rules

- 一个任务同一时间只能有一个 owner。
- owner 格式：`unassigned`、`human:<name>` 或 `agent:<role>/<id>`。
- 每个任务记录当前执行 role 和 project/workspace scope。
- Coding Agent 同一时间只能拥有一个 `In Progress` 任务。
- 状态变化前先读取最新文件；当前由单一 merge owner 串行更新。
- 未来若 YA runtime 接管本仓库，必须通过明确导入生成 runtime task，并记录权威来源切换。
- `Blocked` 必须填写原因和解除条件。
- `Review` 和 `Testing` 必须链接报告或证据。
- 只有验收标准全部满足后才能进入 `Done`。
- 实现偏差进入 alignment report；影响架构或版本范围时同步 `DECISIONS.md`。

## Status Definitions

| Status | 含义 | 允许的下一状态 |
|---|---|---|
| Backlog | 已记录，依赖或优先级尚未满足 | Ready, Blocked |
| Ready | 输入和依赖齐全，可领取 | In Progress, Blocked |
| In Progress | 单一 owner 正在实现 | Review, Blocked, Ready |
| Review | 等待或正在代码审查 | Testing, In Progress, Blocked |
| Testing | 等待或正在验收 | Done, In Progress, Blocked |
| Blocked | 存在明确阻塞 | Backlog, Ready, In Progress |
| Done | 验收完成且证据已记录 | 不允许；重开需新事件 |

## Ready

| ID | Task | Owner | Role | Scope | Status | Blocked Reason | Acceptance Criteria |
|---|---|---|---|---|---|---|---|---|
| YA-001 | Project Foundation and Configuration | agent:coding/sisyphus | Coding Agent | project:YA | Done | - | 可安装、可导入、配置与 UTF-8/secret 测试通过 |

## Backlog

| ID | Task | Owner | Role | Scope | Status | Blocked Reason | Acceptance Criteria |
|---|---|---|---|---|---|---|---|---|
| YA-002 | Provider Contract and MiniMax Streaming Adapter | agent:coding/sisyphus | Coding Agent | project:YA | Done | - | fixture 可重建文本/tool call；错误归一化；无 key 测试可运行 |
| YA-003 | Session and Message Persistence | agent:coding/sisyphus | Coding Agent | project:YA | Done | - | SQLite 重开后会话一致；事务、迁移、中文测试通过 |
| YA-004 | Tool Registry and Safety Policy | agent:coding/sisyphus | Coding Agent | project:YA | Done | - | schema、policy、timeout 与 safe tool 测试通过 |
| YA-005 | Bounded Agent Loop | agent:coding/sisyphus | Coding Agent | project:YA | Done | - | 文本、工具、失败、取消和 max-step 路径均有确定结果 |
| YA-006 | CLI Chat, Run, Doctor and Tool Listing | agent:coding/sisyphus | Coding Agent | project:YA | Done | - | 四类 CLI 命令及 exit code 通过自动/手工验收 |
| YA-007 | Shared Workspace and Task State Commands | agent:coding/sisyphus | Coding Agent | project:YA | Done | - | task CLI 可用，并发 claim 无双 owner，事件可重放 |
| YA-008 | v0.1 Integration, Hardening and Alignment | agent:coordinator/sisyphus | Coordinator Agent | project:YA | Done | - | 全量验证通过并生成 v0.1 alignment report |

## In Progress

当前无任务。

| ID | Task | Owner | Role | Scope | Started At | Blocked Reason | Acceptance Criteria |
|---|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - | - |

## Review

当前无任务。

| ID | Task | Owner | Role | Scope | Reviewer | Report | Acceptance Criteria |
|---|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - | - |

## Testing

当前无任务。

| ID | Task | Owner | Role | Scope | Tester | Report | Acceptance Criteria |
|---|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - | - |

## Blocked

当前无任务。

| ID | Task | Owner | Role | Scope | Blocked Reason | Unblock Condition | Acceptance Criteria |
|---|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - | - |

## Done

| ID | Task | Owner | Role | Scope | Completed At | Evidence | Acceptance Criteria |
|---|---|---|---|---|---|---|---|
| YA-001 | Project Foundation and Configuration | agent:coding/sisyphus | Coding Agent | project:YA | 2026-06-11T23:03Z | 12/12 tests, ruff+mypy clean | 可安装、可导入、配置与 UTF-8/secret 测试通过 |
| YA-002 | Provider Contract and MiniMax Streaming Adapter | agent:coding/sisyphus | Coding Agent | project:YA | 2026-06-11T23:20Z | 7/7 tests, ruff+mypy clean | fixture 可重建文本/tool call；错误归一化；无 key 测试可运行 |
| YA-003 | Session and Message Persistence | agent:coding/sisyphus | Coding Agent | project:YA | 2026-06-11T23:20Z | 12/12 tests, ruff+mypy clean | SQLite 重开后会话一致；事务、迁移、中文测试通过 |
| YA-004 | Tool Registry and Safety Policy | agent:coding/sisyphus | Coding Agent | project:YA | 2026-06-11T23:20Z | 15/15 tests, ruff+mypy clean | schema、policy、timeout 与 safe tool 测试通过 |
| YA-005 | Bounded Agent Loop | agent:coding/sisyphus | Coding Agent | project:YA | 2026-06-11T23:40Z | 7/7 agent loop tests, ruff+mypy clean | 文本、工具、失败、取消和 max-step 路径均有确定结果 |
| YA-007 | Shared Workspace and Task State Commands | agent:coding/sisyphus | Coding Agent | project:YA | 2026-06-11T23:40Z | 16/16 task store tests, ruff+mypy clean | task CLI 可用，并发 claim 无双 owner，事件可重放 |
| YA-006 | CLI Chat, Run, Doctor and Tool Listing | agent:coding/sisyphus | Coding Agent | project:YA | 2026-06-11T23:55Z | 10/10 CLI tests, ruff+mypy clean, all 4 commands verified | 四类 CLI 命令及 exit code 通过自动/手工验收 |

## Task Card Update Checklist

每次状态变化同时更新：

- owner、role、scope 与 status。
- 时间戳（UTC）。
- blocked reason 或报告链接。
- 验收证据。
- 根 `WHITEBOARD.md` 中仍有效的跨 agent 注意事项。
- 若任务已显式导入 runtime，则更新对应 event store；不得人工双写两个任务板。
