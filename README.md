# YA

YA 是一个 Linux-first 的个人全量 agent，用于日常助手、个人项目开发、multi-agent 协作、长期记忆、RAG 与工具调用。

> 当前状态：v0.3 Extensibility + Root Control 已完成。161 测试通过。

## 目标

YA 将提供：

- 可流式输出、可调用工具、可保持多轮上下文的 agent loop。
- 面向个人项目开发的 Planner、Coding、Review、Test、Document 与 Coordinator 协作流程。
- 受 capability/scope/confirmation 约束的 Root Agent、Session Agent 和 Project Team。
- CLI、TUI 和 FastAPI Web UI。
- Markdown/Obsidian-compatible 记忆与 GitHub 同步。
- 文档解析、RAG、向量检索、MCP、Skill、自定义工具和 cron-like scheduler。
- Linux 本地运行，以及从 Windows 通过 SSH 安全访问 Web UI。

当前版本边界见 [docs/ROADMAP.md](docs/ROADMAP.md)。v0.1 只实现最小可运行闭环，不包含全部目标能力。

## 设计原则

- Linux-first，默认本地运行。
- 先建立稳定边界，再逐步增加 provider、界面和集成。
- 所有外部服务通过 adapter 接入，业务代码不直接依赖供应商细节。
- 每个 coding agent 一次只处理一个任务包。
- 计划与实现不一致时记录偏差，不通过修改叙述掩盖差异。
- 危险工具、外部 MCP server 和社区 Skill 默认不受信任。
- Web UI 默认只监听 `127.0.0.1`，不直接暴露到公网。

## 计划中的安装与运行

以下命令是 v0.1 已实现的接口：

```bash
git clone https://github.com/peckerpro/opencode-YA.git
cd YA
uv sync --dev
cp .env.example .env
uv run ya doctor
uv run ya chat
```

已实现的命令：

```text
ya chat          # 交互式对话（需 MiniMax API key）
ya run           # 单次非交互执行
ya doctor        # 环境/配置诊断
ya tools list    # 已注册工具列表
ya serve         # 启动 Web 服务 (127.0.0.1:8000)
ya cron list     # 定时任务管理
ya cron add      # 添加定时任务
```

以下命令计划在 v0.3+ 实现：

```text
ya mcp ...
ya memory ...
ya rag ...
ya skill ...
ya root ...
```

```text
ya chat
ya run
ya doctor
ya tools list
ya mcp ...
ya memory ...
ya rag ...
ya serve
ya task ...
ya skill ...
ya cron ...
ya root ...
```

未实现的命令不得伪装为可用功能。CLI 应明确返回“当前版本未实现”及对应 roadmap 版本。

## 配置与密钥

- 所有文本、源代码和配置默认使用 UTF-8。
- Python 文件读写必须显式指定 `encoding="utf-8"`。
- MiniMax、MinerU、GitHub 等密钥只允许通过环境变量、`.env` 或后续安全配置后端提供。
- `.env` 必须被 Git 忽略；仓库只提交不含真实密钥的 `.env.example`。

建议的环境变量名称：

```dotenv
YA_HOME=~/.ya
YA_LLM_PROVIDER=minimax
YA_LLM_MODEL=MiniMax-M3
MINIMAX_API_KEY=
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
MINERU_API_KEY=
GITHUB_TOKEN=
```

变量名称属于初始设计，实施时如有调整，必须记录到对齐报告；影响公共配置契约时还需更新 `DECISIONS.md`。

## 文档导航

