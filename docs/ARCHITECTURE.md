# YA Architecture

## 1. 架构目标

YA 采用分层、端口与适配器结合的模块化单体架构。早期不拆微服务，但要求核心业务不依赖 CLI、FastAPI、MiniMax、MinerU、具体向量库或 MCP transport。

优先属性：

- 可测试：核心流程可使用 fake provider、内存存储和 fake tool 验证。
- 可替换：供应商、存储、界面和 transport 通过协议隔离。
- 可审计：agent step、tool call、任务状态变化和危险操作有事件记录。
- 可恢复：会话和任务状态在进程退出后可恢复。
- 可约束：agent loop 有最大步数、超时、取消和失败终止条件。

## 2. 逻辑分层

```text
Interfaces
  CLI / TUI / FastAPI / MCP Server
          |
Application Services
  Chat / Agent Run / Session / Root / Project / Task / Memory / RAG /
  Skill / Tool / Scheduler
          |
Domain
  Messages / Sessions / Agents / Roles / Projects / Instructions / Tasks /
  Permissions / Audit / Memory / Cron Jobs
          |
Ports
  LLMProvider / Tool / SessionStore / TaskStore / Parser / Embedder /
  VectorStore / MemoryStore / MCPTransport / SkillSource / SyncBackend /
  CronJobStore / SessionRegistry / AuditSink / Clock
          |
Adapters
  MiniMax / SQLite / Markdown / MinerU / markitdown / MCP / Git / Vector DB
```

依赖只能向内：adapter 实现 port，domain 不导入 adapter。

## 3. 建议源码结构

该结构是模块边界，不要求一次性创建所有目录：

```text
src/ya/
  domain/
    agents/
    messages/
    sessions/
    projects/
    permissions/
    audit/
    tasks/
    tools/
    memory/
    scheduler/
  application/
    chat.py
    runs.py
    sessions.py
    root.py
    projects.py
    instructions.py
    tasks.py
    rag.py
    scheduler.py
  ports/
    llm.py
    stores.py
    parsers.py
    embeddings.py
    tools.py
    scheduler.py
    permissions.py
  adapters/
    llm/minimax.py
    stores/sqlite.py
    memory/markdown.py
    parsers/mineru.py
    parsers/markitdown.py
    mcp/
    git/
  tools/
    builtin/
    registry.py
    policy.py
  skills/
    loader.py
    registry.py
  scheduler/
    models.py
    store.py
    runner.py
    cron.py
    service.py
  permissions/
    models.py
    policy.py
    guard.py
    audit.py
  interfaces/
    cli/
    tui/
    api/
  config/
  observability/
tests/
  unit/
  integration/
  fixtures/
```

禁止为了匹配目录图而创建无行为的空抽象。目录随任务逐步出现。

`scheduler/` 是明确能力边界。实施时可按现有模块风格调整文件名，但 job model、持久化、schedule calculation、runner 和 service lifecycle 的职责不能混入 CLI 或 FastAPI handler。

`permissions/` 是所有管理、工具和跨 scope 操作的统一 guard。业务模块不能根据 role 名称自行跳过检查。

## 4. Agent 核心

### 4.1 LLM provider port

`LLMProvider` 至少表达：

- 普通和流式生成。
- message、tool schema 和 tool result 输入。
- text delta、tool call delta、finish reason、usage 和 provider error 输出。
- provider capability 查询，例如 tools、streaming、vision。

MiniMax 当前可通过 OpenAI-compatible API 接入，但 `MiniMaxProvider` 必须吸收：

- base URL、认证、模型名和超时。
- 流事件到 YA 事件的转换。
- tool call 参数拼接和校验。
- provider 特有字段、错误码、重试提示和 usage。

application/domain 层不得直接导入 OpenAI SDK 或 MiniMax 响应类型。

### 4.2 Agent loop

基础循环：

