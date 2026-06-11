# YA Engineering Decisions

本文件记录影响架构、公共契约、版本范围、安全边界或长期维护成本的决策，以及实施中无法仅靠任务报告解释的重大偏差。

小型实现细节留在代码、task handoff 或 alignment report，不为每个选择创建 ADR。

## Decision Format

```markdown
## DEC-XXXX - Title

- Status: Proposed | Accepted | Superseded | Rejected
- Date: YYYY-MM-DD
- Owners:
- Related tasks:

### Context
### Decision
### Consequences
### Alternatives
### Validation/Revisit
```

---

## DEC-0001 - Use a Modular Monolith with Ports and Adapters

- Status: Accepted
- Date: 2026-06-11
- Owners: Project owner, Document Agent
- Related tasks: YA-001 to YA-008

### Context

YA 目标范围较广，但当前是单用户、单机、从零开始。过早拆微服务会增加部署、调试、事务和版本管理成本，同时供应商与界面确实需要可替换边界。

### Decision

早期采用 Python 模块化单体。domain/application 不依赖 CLI、FastAPI、SDK 或具体存储；外部系统通过 port 和 adapter 接入。

### Consequences

- 单进程开发和测试成本较低。
- 模块边界需要通过 import 规则、review 和测试维护。
- 未来只有在明确的隔离、性能或部署需求出现时才拆服务。

### Alternatives

- 微服务：当前运维成本过高。
- 单层脚本：无法支撑多 provider、工具、RAG 和多界面演化。

### Validation/Revisit

v0.2 完成后检查 application service 是否能被 CLI 与 FastAPI 共同复用。

---

## DEC-0002 - Isolate MiniMax Behind an LLM Provider Contract

- Status: Accepted
- Date: 2026-06-11
- Owners: Project owner, Document Agent
- Related tasks: YA-002, YA-005

### Context

MiniMax 当前提供 OpenAI-compatible API，但兼容范围、字段和推荐 SDK 可能变化。业务代码直接依赖 SDK 会放大变化。

### Decision

定义 YA 自有 `LLMProvider` 与 stream event。MiniMax adapter 可以使用 OpenAI-compatible SDK/HTTP，但 SDK 类型不得越过 adapter 边界。

### Consequences

- 需要维护事件转换和错误归一化。
- fake provider 可直接测试 agent loop。
- 后续增加 provider 不需要重写核心业务。

### Alternatives

- 全项目直接使用 OpenAI SDK 类型：初期简单，长期耦合高。
- 自行实现完整 HTTP client：控制更强，但 v0.1 成本不合理。

### Validation/Revisit

YA-002 依据真实 fixture 和 opt-in smoke test 验证 tool call 与 streaming 兼容性。

---

## DEC-0003 - Use SQLite for Runtime State and Markdown for Long-term Memory

- Status: Accepted
- Date: 2026-06-11
- Owners: Project owner, Document Agent
- Related tasks: YA-003, v0.2 memory tasks

### Context

会话、run 和 task transition 需要事务与查询；长期个人记忆需要人可读、Obsidian-compatible 和 Git-friendly。

### Decision

- SQLite 保存会话、消息、run、tool event 等运行状态。
- Markdown 保存长期 memory，并作为该类内容的事实源。
- 向量索引和 Markdown board 均为可重建投影，不是唯一副本。

### Consequences

- 不强迫一种存储处理所有数据形态。
- 需要定义投影同步和重建流程。
- SQLite schema 需要 migration。

### Alternatives

- 全部 Markdown：并发、事务和查询困难。
- 全部数据库：降低 Obsidian/Git 可读性。

### Validation/Revisit

v0.2 验证删除索引后能从 Markdown/解析产物重建。

---

## DEC-0004 - Keep v0.1 to a Local CLI Agent Closed Loop

- Status: Accepted
- Date: 2026-06-11
- Owners: Project owner, Planner Agent
- Related tasks: YA-001 to YA-008

### Context

完整愿景同时包含 Web、TUI、RAG、memory、MCP、Skill、多模态和 multi-agent runtime。一次实现会导致不可验收的大任务和高集成风险。

### Decision

v0.1 只交付 CLI、MiniMax streaming、多轮持久化、受控 tool call、有界 loop、doctor 和最小共享 task flow。其余按 Roadmap 推迟。

### Consequences

- v0.1 可以形成真实垂直闭环。
- 早期无法使用 Web/RAG/MCP 等目标能力。
- 新需求必须进入 Backlog，不能扩大当前 coding task。

### Alternatives

- 按技术层横向搭全部空壳：看似覆盖广，但无可用闭环。
- 一次实现完整愿景：任务不可控。

### Validation/Revisit

v0.1 alignment 只按 `plans/v0.1.md` 验收，不按最终愿景验收。

---

## DEC-0005 - Use Append-only Events Plus Locked Projections for Shared Tasks

- Status: Accepted
- Date: 2026-06-11
- Owners: Project owner, Document Agent
- Related tasks: YA-007

### Context

多个 agent 可能同时领取任务或更新共享 Markdown。无锁覆盖会产生双 owner 和内容丢失。

### Decision

任务状态变化形成 append-only 事件；claim/transition 使用文件锁或等价原子机制；Markdown Task Board 是投影。每个任务同一时刻只有一个 owner。

