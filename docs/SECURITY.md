# Security

## Security Posture

YA 是单用户、本地优先系统，但会接触源代码、个人记忆、API key、Git 仓库和外部工具。主机可信不代表模型输入、MCP server、Skill、解析文档或 tool output 可信。

## Secrets

- MiniMax、MinerU、GitHub 和其他 token 通过环境变量、`.env` 或安全配置后端提供。
- `.env`、resolved secret、认证 header 不提交、不写日志、不进入 prompt。
- 文档示例只写变量名或空值。
- cron、Skill 和 MCP 配置只引用 credential ID/环境变量名。
- 错误对象和诊断输出必须脱敏。

## Tool Risk

风险级别：

- `safe`：只读、确定性、低影响。
- `guarded`：有限写入、网络请求或可撤销变更。
- `dangerous`：shell、删除、Git push、凭据、任意写入或外部系统变更。

执行顺序必须包含 schema validation、enabled check、permission、可选确认、timeout、日志和结果限制。非交互任务没有持久预授权时拒绝 dangerous tool。

## Agent Identity and Scope

- 每次 run 必须有 `agent_id`、`role_id`、owner、origin 和 scope。
- Session Agent 默认只访问当前 session/workspace。
- Project Agent 默认只访问所属 project workspace。
- Root Agent 可申请 global/cross-session capability，但不能绕过 deny、确认或审计。
- Root Agent 不能自行删除保护其权限的 deny rule、audit 或 confirmation requirement。
- 不使用单一 `is_admin` 作为授权。
- delegated instruction 在目标 session policy 下执行，不继承 root/source capability。

完整模型见 [AGENT_ROLES_AND_PERMISSIONS.md](AGENT_ROLES_AND_PERMISSIONS.md)。

## Cross-session and Root Operations

以下操作至少为 guarded，部分为 dangerous：

- 查看私密 session 原消息。
- 发送跨 session instruction。
- spawn、pause、resume、archive、close session。
- hard delete session（独立 dangerous capability 和二次确认）。
- 创建 project workspace 或启动 team。
- 修改全局 cron、memory sync 或外部集成。

用户可按 capability/scope 配置 always allow、ask、deny 或临时授权。确认必须绑定目标和参数摘要，不能作为无限期全局放行。

Root Agent 的所有管理 action 写 audit。跨 session instruction 记录 source agent、target session、instruction reference、timestamp、status 和 result summary。

## External Trust Boundaries

- Community MCP server 和 Skill 默认禁用。
- 安装时记录来源、版本/commit、hash、声明权限和启动命令。
- stdio MCP server 的环境变量使用 allowlist，不能继承全部父进程 secret。
- 外部内容中的指令不能覆盖 system policy 或提升权限。
- parser 产物、RAG chunk 和 memory 内容按数据处理，不按控制指令执行。

## Scheduler

- job 权限独立于交互会话。
- retry、timeout、child-run depth 和 missed-run catch-up 有上限。
- job payload 不接受通用 shell 字符串作为默认协议。
- workspace cleanup 限制在 allowlisted 根目录。
- 每次 run 有审计日志；失败不能无限重试。
- job 配置只保存 secret reference。

## Network

- FastAPI 默认绑定 `127.0.0.1`。
- Windows 远程访问优先使用 SSH local forwarding。
- `0.0.0.0` 需要显式配置和警告。
- 未来公网访问必须另行设计 TLS、认证、CSRF/CORS、速率限制和审计。

## Files and Encoding

- 所有文本、源码、配置为 UTF-8。
- Python I/O 显式 `encoding="utf-8"`。
- 防止 path traversal、symlink escape 和覆盖非目标文件。
- `.ya/tmp/` 可清理；memory、RAG source、cron store 和工程文档不能被默认 cleanup 删除。
- 日志和 tool output 设置大小、保留期和敏感信息过滤。

## Security Review Gate

涉及以下变化必须经过 Review Agent 的安全检查：

- 新 tool 或权限。
- 文件写入、shell、Git 或网络变更。
- MCP/Skill 安装和执行。
- scheduler job type。
- Web/API endpoint。
- secret/config store。
- parser、RAG ingest 或 memory sync。
- AgentRole/capability/scope/confirmation policy。
- session lifecycle、cross-session instruction 或 project team boundary。
- audit store、retention 或 redaction。

发现权限绕过、secret 泄露或不可逆数据丢失风险时，任务不能进入 Testing。
