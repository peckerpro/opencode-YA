# Agent Roles, Sessions and Permissions

## 1. Purpose

YA 不把所有 agent 当作同一权限主体。每次执行必须明确：

- 谁在执行：`Agent` / `AgentRole`。
- 为谁执行：用户、root-agent、session 或 project team。
- 在哪里执行：global、session 或 project workspace scope。
- 可以做什么：`Capability`。
- 为什么被允许：role grant、session/project policy、用户确认或持久 allowlist。
- 如何追踪：`AgentEvent` 和 `AuditLog`。

高权限 role 可以申请更多操作，但不能绕过统一 permission guard。

## 2. System Relationship

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

Root Agent 是全局管理主体，但不是超级用户绕过器。Session Agent 和 project role 都是受 scope 限制的执行主体。

## 3. Domain Objects

### Session

```text
id
title
kind: personal | project | system
status: active | paused | archived | closed
project_id
workspace_id
default_agent_id
privacy_label
summary
created_at
updated_at
last_activity_at
version
```

规则：

- session 是消息、run、instruction 和 session-local context 的容器。
- `paused` 不接受普通自动执行；`archived` 只读；`closed` 不再恢复运行，除非显式 reopen policy。
- summary 是可重建投影，不代替原消息。
- privacy label 和 project membership 参与跨 session 检索授权。

### Agent

```text
id
name
role_id
status
session_id
project_id
workspace_id
permission_profile_id
created_by
created_at
last_heartbeat_at
```

Agent 是一次可追踪的执行身份。Root Agent 可以是长期逻辑身份，但每次 run 仍创建具体 agent/run correlation。

### AgentRole

```text
id
name
role_class: root | session | project
capability_set
default_scope
tool_allowlist
memory_policy
instruction_policy
confirmation_policy
max_run_limits
```

role 是默认权限模板，不是最终授权结果。实际权限还要与 session/project policy、用户配置和资源 scope 求交集。

### Project

```text
id
name
status
workspace_id
owner
privacy_label
team_id
created_at
updated_at
```

### Workspace

```text
id
kind: session | project
root_path
read_roots
write_roots
task_board_ref
whiteboard_ref
report_root
lock_root
```

文件访问必须通过 canonical path 和 allowlisted root 验证，防止 path traversal 和 symlink escape。

### Task / TaskBoard / Whiteboard

- Task 绑定 `project_id` 或 `session_id`，并记录 owner、role、scope、状态和验收标准。
- Project team task 必须绑定 project workspace。
- TaskBoard 是状态投影；事件 store 是 runtime 上线后的权威来源。
- Whiteboard 是短期共享上下文，不承载权限授予。

### Instruction

```text
id
source_agent_id
source_session_id
target_session_id
target_agent_id
root_request_id
content
status: queued | accepted | running | completed | rejected | cancelled
created_at
delivered_at
completed_at
result_summary
permission_decision_id
```

跨 session instruction 是显式消息对象，不直接注入目标 session 的 system prompt。目标 session 在边界处验证来源、状态和权限，再形成可审计的 user/delegated instruction。

### AgentEvent

记录普通生命周期和业务事件，例如 session created、agent spawned、task claimed、instruction delivered、tool called、run completed。

### AuditLog

记录安全与管理决策。Audit log append-only，普通 agent 不能修改或删除。

### Permission

```text
id
capability
effect: allow | deny | confirm
scope_type
scope_id
resource_pattern
conditions
expires_at
granted_by
reason
```

### Capability

Capability 是稳定、可组合的动作标识，格式建议为：

```text
<resource>.<action>
```

示例：

```text
session.list
session.inspect
session.summarize
session.search
session.instruction.send
session.spawn
session.pause
session.resume
session.archive
session.close
session.delete
agent.list
system.status.read
report.global.generate
project.create
project.team.start
workspace.read
workspace.write
task.read
task.transition
memory.read
memory.write
memory.sync
rag.query
rag.reindex
cron.read
cron.manage
tool.execute.safe
tool.execute.guarded
tool.execute.dangerous
mcp.invoke
git.push
audit.read
```

禁止用单一 `is_admin=true` 代替 capability 判断。

## 4. Scope Model

scope 至少包括：

```text
global
session:<session_id>
project:<project_id>
workspace:<workspace_id>
task:<task_id>
resource:<resource_id>
```

Permission decision 输入：

```text
subject agent
role grants
requested capability
target resource and scope
session/project policy
tool risk
execution origin: interactive | scheduled | delegated
user confirmation/allowlist
```

决策顺序：

```text
explicit deny
-> scope validity
-> role capability
-> resource/project/session policy
-> risk and execution-origin policy
-> confirmation or persistent grant
-> allow/deny + audit
```

