# YA Shared Whiteboard

> 用途：记录短期、可变化、跨 agent 有用的信息。这里不是架构决策、需求真相或完成记录；稳定结论应迁移到对应正式文档。

## Current Context

- 项目阶段：v0.1 Local Agent Core — YA-001 Done, YA-002/003/004 Ready。
- 当前 milestone：v0.1 Local Agent Core。
- 下一可领取任务：YA-002 (Provider), YA-003 (Session Store), YA-004 (Tool Registry) — 可并行。
- 默认运行平台：Linux。
- 默认远程访问方式：Windows 使用 SSH 本地端口转发访问 Linux 上绑定 `127.0.0.1` 的服务。
- 真实 multi-agent runtime 不属于 v0.1；当前先使用文档流程和最小 task 命令。
- Root Agent 不属于 v0.1；v0.1 只实现 Session Agent 与基础 capability/scope primitives。

## Active Assumptions

| ID | Assumption | Owner | Validate By | Outcome |
|---|---|---|---|---|
| A-001 | 使用现代、仍受支持的 Python 3.x；具体最低版本由 YA-001 根据依赖验证后固定 | YA-001 owner | YA-001 Review | Verified: Python >=3.12, uv 0.11.6, all deps resolve |
| A-002 | MiniMax OpenAI-compatible Chat Completions 足以支持 v0.1 文本 streaming 与 tool call | YA-002 owner | YA-002 Testing | Open |
| A-003 | SQLite 足以支持单机 v0.1 会话持久化 | YA-003 owner | YA-003 Testing | Open |
| A-004 | 项目级 `.ya/workspace/` 适合作为工程任务的默认共享目录 | YA-007 owner | YA-007 Review | Open |
| A-005 | capability + scope + confirmation 足以表达 Root/Session/Project 权限，不需要 `is_admin` | V4-001 owner | V4-001 Review | Open |

验证失败时：

1. 在对应任务报告中写明证据。
2. 若影响架构或版本范围，新增 decision。
3. 更新本表 outcome，并删除失效的临时建议。

## Cross-agent Notes

- Provider adapter 不得让 OpenAI SDK 类型越过 `adapters/` 边界。
- tool call 的流式 arguments 可能分段到达，测试必须覆盖重建。
- Markdown Task Board 与未来 runtime store 不能同时作为权威来源。
- 测试不得要求真实 MiniMax key；真实 API 只做 opt-in smoke test。
- 中文内容、中文文件名和 Windows 常见错误编码是必测项。
- v0.1 不要顺手加入 Web、RAG、MCP、Skill 或危险工具。

## Shared Todo Lists

### TODO.project.md 的用途

记录项目级、尚未形成正式 task package 的候选工作。Planner 定期清理并迁移到 Roadmap/Plan/Task Board。

建议格式：

```markdown
- [ ] IDEA-001 简短描述
  - source: <来源>
  - rationale: <价值>
  - target: v0.x or untriaged
  - owner: unassigned
```

### TODO.agent.md 的用途

记录某次 agent 运行中的短期步骤，只对当前 owner 有约束。任务结束时必须清空、归档或将未完成内容交回 Task Board。

建议格式：

```markdown
# <task-id> / <agent-id>
- [x] 已完成步骤
- [ ] 下一步骤
```

TODO 文件不能替代任务卡，不能用 TODO 绕过验收标准。

## Handoff Scratch Format

跨 agent 临时交接写入 `.ya/workspace/handoffs/<task-id>/<stage>.md`：

```markdown
# Handoff: <task-id>

- From:
- To:
- Commit/working tree:
- Files changed:
- Commands run:
- Tests:
- Known failures:
- Deviations:
- Required next action:
```

## Conflict Notes

若多个 agent 需要写同一共享文件：

1. 先确定单一 merge owner。
2. 其他 agent 写各自 handoff/report，不直接改汇总文件。
3. merge owner 持锁后读取最新版本并合并。
4. 无法自动合并时保留双方内容并记录冲突，不静默覆盖。

## Parking Lot

- v0.2 选择 embedding provider 与本地/远程 vector store。
- v0.2 确认 MinerU API 的认证、额度、文件大小和异步任务契约。
- v0.3 选择 TUI framework。
- v0.3 定义社区 Skill Hub 的首个兼容源。
- v0.4 决定 worker 进程模型与 lease heartbeat 周期。
- v0.2 选择 cron expression parser，并验证 IANA timezone/DST 行为。
- v0.3 确定 scheduler 的危险任务持久授权和日志保留默认值。
- v0.2 确定 session privacy label、summary freshness 和跨 session search redaction。
- v0.4 确定 audit retention、confirmation expiry 和默认 project role matrix。
