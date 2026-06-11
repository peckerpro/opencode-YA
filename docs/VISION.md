# YA Vision

## 项目陈述

YA 是一个为单个用户长期使用而设计的 Linux-first 全量 agent。它既是日常助手，也是个人软件项目的执行环境，重点解决现有 coding agent 工具在长期上下文、个人记忆、共享白板、任务流控制和 multi-agent 协作方面的不匹配。

YA 不追求在第一阶段替代所有成熟产品。它优先建立一个可理解、可控制、可审计、可逐步扩展的个人 agent 核心。

## 目标用户

主要用户是项目所有者本人。

设计默认值可以针对单用户、本地优先和可信主机优化，但不能因此忽略：

- 外部工具和内容的不可信性。
- API key 与个人数据的安全。
- 并发 agent 写入冲突。
- 可迁移、可备份和可追踪。

## 核心使用场景

1. 通过 CLI、TUI 或 Web UI 进行连续对话和日常任务处理。
2. 在个人软件项目中拆分任务、编码、review、测试和维护文档。
3. 让多个角色 agent 通过共享任务板、白板和阶段报告协作。
4. 从个人文档、项目资料和历史记忆中检索上下文。
5. 调用内置工具、自定义 Python 工具、MCP 工具和 Skill。
6. 将 Obsidian-compatible Markdown 记忆同步到私有 GitHub 仓库。
7. 在 Linux 主机运行服务，并从 Windows 通过 SSH 安全访问。
8. 通过 cron-like scheduler 定时执行 prompt、同步、检查、索引和报告任务。
9. 通过 Root Agent 查看和协调所有 session、project、team 与系统能力。

## 产品目标

### G1. 完整但可控的 agent 核心

支持 LLM 调用、流式响应、多轮上下文、工具调用、有限步 agent loop，以及可插拔的 ReAct、Plan-and-Execute 和 Reflection 策略。

### G2. 面向工程任务的协作控制

任何 agent 都应能明确回答：

- 当前版本目标是什么。
- 当前任务包是什么。
- 自己可以修改哪些文件。
- 验收标准是什么。
- 下一状态和接收角色是谁。
- 实现与计划是否存在偏差。

### G3. 可积累的个人上下文

长期知识和记忆以人可读 Markdown 保存，兼容 Obsidian 的 frontmatter、tag、wikilink 和目录组织；结构化索引可以重建，不成为唯一事实源。

### G4. 统一扩展面

内置工具、自定义工具、MCP 工具和 Skill 通过清晰边界接入。外部集成不能绕过权限、日志、超时和失败控制。

### G5. 多入口一致体验

CLI、TUI 和 Web UI 共享同一个 application/service 层，不各自复制 agent 逻辑。远程访问默认通过 SSH，不默认开放公网监听。

### G6. 可控的主动执行

Scheduler 支持持久化计划、有限重试、超时和日志，让 YA 可以主动执行日常 review、task board 检查、memory sync、RAG re-index 和报告任务。定时执行不能绕过工具权限，也不能形成 agent 自调用死循环。

### G7. 分层 Agent 管理

Root Agent 提供全局秘书入口，Session Agent 保持当前会话边界，Project Team 在独立 workspace 内按 Planner/Coding/Review/Test/Document/Coordinator 分工。权限以 capability 和 scope 表达，高权限角色也不能绕过确认与审计。

## 成功标准

### v0.1 成功

- 用户能在 Linux 终端配置 MiniMax，获得流式多轮对话。
- 模型能在有限循环内调用一个已注册的安全工具，并继续生成回答。
- 会话可在本地恢复。
- `doctor` 能发现关键配置问题。
- 共享 workspace 与任务状态具备 owner、锁和事件记录规则。
- 全流程可由测试替身在无真实 API key 的环境验证。

### 中期成功

- Web UI、Markdown memory 和项目/个人 RAG 可用。
- cron/interval/calendar job 可持久化运行，并能从 CLI/Web 查看状态和日志。
- Planner、Coder、Reviewer、Tester、Documenter 能通过任务状态机完成可审计交接。
- MCP 与 Skill 可在明确授权下安装和运行。
- Root Agent 能只读理解所有允许 session，并在确认后执行跨 session 管理。

### 长期成功

- 多 agent runtime 能可靠调度角色、限制循环、恢复中断并保留完整证据。
- Project team 和 Root Agent 的所有越权请求被拒绝或进入确认流程。
- 个人记忆、项目知识、工具和界面可以独立演化，而不破坏 agent 核心。

## 非目标

- v0.1 不实现完整 Web UI、TUI、RAG、MCP、Skill Hub、多模态解析或自动 GitHub memory sync。
- v0.1 不实现 Root Agent 或跨 session orchestration。
- 不在早期构建面向多租户的 SaaS、计费系统或公网托管平台。
- 不训练自有基础模型。
- 不保证兼容所有 LLM provider；先稳定 provider protocol，再按需增加 adapter。
- 不让 agent 在无边界、无最大步数、无验收标准的情况下自主无限运行。
- 不让 scheduler 无限重试、无授权执行危险操作或递归创建自触发任务。
- 不默认授予 shell、删除、文件写入、Git push 或外部网络访问权限。
- 不把向量数据库当作记忆的唯一事实源。
- 不盲目复刻 Hermes 的目录、功能数量或运行复杂度。

## 产品原则

1. **控制优先于自治**：每次执行都有任务、owner、范围、预算和终止条件。
2. **人可读优先**：关键计划、决策、记忆和报告使用 Markdown。
3. **事实与投影分离**：机器状态可以使用 SQLite/JSONL，Markdown 是可审阅投影时必须定义同步方向。
4. **安全默认值**：本地绑定、最小权限、显式确认、密钥隔离。
5. **适配器隔离变化**：LLM、parser、embedding、vector store、MCP transport 和 sync backend 均可替换。
6. **先垂直闭环后横向扩张**：每个版本必须产生可运行、可测试的增量。
7. **偏差可见**：实现与计划不同属于工程事实，必须记录和处理。
