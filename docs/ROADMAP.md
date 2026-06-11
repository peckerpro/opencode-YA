# YA Roadmap

版本按可验证的垂直闭环拆分。进入下一版本前，当前版本必须完成 alignment report；未完成项重新评估，不自动滚入。

## 版本总览

| 版本 | 主题 | 可交付结果 |
|---|---|---|
| v0.1 | Local Agent Core | Linux CLI 中可流式多轮对话、调用安全工具、恢复会话并执行受控任务 |
| v0.2 | Knowledge + Web + Scheduler + Root Read | Memory/RAG/Web、cron 核心和只读 Root Overview |
| v0.3 | Extensibility + Root Control | MCP/Skill/TUI、Git sync、session 控制和 project workspace |
| v0.4 | Project Team + Permission/Audit | 完整 project team runtime、角色 capability 和统一审计 |
| v0.5 | Autonomous Coordination + Multimodal | 跨 session 自动编排、root scheduler integration 和多模态扩展 |

## v0.1 - Local Agent Core

### 范围

- Python 项目骨架、配置、日志和诊断。
- provider-neutral LLM port。
- MiniMax OpenAI-compatible adapter，支持 streaming。
- 多轮会话本地持久化。
- 有最大步数和失败边界的基础 agent loop。
- 统一 tool registry、schema 校验、风险分级和一个安全内置工具。
- CLI：`ya chat`、`ya run`、`ya doctor`、`ya tools list`。
- 最小 `ya task` 流程与共享 workspace 约定。
- 基础 Session Agent 身份、当前 session scope 和 capability/guard primitives。
- 单元测试、集成测试和无真实 API 的 fake provider 测试。

### 明确不做

- FastAPI/Web UI、TUI。
- RAG、向量库和 MinerU。
- 正式 memory subsystem 与 GitHub sync。
- MCP、Skill Hub、自定义插件市场。
- 自动 multi-agent 调度。
- Root Agent、跨 session 查看/控制和 project team。
- shell、文件写入、删除和 Git push 等危险工具。

详细计划见 [../plans/v0.1.md](../plans/v0.1.md)。

## v0.2 - Knowledge + Web + Scheduler + Root Read

### 范围

- Obsidian-compatible Markdown memory。
- episodic/task/semantic memory 基础写入和检索。
- MinerU parser adapter 与 markitdown fallback。
- 文档 hash、解析产物、chunk、embedding 和 vector search。
- 项目级与个人级 RAG namespace。
- 检索引用注入 agent context。
- FastAPI application 接口。
- SSE streaming chat。
- 最小 Web UI：chat、tool event、task board、RAG query。
- scheduler core：持久化 job/run、cron/interval/daily/weekly/monthly。
- CLI：`ya cron list/add/remove/pause/resume/run/logs`。
- prompt、安全 tool、daily review、task board check、workspace cleanup 和 report job。
- scheduler 状态与 run logs 的 FastAPI/Web UI 管理入口。
- 有限重试、timeout、occurrence 去重和自调用深度限制。
- Session registry 和 Root Agent 只读 overview。
- `ya root sessions/inspect/summarize/summarize-all/search`。
- Web UI/TUI-ready session overview API；跨 session 读取按 privacy/scope 过滤。
- Root Overview 显示 active agents、memory、RAG、scheduler 和 Tool Registry 的只读状态。
- 只读 audit 查询和 root read action 审计。
- SSH 本地端口转发文档和安全默认值验证。

### 发布门槛

- 原始 Markdown memory 可脱离向量索引读取。
- 删除并重建 vector index 后检索仍可恢复。
- Web 服务默认绑定 `127.0.0.1`。
- parser fallback 和 citation 来源可见。
- scheduler 重启后 job 保留，重复 occurrence 不会并发执行。
- cron 配置为 UTF-8，且不含 API key/token 明文。
- Session Agent 不能读取其他 session；Root read 结果经过 scope/privacy filter。

### 不做

- 完整多租户认证。
- 自动 multi-agent runtime。
- 大规模分布式向量服务。
- 完整音视频解析。
- GitHub push、外部 MCP 和危险 tool 的无人值守定时执行。
- Root Agent send/spawn/lifecycle write 和 project team。

详细计划见 [../plans/v0.2.md](../plans/v0.2.md)。

## v0.3 - Extensibility + Root Control

### 范围

