# MCP and Skills

## MCP

YA 同时支持：

- 作为 MCP client 接入社区 server。
- 作为 MCP server 暴露允许的 YA 工具。

v0.3 首先支持 stdio transport，HTTP/SSE 后续扩展。

所有 MCP tool 进入统一 `ToolRegistry`，使用相同 schema validation、权限、timeout、日志和 circuit breaker。MCP transport 不得直接执行工具。

调用还必须经过 agent capability/scope guard：

- Session Agent 只能调用 session allowlist。
- Project Agent 只能调用 project/role allowlist。
- Root Agent 的外部 MCP 调用仍按风险确认并审计。
- 跨 session instruction 不会把 source agent 的 MCP 权限传给 target。

外部 server 配置记录：

- ID、来源、版本。
- command/arguments 或 endpoint。
- environment allowlist。
- enabled 状态。
- tool allowlist。
- 权限 profile。

社区 server 默认禁用，不能继承全部宿主环境变量或 secret。

## Skills

Skill 使用 `SKILL.md` 风格：

```text
skills/<skill-name>/
  SKILL.md
  scripts/
  references/
  assets/
```

支持内置、本地和社区来源。操作包括 list、inspect、install、enable、disable 和 remove。

Skill 描述任务方法和上下文注入，不自动获得工具权限。Skill 声明的权限只是请求，实际授权由 policy 决定。

安装社区 Skill 时记录 source、version/commit、content hash、license 和安全审查状态。安装后默认 disabled。

## Scheduler Integration

v0.3 可让 scheduler 调用 allowlisted MCP tool 或使用 Skill 生成 prompt context，但必须满足：

- job 固定 server/tool/skill 版本或记录变更。
- 每次运行重新经过权限检查。
- 外部更新不能自动扩大权限。
- dangerous MCP tool 需要持久授权。
- 失败有有限 retry 和 circuit breaker。

## MCP Server Exposure

YA 作为 server 时只暴露明确 allowlist。内部 tool enabled 不等于可对外暴露。对外 schema、权限和日志是独立配置。

## Security Baseline

- 不默认信任 community hub。
- 不执行未经审查的 install script。
- 不将 secret 注入 Skill 文本。
- 不允许 MCP/Skill 覆盖 system policy。
- tool output 有大小和敏感信息限制。
- 删除/更新外部集成时保留审计记录。