```text
load session/context
  -> call provider with available tools
  -> stream model events
  -> if final text: persist and finish
  -> if tool calls:
       validate -> authorize -> execute -> persist result
       -> append tool result -> next step
  -> stop on max steps / timeout / cancellation / repeated failure
```

所有策略共享同一执行内核：

- ReAct：模型在每步决定回答或调用工具。
- Plan-and-Execute：先生成有界计划，再逐项执行。
- Reflection：在规定检查点产生评价，不允许无限自省。

v0.1 只要求有界的基础 ReAct 风格循环。其他策略后续通过 `AgentStrategy` 扩展。

### 4.3 Agent, Role and Session

Role 是提示词、capability set、默认 scope、可用工具、上下文策略、确认策略和输出契约的组合，不是独立复制的一套 agent loop。

```text
User
└── Root Agent
    ├── Session A
    │   └── Session Agent
    ├── Session B
    │   └── Session Agent
    ├── Project Workspace 1
    │   └── Multi-Agent Team
    │       ├── Planner Agent
    │       ├── Coding Agent
    │       ├── Review Agent
    │       ├── Test Agent
    │       ├── Document Agent
    │       └── Coordinator Agent
    └── Project Workspace 2
        └── Multi-Agent Team
```

- Root Agent 是跨 session/project 的全局协调身份，但所有管理操作仍经过 permission guard。
- Session Agent 只存在于一个 session scope，默认不能读取或控制其他 session。
- Project Agent 绑定 project/workspace；Planner、Coding、Review、Test、Document 和 Coordinator 共享执行内核，但 capability 不同。

每次 agent run 必须记录 `agent_id`、`role_id`、owner、origin、session/project/workspace scope 和 permission profile。

### 4.4 Core Control Objects

对象关系：

```text
Project 1---1 Workspace
Project 1---0..1 Multi-Agent Team
Session 0..*---0..1 Project
Session 1---1 default Session Agent
Agent *---1 AgentRole
Task *---1 Session or Project
TaskBoard/Whiteboard 1---1 Workspace
Instruction *---1 source Agent and target Session
AgentEvent/AuditLog *---1 actor/run
Permission *---1 Capability and Scope
```

核心对象：

- `Session`：消息、run、session-local context 和生命周期容器。
- `Agent`：可追踪执行身份。
- `AgentRole`：capability、默认 scope、工具和确认策略模板。
- `Project`：大型工作目标和 team 容器。
- `Workspace`：文件、task board、whiteboard、report 和 lock 的边界。
- `Task`：绑定 session/project、owner、role、scope 和验收标准。
- `TaskBoard` / `Whiteboard`：人类可读状态投影与短期上下文。
- `Instruction`：跨 session 的持久化、可审计命令对象。
- `AgentEvent`：普通生命周期/业务事件。
- `AuditLog`：安全、管理和高危操作的 append-only 记录。
- `Permission`：capability 在指定 scope 上的 allow/deny/confirm 规则。
- `Capability`：稳定动作标识，例如 `session.inspect`、`git.push`。

完整字段和状态见 [AGENT_ROLES_AND_PERMISSIONS.md](AGENT_ROLES_AND_PERMISSIONS.md)。

### 4.5 Session Lifecycle and Cross-session Instruction

Session 状态：

```text
active -> paused -> active
active/paused -> archived
active/paused/archived -> closed
```

- paused：停止新自动 run，可恢复。
- archived：保留并只读检索。
- closed：停止执行，不接受新 instruction。
- hard delete 不属于普通生命周期；若提供必须是 dangerous capability。

跨 session instruction：

```text
Root Agent request
-> authorize session.instruction.send
-> optional user confirmation
-> persist Instruction
-> target session validates state and accepts/rejects
-> delegated run executes with target session permissions
-> persist result summary and audit
```

Root Agent 发送的 instruction 不向目标 Session Agent 传递 root capability。

### 4.6 Capability-based Permission

Capability 使用 `<resource>.<action>`，例如：

```text
session.list
session.inspect
session.instruction.send
session.spawn
project.create
project.team.start
workspace.write
cron.manage
tool.execute.dangerous
mcp.invoke
git.push
```