deny 优先。Root role 也必须经过该流程。

## 5. Root Agent

### Position

`root-agent` 是用户管理 YA 的全局秘书和协调入口。它跨 session、project 和 subsystem 查看状态、生成摘要和发起管理动作。

Root Agent 不是某个普通 Session Agent。界面可以为用户与 Root Agent 的对话保存 control session，但全局身份、权限和 audit subject 独立于该对话 session。

Root Agent 可以被配置为拥有与用户相当的管理 capability，但用户始终是 policy/confirmation 的最终授权者，Root Agent 不能修改保护自身权限的 deny 规则。

### Baseline Capabilities

- 查看所有允许范围内的 session 摘要、状态、任务板、白板和最近活动。
- session list、inspect、summarize、search。
- 查看 active agents、projects、task boards 和 scheduler。
- 查看 memory、RAG index、MCP server、Skill 和 Tool Registry 状态。
- 生成全局日报、项目状态报告和 session overview。
- 建议用户关注的 session/project。

典型语义命令：

```text
list sessions
summarize all sessions
inspect session <session_id>
send instruction to session <session_id>
spawn session for <task>
start project team for <project>
show active agents
show task boards
show cron jobs
summarize today
sync memories
```

### Managed Capabilities

需要 policy/confirmation：

- 向 session 发送 instruction。
- spawn、pause、resume、archive、close session。
- 创建 project workspace 或启动 project team。
- 修改全局 scheduler。
- memory sync、Git push、危险 tool、shell、删除和外部 MCP。

Root Agent 可以提出请求和组织上下文，但 guard 做最终决定。

### Root Audit

所有 root run 写：

- source user/root agent/run。
- requested capability。
- target session/project/resource。
- decision、confirmation actor 和 policy rule。
- result、error、timestamp 和 correlation IDs。

## 6. Session Agent

Session Agent 默认只能：

- 访问当前 session 的消息、摘要和 workspace。
- 操作当前 session task board/whiteboard。
- 调用 session policy 允许的 tools/skills/memory/RAG。
- 在当前 session 内执行 prompt、文档处理和任务。

默认禁止：

- 查看、搜索或控制其他 session。
- 向其他 session 发送 instruction。
- spawn session。
- 管理全局 cron、global memory sync、MCP server 或 Skill 安装。
- 访问其他 project workspace。

若需要越界，Session Agent 必须创建 permission request 或委托给 Root Agent。一次授权不得自动变成永久授权。

## 7. Project Multi-Agent Team

Team 绑定唯一 project/workspace。所有角色共享 project scope，但 capability 不同。

| Role | Default capabilities | Default restrictions |
|---|---|---|
| Planner | project/task/doc read；创建任务包；维护 project roadmap/board | 不直接修改产品代码或全局设置 |
| Coding | 读取 project；修改任务卡允许文件；运行允许的开发命令 | 一次一个任务；不能写全局 memory；不能跨 project |
| Review | project/code/test/doc read；创建 review report | 默认只读；未经授权不修代码 |
| Test | project read；写测试/测试报告；运行 allowlisted test command | 危险 shell、外部变更需确认 |
| Document | project docs/report write；更新 alignment/decision/changelog | 不修改产品代码；全局 memory 需批准 |
| Coordinator | team spawn/stop；task claim/transition；status aggregate | 不能代替 root 执行 global/session 管理或危险工具 |

附加规则：

- Coding Agent 不直接修改全局 memory；项目经验由 Document Agent 提议，Root/User 批准后提升。
- Review Agent 的小修权限必须是显式 capability，且修改仍需重新测试。
- Test Agent 的命令按 executable/argument/workdir allowlist 判断，不能因名称含 `test` 自动信任。
- Coordinator 只调度 team 内 agent，并向 Root Agent 汇总状态。

## 8. Cross-session Operations

目标 CLI：

```bash
ya root sessions
ya root inspect <session_id>
ya root summarize <session_id>
ya root summarize-all
ya root search "<query>"
ya root status
ya root active-agents
ya root summarize-today
ya root sync-memories
ya root send <session_id> "<instruction>"
ya root spawn "<task>"
ya root project create "<name>"
ya root team start <project_id>
ya root pause <session_id>
ya root resume <session_id>
ya root archive <session_id>
ya root close <session_id>
```

### Read Flow

```text
root request -> session registry query -> privacy/scope filter
-> summary/search service -> redaction -> result + audit
```

跨 session search 默认优先索引/摘要，只有明确 inspect 权限时读取原消息。

### Instruction Flow

```text
root request
-> authorize session.instruction.send on target
-> optional user confirmation
-> persist Instruction
-> enqueue/deliver
-> target session validates state and accepts/rejects
-> execute as delegated run with target session policy
-> persist result summary and audit
```