- MCP client，首选 stdio transport。
- MCP server，暴露经过 allowlist 的 YA 工具。
- MCP 工具接入统一 registry 与权限管线。
- `SKILL.md` loader、内置/本地 Skill。
- Skill 查询、启用、禁用和受控安装。
- 社区 Skill Hub adapter 与来源审计。
- 用户自定义 Python tool 注册。
- 危险工具确认、运行日志、超时和 circuit breaker。
- TUI：stream、tool event、任务板。
- Markdown memory GitHub commit/pull/push 与冲突报告。
- scheduler 接入 memory sync/GitHub push、RAG re-index 和允许的 MCP tool。
- TUI/Web UI 展示 next run、last result、pause/resume 和 job logs。
- scheduler 权限快照、失败熔断、保留策略和 missed-run 策略完善。
- Root Agent `send/spawn/pause/resume/archive/close`。
- 持久化 `Instruction`、跨 session delivery/result 和确认。
- Project/Workspace 创建和基础 project session。
- Root overview 的 TUI/Web 管理 action。
- Root Overview 增加 MCP server、Skill 和 Git/memory sync 状态。
- CLI 扩展：`ya mcp`、`ya skill`、`ya memory`、`ya rag`。

### 发布门槛

- 未审查社区 MCP/Skill 默认不可执行危险操作。
- MCP server 不能暴露 registry 中未授权工具。
- Git 冲突不静默覆盖。
- TUI 与 Web/CLI 复用 application services。
- 定时危险任务没有明确持久授权时拒绝执行。
- 失败 job 不无限重试，自调用链不能形成死循环。
- Root instruction 不向目标 session 传递 root capability。
- session lifecycle 和 project creation 高危动作均可审计。

详细计划见 [../plans/v0.3.md](../plans/v0.3.md)。

## v0.4 - Project Team Runtime + Permission/Audit

### 范围

- Planner、Coding、Review、Test、Document、Coordinator role profile。
- 完整 `AgentRole`、`Capability`、`Permission`、scope 和 confirmation policy。
- 统一 `PermissionGuard` 与 append-only `AuditLog`。
- Coordinator task dispatcher、claim lease、heartbeat 和恢复。
- 共享 board、whiteboard、handoff、review/test report 自动投影。
- 最大重试/返工次数、重复工作检测和人工升级。
- Plan-and-Execute 与受限 Reflection。
- 长任务 checkpoint、取消和恢复。
- Root Agent 启动/停止 project team，并接收 team summary。
- Project role 的代码、文档、测试、memory 和 workspace 权限隔离。
- 跨 session/project instruction 与危险操作完整审计。

### 发布门槛

- 两个以上 worker 不会同时合法拥有同一任务。
- agent crash 后任务 lease 可回收，历史事件保留。
- Review/Testing 退回次数有上限，不能无限循环。
- 每个阶段自动生成可审阅 alignment report 草稿。
- Session/Project Agent 无法越过授权 scope。
- Root Agent 不能绕过 deny/confirm/audit。
- 每个 task/run 记录 owner、role、scope 和 permission decision。

详细计划见 [../plans/v0.4.md](../plans/v0.4.md)。

## v0.5 - Autonomous Coordination + Multimodal

### 范围

- Root Agent 根据用户 policy 跨 session/project 自动汇总、提醒和分派。
- Scheduler 触发经过持久授权的 root/team orchestration。
- 跨 session instruction queue 的优先级、取消、限流和恢复。
- 全局日报、项目状态报告和注意力建议自动生成。
- 图片、视频、音频和图文混合 parser adapter。
- 多模态内容进入 RAG 的 metadata 与引用模型。
- 更复杂的 policy simulation、approval inbox 和异常升级。
- 可选 session hard-delete/tombstone 流程，使用独立 dangerous capability。

### 发布门槛

- autonomous action 只能使用明确 capability/scope/expiry。
- 定时 root action 不能形成跨 session 自调用循环。
- 用户可查看、撤销和暂停全部自动授权。
- 多模态 parser 失败不会破坏已有文本 ingest。

## 跨版本质量要求

- 所有任务有测试和验收标准。
- 所有文本与代码使用 UTF-8；Python 文件 I/O 显式编码。
- 公共契约变更有迁移说明和 decision 记录。
- 新外部依赖说明用途、license、替代方案和安全影响。
- 每个 agent run/task 记录 owner、role、scope 和 permission decision。
- 跨 session、Root 管理和危险操作具有 append-only audit。
- 真实功能完成并通过验收后才更新 `CHANGELOG.md`。
- 未完成或偏离计划的内容写入 alignment report。