统一决策顺序：

```text
explicit deny -> scope validity -> role grant -> resource policy
-> risk/origin policy -> confirmation/persistent allow -> decision + audit
```

Root Agent 可以申请 global scope capability，但不能静默绕过 deny、确认或审计。

## 5. Tool 系统

### 5.1 统一注册表

所有工具归一为：

```text
name
description
JSON schema
source: builtin | custom | mcp
risk: safe | guarded | dangerous
permissions
timeout
enabled
version
handler
```

Python 函数可通过类型标注和显式 metadata 生成 schema。生成失败或 schema 含糊时拒绝注册，不猜测参数。

### 5.2 执行管线

```text
lookup -> enabled check -> schema validation -> permission policy
-> optional confirmation -> timeout-bound execution -> normalized result
-> audit event -> circuit breaker update
```

危险操作包括但不限于 shell、文件写入、删除、Git push、凭据访问和外部系统变更。非交互运行中若没有预授权策略，必须拒绝而不是默认同意。

MCP 工具进入同一个 registry，不能绕过策略。

## 6. Multi-agent 与任务控制

### 6.1 任务状态机

```text
Backlog -> Ready -> In Progress -> Review -> Testing -> Done
                       |             |          |
                       +-----------> Blocked <--+
Review/Testing -> In Progress  (带反馈)
```

每个任务必须有唯一 ID、owner、scope、输入、输出、测试、验收标准和非目标。状态变化必须有操作者、时间、原因和证据。

### 6.2 Coordinator

后续 runtime 中 Coordinator 负责：

- 原子 claim 任务和 owner lease。
- 限制每个 worker 同时只持有一个任务。
- 按状态选择下一角色。
- 检测重复分派、超时、失联和循环退回。
- 限制同一任务的 review/test 往返次数，超限后升级给用户。
- 汇总事件并更新 Markdown 投影。

Coordinator 不替代 Planner 的优先级判断，也不替代 Reviewer/Test Agent 的专业判断。

## 7. 项目目录与运行时边界

### 7.1 项目源码文档

以下内容属于 Git 管理的长期工程事实：

```text
README.md
AGENTS.md
CHANGELOG.md
DECISIONS.md
TASK_BOARD.md
WHITEBOARD.md
docs/
plans/
reports/
```

- `docs/`：稳定的目标、架构和专题设计。
- `plans/`：按版本拆分的任务包。
- `reports/`：可复用模板和经确认的阶段报告。
- 根 `TASK_BOARD.md`：YA 项目本身的开发计划，不是 YA 将来管理的任意用户项目任务。
- 根 `WHITEBOARD.md`：当前仓库开发期的临时假设。

### 7.2 Multi-agent 运行时共享文件

项目级 runtime 使用 `.ya/workspace/`：

```text
.ya/workspace/
  README.md
  TASK_BOARD.md
  WHITEBOARD.md
  TODO.project.md
  TODO.agent.md
  reports/
  handoffs/       # runtime 创建
  locks/          # runtime 创建，不提交
  events.jsonl    # runtime 创建，append-only
```

该目录服务于 YA 执行中的 agent team。根任务板与 runtime 任务板用途不同，不相互自动覆盖。需要把 YA 自身作为被管理项目时，必须由明确导入操作生成 runtime task，不能靠双写同步。

### 7.3 运行时数据

```text
.ya/
  memory/         # Markdown memory；是否纳入独立 memory repo 由用户配置
  rag/            # source metadata、解析产物、chunk 和可重建 vector index
  logs/           # agent/tool/scheduler/audit 运行日志
  cron/           # job store、scheduler metadata 和 job run 引用
  tmp/            # 可清理中间文件
```

全局用户级 registry 建议：

```text
~/.ya/
  state/ya.db
  sessions/<session-id>/workspace/
  projects/<project-id>/metadata/
  logs/audit/
```

project 的真实源码 workspace 可以位于任意用户授权路径，registry 只保存 canonical path 和 policy，不复制整个项目。