### Consequences

- 可以审计和重放状态。
- 需要 lock stale/lease 恢复规则。
- 人工文档阶段仍需指定单一 merge owner。

### Alternatives

- 直接编辑 Markdown 表格：简单但并发不可靠。
- v0.1 引入外部队列/数据库服务：超出单机需求。

### Validation/Revisit

YA-007 必须包含并发 claim 测试。v0.4 再评估 SQLite task store 或独立 coordinator store。

---

## DEC-0006 - Bind Web Services to Loopback by Default

- Status: Accepted
- Date: 2026-06-11
- Owners: Project owner, Document Agent
- Related tasks: v0.2 Web tasks

### Context

YA 会处理私有记忆、代码和危险工具。默认公网监听会扩大攻击面。

### Decision

FastAPI 默认监听 `127.0.0.1`。Windows 访问优先使用 SSH 本地端口转发；监听 `0.0.0.0` 需要显式配置和安全警告。

### Consequences

- 默认无法被局域网直接访问。
- 远程使用需要 SSH 或后续受保护的 gateway。
- 文档和 `doctor` 必须检查绑定配置。

### Alternatives

- 默认 `0.0.0.0`：便利但不符合个人私密 agent 的安全基线。

### Validation/Revisit

v0.2 集成测试验证默认 host，安全 review 检查公网暴露路径。

---

## DEC-0007 - Implement Scheduler Core in v0.2 and High-risk Integrations in v0.3

- Status: Accepted
- Date: 2026-06-11
- Owners: Project owner, Planner Agent, Document Agent
- Related tasks: V2-006, V2-007, V3-007

### Context

Scheduler 依赖 v0.1 的 agent loop、tool policy、持久化和 CLI，但完整能力还会调用 v0.2 memory/RAG/Web 与 v0.3 Git/MCP/Skill。把完整 cron 系统塞进 v0.1 会破坏最小闭环，把全部功能推迟到 v0.3 又会让基础主动执行过晚。

### Decision

- v0.1 只保留 scheduler 架构边界，不实现。
- v0.2 实现持久化 job/run、cron/interval/calendar schedule、prompt/安全 tool/本地维护 job、CLI/API、日志、有限 retry、timeout 和 loop prevention。
- v0.3 接入 GitHub memory push、RAG re-index、外部 MCP、TUI 状态，以及危险任务权限快照、熔断和保留策略。

### Consequences

- scheduler 核心可在不依赖外部生态时独立验收。
- 高风险和供应商集成不会绕过后续安全机制。
- v0.2 范围增加，必须通过 V2-006/V2-007 独立任务控制。

### Alternatives

- v0.1 只做空 skeleton：产生不可运行代码，价值低。
- v0.1 实现完整 scheduler：扩大最小版本。
- v0.3 一次实现全部：延迟 daily review/task check 等基础能力。

### Validation/Revisit

V2-009 验证重启恢复、occurrence 去重、timeout/retry 和无 secret 配置；V3-007/V3-010 验证危险集成授权与熔断。

---

## DEC-0008 - Use Capability and Scope Authorization for Root, Session and Project Agents

- Status: Accepted
- Date: 2026-06-11
- Owners: Project owner, Planner Agent, Document Agent
- Related tasks: YA-003 to YA-005, V2-008, V3-008, V3-009, V4-001 to V4-008

### Context

YA 需要全局 Root Agent、普通 Session Agent 和 project role team。仅使用 `is_admin` 或 role 名称判断会导致 Root Agent 绕过安全边界，也无法表达 project/session 隔离、临时确认和 scheduler/delegated origin。

### Decision

- 使用稳定 `Capability`、资源 `Scope`、allow/deny/confirm `Permission` 和统一 `PermissionGuard`。
- Root Agent 可申请 global/cross-session capability，但 explicit deny、确认和 audit 仍适用。
- Session Agent 默认仅有当前 session scope。
- Project role 默认仅有所属 project/workspace scope，并按 Planner/Coding/Review/Test/Document/Coordinator 分配 capability。
- 跨 session instruction 在目标 session 权限下执行，不继承 source/root capability。
- 每次 run/task 记录 owner、role、scope 和 permission decision。

### Consequences

- 需要 session registry、instruction、confirmation 和 append-only audit 数据模型。
- 所有 tool、scheduler、MCP、Git、session 和 project handler 必须使用同一 guard。
- 角色配置更清晰，但 permission matrix 和测试量增加。

### Alternatives

- Root Agent 无条件超级用户：无法满足确认和审计要求。
- 每个模块自行判断 role：规则漂移且容易绕过。
- 只按 tool risk 授权：无法覆盖 session/project 管理操作。

### Validation/Revisit

v0.2 验证 Root read 和 Session isolation；v0.3 验证 instruction/lifecycle/project boundary；v0.4 验证完整 team matrix 和统一 audit。

---

## Implementation Deviations

当前没有产品实现，因此没有已知实现偏差。

新增偏差时使用：

```markdown
## DEV-XXXX - Short title

- Date:
- Task:
- Severity: Local | Architecture | Scope
- Planned:
- Implemented:
- Reason:
- Impact:
- Follow-up:
- Decision link: DEC-... or N/A
```