Root Agent 的 instruction 不能把目标 session 的权限提升到 root 权限。

### Lifecycle Flow

- spawn：创建 Session、Workspace 和默认 Session Agent。
- pause：停止新 run/scheduled delivery，不删除状态。
- resume：恢复接收任务。
- archive：只读保留，可搜索但不主动运行。
- close：终止活动 run，禁止新 instruction；数据保留按 retention policy。

删除 session 不作为常规生命周期命令。若未来提供 hard delete，必须使用独立 `session.delete` dangerous capability、二次确认、retention/tombstone 和 audit；计划不早于 v0.5。

## 9. Permission Modules

建议结构：

```text
src/ya/permissions/
  models.py
  policy.py
  guard.py
  audit.py
```

- `models.py`：Capability、Permission、Scope、Decision、Confirmation。
- `policy.py`：role grants、deny precedence、conditions 和配置加载。
- `guard.py`：统一 authorization API；tool、session、scheduler、MCP、Git 都调用。
- `audit.py`：append-only security/management audit sink 和查询。

业务 handler 不允许自行使用 role 名称判断，例如 `if role == "root"`。必须请求 capability。

## 10. Confirmation and User Policy

用户可配置：

- always allow。
- allow within scope。
- ask every time。
- deny。
- temporary allow with expiry。

建议默认：

| Operation | Root Agent | Session Agent | Project Team |
|---|---|---|---|
| Read own/current scope | Allow | Allow | Allow |
| Cross-session summary | Allow + audit | Deny | Deny |
| Cross-session raw inspect | Confirm for private scope | Deny | Deny |
| Send instruction | Confirm by default | Deny | Team-local only |
| Spawn/pause/resume | Confirm or configured allow | Deny | Coordinator team-local |
| Archive/close | Confirm | Deny | Deny |
| Safe tool | Policy allow | Session allowlist | Role/project allowlist |
| Dangerous tool/Git push | Confirm | Confirm if granted | Confirm if granted |
| External MCP | Allowlist + risk policy | Session allowlist | Project allowlist |
| Global cron/memory sync | Confirm/configured allow | Deny | Deny |

确认记录必须绑定 capability、目标、参数摘要、expiry 和 actor，不能用一次“全部允许”覆盖未来未知操作。

## 11. Audit Model

跨 session instruction 必须记录：

```text
source_agent_id
source_session_id
target_session_id
instruction_id
instruction_digest or protected content reference
timestamp
status
result_summary
permission_decision
```

高危 audit 至少包含：

```text
event_id
actor_agent_id
actor_role_id
owner/user
origin_run_id
capability
target_type
target_id
scope
risk
request_summary
decision
policy_rule
confirmation_actor
started_at
finished_at
result_status
result_summary
error_type
```

敏感 instruction 内容可保存受保护引用或 digest；普通日志不复制完整 secret/私密内容。Audit log 必须 append-only、可查询、可设置保留期，但清理本身也需要审计。

## 12. Interface Design

Web/TUI Root Overview：

- session/project 列表与状态。
- active agents 和最近活动。
- task board/whiteboard summary。
- cron、memory、RAG、MCP、Skill、Tool 状态。
- pending confirmations 和 failed operations。
- session inspect、summary、instruction 和 lifecycle actions。
- global daily report、project status report、attention suggestion 和 memory sync action。

界面必须显示当前执行身份、目标 scope、风险级别和是否需要确认。

## 13. Version Plan

- v0.1：Session Agent、单 session 上下文、基础 `AgentRole`/`Capability`/scope primitives；不实现 Root Agent。
- v0.2：Session registry、Root Agent 只读 session list/inspect summary/search、Root Overview、只读 audit。
- v0.3：Root Agent send/spawn/pause/resume/archive/close、Instruction、Project/Workspace 创建和显式 confirmation。
- v0.4：完整 project multi-agent team、角色 capability matrix、统一 guard、跨 session/project audit、team coordinator。
- v0.5：跨 session 自动调度、scheduler 与 root/team orchestration、policy-based autonomous operation。

## 14. Acceptance Baseline

- Session Agent 无法读取其他 session。
- Project Agent 无法越过 project workspace root。
- Root Agent 的 dangerous/cross-session write 操作不能绕过 guard。
- Instruction 从 source 到 target/result 可完整追踪。
- 每个 task/run 记录 owner、role 和 scope。
- role 变更或 permission 撤销对后续执行立即生效。
- scheduled/delegated run 不继承不适用的临时授权。
- audit 不包含 API key/token 明文。
- UTF-8 session title、instruction、project name 和 audit summary 不乱码。