- runtime 数据不得与 `docs/`、`plans/` 混放。
- secret 不得写入任何上述目录的普通文件。
- `.ya/cron/` 中的 job 只能引用 credential/profile ID 或环境变量名。
- `.ya/tmp/` 可被 cleanup job 删除；其他目录不能被 cleanup 默认递归删除。
- 用户级等价目录位于 `~/.ya/`，项目级配置优先级必须显式定义。

## 8. 共享 Workspace

### 8.1 位置与优先级

- 项目级：`<project>/.ya/workspace/`
- 用户级：`~/.ya/workspace/`

项目任务优先使用项目级目录；跨项目个人任务使用用户级目录。路径可由配置覆盖。

### 8.2 建议结构

```text
.ya/workspace/
  README.md
  TASK_BOARD.md
  WHITEBOARD.md
  TODO.project.md
  TODO.agent.md
  events.jsonl
  handoffs/<task-id>/
  reports/
  locks/
```

根文件用于 YA 仓库开发，`.ya/workspace/` 文件用于 YA runtime 管理的工作。两者不是同一份状态的双重投影。

### 8.3 并发规则

- `events.jsonl` 为 append-only；每行一个完整 UTF-8 JSON 事件。
- task claim 与状态转换使用文件锁和原子替换，不能直接无锁覆盖。
- 一个任务同一时刻只有一个 owner；owner 使用 lease/heartbeat，不能永久占用。
- agent 只写自己的 handoff/report 文件；共享汇总由 Coordinator 或指定 Document Agent 合并。
- 临时文件使用 `<task-id>/<agent-id>/` 隔离。
- 冲突时保留双方内容，记录冲突事件，由 owner 或 Document Agent 合并；禁止静默 last-write-wins。

## 9. 存储设计

| 数据 | 权威存储 | 说明 |
|---|---|---|
| 运行配置 | 环境变量 + 配置文件 | 密钥不进入普通配置文件 |
| 会话、消息、run、tool event | SQLite | 本地事务、恢复和查询 |
| Session registry/project/agent | SQLite | 生命周期、scope 和 role binding |
| Instruction | SQLite/event store | 跨 session 状态与结果关联 |
| 任务事件 | append-only JSONL/SQLite | Markdown Task Board 是人类投影 |
| 长期记忆 | Markdown | Obsidian-compatible，索引可重建 |
| 文档原文/解析产物 | 文件系统 + metadata DB | 保存来源、hash、parser 版本 |
| embedding/vector | VectorStore adapter | 不作为原文唯一副本 |
| Skill | 目录 + `SKILL.md` | 安装来源和 hash 可审计 |
| Cron job/run | SQLite 或 `.ya/cron/` store | 事务更新；配置不含 secret 明文 |
| Permission/confirmation | SQLite/config | deny/allow/confirm、scope、expiry |
| Audit log | append-only SQLite/JSONL | 高危与管理事件；脱敏且普通 agent 不可修改 |

SQLite schema 变更必须使用迁移。所有时间存储为 UTC ISO 8601，显示时再转本地时区。

## 10. Memory

Markdown memory 是长期事实源，建议：

```text
~/.ya/memory/
  daily/YYYY/MM/YYYY-MM-DD.md
  projects/<project>/index.md
  topics/<topic>.md
  episodes/<year>/<id>.md
```

frontmatter 最小字段：

```yaml
---
id: mem-...
title: ...
created_at: 2026-06-11T00:00:00Z
updated_at: 2026-06-11T00:00:00Z
type: semantic
tags: [ya, project]
projects: [YA]
source: conversation
---
```

正文可使用 `[[YA]]` 等 wikilink。文件名、frontmatter 和正文均为 UTF-8。

GitHub 同步通过 `SyncBackend` 执行 status、commit、pull/rebase、冲突检测和 push。冲突不得自动丢弃任一版本；token 只从安全配置读取。

## 11. 文档解析与 RAG