| 文档 | 用途 |
|---|---|
| [docs/VISION.md](docs/VISION.md) | 目标用户、场景、目标与非目标 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 模块边界、数据流、目录职责与扩展点 |
| [docs/ROADMAP.md](docs/ROADMAP.md) | v0.1-v0.5 版本范围 |
| [docs/SECURITY.md](docs/SECURITY.md) | secret、权限、外部集成和网络安全 |
| [docs/MEMORY.md](docs/MEMORY.md) | Markdown memory、Git sync 与检索 |
| [docs/MCP_AND_SKILLS.md](docs/MCP_AND_SKILLS.md) | MCP 与 Skill 信任边界 |
| [docs/SCHEDULER.md](docs/SCHEDULER.md) | cron job、执行器、重试和安全 |
| [docs/AGENT_ROLES_AND_PERMISSIONS.md](docs/AGENT_ROLES_AND_PERMISSIONS.md) | Root/Session/Project role、session 与权限审计 |
| [docs/MULTI_AGENT_WORKFLOW.md](docs/MULTI_AGENT_WORKFLOW.md) | 角色、任务状态和交接流程 |
| [plans/v0.1.md](plans/v0.1.md) | v0.1 任务包与验收标准 |
| [plans/v0.2.md](plans/v0.2.md) | v0.2 memory/RAG/Web/scheduler 计划 |
| [plans/v0.3.md](plans/v0.3.md) | v0.3 MCP/Skill/TUI/scheduler integration 计划 |
| [plans/v0.4.md](plans/v0.4.md) | v0.4 project team、permission 与 audit 计划 |
| [TASK_BOARD.md](TASK_BOARD.md) | YA 仓库开发任务和 owner |
| [WHITEBOARD.md](WHITEBOARD.md) | YA 仓库开发假设和跨 agent 信息 |
| [AGENTS.md](AGENTS.md) | multi-agent 工作规则 |
| [DECISIONS.md](DECISIONS.md) | 架构决策和重大偏差 |
| [CHANGELOG.md](CHANGELOG.md) | 已完成、可验证的产品变化 |
| [reports/ALIGNMENT_TEMPLATE.md](reports/ALIGNMENT_TEMPLATE.md) | 阶段对齐报告模板 |
| [reports/STAGE_REPORT_TEMPLATE.md](reports/STAGE_REPORT_TEMPLATE.md) | Coding/Review/Test/Document 阶段报告模板 |
| [docs/SSH_WEB_UI.md](docs/SSH_WEB_UI.md) | Linux Web UI 与 Windows SSH 访问 |

## 推荐目录结构

目录随任务逐步创建，不为未来功能预先生成空模块：

```text
YA/
  README.md
  TASK_BOARD.md
  WHITEBOARD.md
  DECISIONS.md
  CHANGELOG.md
  AGENTS.md
  plans/
    v0.1.md
    v0.2.md
    v0.3.md
    v0.4.md
  reports/
    ALIGNMENT_TEMPLATE.md
    STAGE_REPORT_TEMPLATE.md
    <milestone>-alignment.md
  docs/
    VISION.md
    ARCHITECTURE.md
    ROADMAP.md
    SSH_WEB_UI.md
    SECURITY.md
    MEMORY.md
    MCP_AND_SKILLS.md
    SCHEDULER.md
    AGENT_ROLES_AND_PERMISSIONS.md
    MULTI_AGENT_WORKFLOW.md
  src/ya/
    domain/
    application/
    ports/
    adapters/
    tools/
    skills/
    scheduler/
    permissions/
    interfaces/
    config/
    observability/
  tests/
    unit/
    integration/
    fixtures/
  .ya/
    workspace/                # multi-agent 运行时共享文件
      README.md
      TASK_BOARD.md
      WHITEBOARD.md
      TODO.project.md
      TODO.agent.md
      reports/
    memory/                   # Markdown memory 运行数据
    rag/                      # 解析产物与可重建索引
    logs/                     # 运行、工具、cron 和 audit 日志
      audit/
    cron/                     # scheduler 状态、job store 和 run metadata
    tmp/                      # 可清理临时文件
```

根目录、`docs/`、`plans/`、`reports/` 是项目源码文档；`.ya/workspace/` 是运行时协作状态；`.ya/memory/`、`.ya/rag/`、`.ya/logs/`、`.ya/cron/`、`.ya/tmp/` 是运行数据。长期个人数据也可放在 `~/.ya/`。具体边界见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。

仓库可提交 `.ya/workspace/` 中的空白模板，但生成的事件、lock、日志、数据库、索引、个人记忆和临时文件默认不得提交。任何 cron job 只引用 secret 名称，不保存 token 明文。

## 文档维护顺序

1. Document Agent 维护 Vision、Architecture 与 Roadmap。
2. Planner 从版本计划创建或细化任务包，并更新 Task Board。
3. Coding Agent 只领取一个 Ready 任务。
4. Review Agent 检查代码质量、任务边界和文档一致性。
5. Test Agent 按任务验收标准验证并记录证据。
6. Document Agent 生成 alignment report，按需更新 Decisions 和 Changelog。

## 参考

YA 可借鉴但不复制以下项目和接口：

- Hermes Agent: <https://github.com/NousResearch/hermes-agent>
- MiniMax OpenAI SDK 接入文档: <https://platform.minimaxi.com/docs/api-reference/text-openai-api>
- MiniMax Chat Completions 文档: <https://platform.minimaxi.com/docs/api-reference/text-chat-openai>