### 11.1 Parser port

`DocumentParser` 输入 source 和 options，输出统一 `ParsedDocument`：

- text/markdown blocks。
- page/section/source location。
- media references。
- metadata、warnings、parser name/version。

adapter 顺序：

1. MinerU API：优先处理支持的复杂文档。
2. markitdown：离线或 API 失败时的 fallback。
3. 后续 image/video/audio/media parser adapter。

fallback 必须记录原因，不能把低质量解析伪装成 MinerU 成功结果。

### 11.2 RAG pipeline

```text
ingest -> identify/hash -> parse -> normalize -> chunk
-> embed -> upsert vector index -> query -> rerank(optional)
-> citation/context pack -> agent context
```

chunk 必须保留 source、document ID、section/page、content hash 和 parser version。项目知识库与个人知识库使用不同 namespace，并支持显式跨库查询。

## 12. MCP 与 Skill

### MCP

- v0.3 首先支持 MCP client 的 stdio transport。
- MCP server 提供 YA 明确允许暴露的工具子集。
- HTTP/SSE transport 后续添加，不改变 registry 契约。
- 外部 server 需要 allowlist、启动命令审查、环境变量过滤、超时和日志。

### Skill

Skill 目录包含 `SKILL.md` 与可选资源。loader 解析 metadata、描述、触发条件和所需权限。Skill 内容是上下文/流程能力，不自动获得工具权限。

社区 Skill 安装需记录来源、版本或 commit、内容 hash 和启用状态；默认安装后禁用，审查后启用。

## 13. Scheduler / Cron

Scheduler 负责在无人交互时触发已授权的 application command。它不绕过 agent loop、tool policy、memory sync 或 RAG service。

建议模块：

```text
src/ya/scheduler/
  models.py      # CronJob, JobRun, JobStatus, RetryPolicy
  store.py       # persistent job/run store
  cron.py        # expression parsing and next-run calculation
  runner.py      # timeout-bound dispatch and result normalization
  service.py     # tick loop, lifecycle, pause/resume and recovery
```

支持的 schedule：

- 标准 cron expression。
- interval。
- daily、weekly、monthly calendar schedule。
- timezone 明确保存；内部 next run 使用 UTC。

支持的 job type：

- prompt run。
- registered tool run。
- memory sync / GitHub memory push。
- RAG re-index。
- task board check / daily review。
- workspace cleanup。
- report generation。

job type 按版本启用。v0.2 只允许 prompt、安全 tool 和本地维护类任务；依赖 GitHub、RAG 或外部 MCP 的 job 在对应能力可用后启用。

执行流程：

```text
load due jobs -> atomically claim run -> resolve credential references
-> authorize job type/tool -> execute with timeout and run limits
-> persist result/log reference -> calculate next run
-> bounded retry or terminal failure
```

关键约束：

- job 必须持久化，支持 create/list/pause/resume/delete/manual run。
- 同一计划触发使用 deterministic occurrence key，避免进程恢复后重复执行。
- retry 有最大次数和 backoff；不能无限重试。
- prompt job 与 agent run 都有 max steps、timeout 和 child-run depth。
- scheduler 触发的 agent 不得创建立即触发自身的 job；达到 recursion/depth 限制时拒绝。
- dangerous tool、Git push、删除和外部 MCP 需要 job 级权限快照或审批策略。
- job config 使用 UTF-8，只保存 secret reference，不保存 token/value。
- 每次 run 写结构化状态、开始/结束时间、attempt、错误分类和日志引用。

完整契约见 [SCHEDULER.md](SCHEDULER.md)。

## 14. Interfaces

CLI、TUI 和 FastAPI 调用 application services：

- CLI：脚本、诊断和低依赖入口。
- TUI：对话、stream、tool event 和任务板展示。
- FastAPI：Web UI API、SSE/WebSocket stream、配置和状态接口。
- Scheduler：后台 service；CLI/TUI/Web 只调用其 application service。

FastAPI 初始 endpoint 目标：

```text
POST /api/chat
GET  /api/chat/{run_id}/events
GET  /api/tools
GET  /api/memory
POST /api/rag/query
GET  /api/tasks
GET  /api/root/sessions
GET  /api/root/status
GET  /api/root/agents
POST /api/root/search
POST /api/root/summarize-all
GET  /api/root/sessions/{session_id}
POST /api/root/sessions/{session_id}/summarize
POST /api/root/sessions/{session_id}/instructions
POST /api/root/sessions
POST /api/root/sessions/{session_id}/pause
POST /api/root/sessions/{session_id}/resume
POST /api/root/sessions/{session_id}/archive
POST /api/root/sessions/{session_id}/close
GET  /api/root/audit
GET  /api/cron/jobs
POST /api/cron/jobs
POST /api/cron/jobs/{job_id}/pause
POST /api/cron/jobs/{job_id}/resume
POST /api/cron/jobs/{job_id}/run
GET  /api/cron/jobs/{job_id}/runs
GET  /api/config
GET  /health
```

API schema 与 domain model 分离。默认监听 `127.0.0.1`，详见 `docs/SSH_WEB_UI.md`。

Root CLI 目标：

```text
ya root sessions
ya root inspect <session_id>
ya root summarize <session_id>
ya root summarize-all
ya root search <query>
ya root status
ya root active-agents
ya root summarize-today
ya root sync-memories
ya root send <session_id> <instruction>
ya root spawn <task>
ya root project create <name>
ya root team start <project_id>
ya root pause|resume|archive|close <session_id>
```

这些接口按 Roadmap 分阶段启用。未实现或未授权的 action 必须明确拒绝，不能退化为普通 chat prompt。

## 15. 安全与编码基线

- 默认 UTF-8；Python `open()`、`read_text()`、`write_text()` 显式使用 `encoding="utf-8"`。
- 测试至少覆盖含中文路径和内容，防止 cp936、GBK、cp1252 环境问题。
- secret 不进入日志、prompt、异常文本、Git 或示例值。
- prompt injection 内容不能直接改变工具权限和系统策略。
- 外部 parser、MCP、Skill 与文档均按不可信输入处理。
- 网络调用配置超时、有限重试和取消。
- tool output 有大小上限；超限内容落盘后仅注入摘要/引用。
- Web UI 不默认公网监听；任何 `0.0.0.0` 使用都需显式警告。
- scheduler job 不继承交互会话中的临时授权；必须使用持久化的最小权限策略。
- cron 配置只引用 secret，不保存 secret value。
- Session Agent 默认不能访问其他 session；Project Agent 默认不能越过 project workspace。
- Root Agent 的跨 session 写入和危险操作必须经过 capability guard、确认策略和 audit。
- delegated instruction 在目标 session 权限下执行，不继承 source agent 的更高权限。

## 16. 可观测性

每次 run 使用 correlation ID。结构化事件至少包含：

- run/session/task/agent ID。
- role、owner、origin、project/workspace scope 和 permission decision ID。
- provider、model、latency、usage。
- tool name、risk、authorization、duration、result status。
- 状态转换、失败分类和重试次数。
- cron job/run/occurrence ID、scheduled time、attempt、next run 和 terminal status。
- cross-session instruction source/target/status/result summary。

日志不得记录 API key、完整敏感文档或未经脱敏的 tool 参数。

## 17. 关键扩展点

稳定 port：

- `LLMProvider`
- `AgentStrategy`
- `Tool` / `ToolRegistry` / `PermissionPolicy`
- `SessionStore` / `SessionRegistry` / `TaskStore` / `MemoryStore`
- `PermissionGuard` / `AuditSink`
- `InstructionQueue`
- `DocumentParser`
- `Embedder` / `VectorStore` / `Retriever`
- `MCPTransport`
- `SkillSource`
- `SyncBackend`
- `CronJobStore` / `Clock` / `JobExecutor`

新增实现优先实现 port，不修改核心流程中的供应商条件分支。
