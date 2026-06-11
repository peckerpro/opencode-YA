# Scheduler / Cron

## 1. Purpose

Scheduler 让 YA 在无人交互时按计划执行受控任务。它是 application service 的触发器，不是绕过 tool policy、agent limits 或安全确认的后门。

版本边界：

- v0.1：仅保留架构边界，不实现 scheduler。
- v0.2：实现持久化 job/run、调度计算、prompt/安全 tool/本地维护任务、CLI/API、日志、有限重试和超时。
- v0.3：接入 GitHub memory push、RAG re-index、允许的 MCP tool、TUI 和强化权限/熔断。
- v0.5：在独立持久授权下支持 Root Agent/Coordinator 的跨 session 自动编排。

## 2. Capability

用户可：

- 创建、查看、暂停、恢复和删除 job。
- 手动触发一次 job。
- 查看 scheduler 状态、next run、last run 和历史日志。
- 使用 cron expression、interval、daily、weekly、monthly schedule。
- 配置 timeout、有限 retry、timezone、enabled 和 missed-run policy。

目标 CLI：

```bash
ya cron list
ya cron add
ya cron remove <job_id>
ya cron pause <job_id>
ya cron resume <job_id>
ya cron run <job_id>
ya cron logs <job_id>
```

## 3. Module Boundary

```text
src/ya/scheduler/
  models.py
  store.py
  cron.py
  runner.py
  service.py
```

职责：

- `models.py`：`CronJob`、`JobRun`、`Schedule`、`RetryPolicy`、状态枚举。
- `store.py`：job/run 的事务持久化、claim 和恢复。
- `cron.py`：解析 schedule、timezone 和 next occurrence。
- `runner.py`：授权、timeout-bound dispatch、结果归一化和 retry 决策。
- `service.py`：生命周期、tick、due job claim、pause/resume 和 shutdown。

CLI、TUI 和 API 只能调用 scheduler application service，不自行计算 next run 或直接改 store。

## 4. Data Model

### CronJob

```text
id
name
description
job_type
payload
schedule
timezone
enabled
timeout_seconds
retry_policy
permission_profile
credential_refs
max_agent_steps
max_child_run_depth
run_as_role
scope
misfire_policy
created_at
updated_at
next_run_at
version
```

### JobRun

```text
id
job_id
occurrence_key
scheduled_at
started_at
finished_at
status
attempt
trigger: scheduled | manual
agent_run_id
result_summary
error_type
error_message
log_ref
```

状态至少包括：

```text
pending
claimed
running
succeeded
failed
timed_out
cancelled
skipped
blocked
```

`occurrence_key` 由 job ID 和计划触发时间确定，并设置唯一约束，防止服务重启后重复执行同一 occurrence。

## 5. Schedule Model

支持：

- `cron`：标准五字段表达式；若实现选择六字段必须在公共契约中明确。
- `interval`：固定秒/分/小时/日。
- `daily`：本地时间每日执行。
- `weekly`：星期与本地时间。
- `monthly`：月内日期与本地时间。

要求：

- job 明确保存 IANA timezone，例如 `Asia/Shanghai`。
- store 中的 `next_run_at` 使用 UTC。
- daylight saving time 的 missing/duplicate local time 有确定策略和测试。
- 无效日期，例如每月 31 日，采用明确 skip/last-day 策略，不隐式猜测。
- schedule parser 必须有资源限制，拒绝导致高频或计算异常的表达式。

## 6. Job Types

| Job type | v0.2 | v0.3 | Notes |
|---|---|---|---|
| Prompt run | Yes | Yes | 使用有界 agent run |
| Safe registered tool | Yes | Yes | 仍经过 registry/policy |
| Daily review | Yes | Yes | prompt job profile |
| Task board check | Yes | Yes | 只读或受控状态更新 |
| Workspace cleanup | Yes | Yes | 仅允许配置的 tmp/expired artifacts |
| Report generation | Yes | Yes | 输出到指定 reports 目录 |
| Memory sync | Local only | Full | GitHub push 在 v0.3 |
| GitHub memory push | No | Yes | guarded/dangerous |
| RAG re-index | Optional local | Yes | 使用 RAG service |
| External MCP tool | No | Allowlisted | 默认禁用 |
| Shell/delete arbitrary path | No | Explicit policy only | 不提供默认 job type |

payload 必须是 typed/validated 数据，不能把任意 Python import path 或 shell string 当作通用执行协议。

## 7. Execution Lifecycle

```text
calculate due occurrences
  -> atomically claim occurrence
  -> load current job version
  -> resolve permission profile and credential references
  -> validate payload
  -> dispatch application command
  -> enforce timeout/cancellation/run limits
  -> persist terminal run and log reference
  -> calculate next occurrence
  -> retry only when policy permits
```

服务关闭时：

- 停止 claim 新 job。
- 向运行中的任务发出取消。
- 在 grace period 后标记未结束 run 为 interrupted/failed。
- 重启恢复时根据 lease 和 occurrence key 判断重试，不假设成功。

## 8. Retry, Timeout and Misfire

`RetryPolicy`：

```text
max_attempts
backoff: fixed | exponential
initial_delay_seconds
max_delay_seconds
retryable_error_types
```

规则：

- `max_attempts` 必须有有限上限。
- validation、permission denied、invalid credential reference 默认不可重试。
- rate limit、transient network 和明确的 provider temporary error 可以重试。
- 每次 attempt 单独记录。
- timeout 后不立即无限重启。

`misfire_policy`：

- `skip`：跳过错过的 occurrence。
- `run_once`：恢复后只补一次。
- `catch_up_limited`：最多补配置的有限次数。

默认使用 `run_once` 或 `skip`，禁止无上限补跑。

## 9. Safety Model

- scheduler 不继承交互会话中一次性的“允许”。
- 每个 job 绑定持久化 `permission_profile`，只授予必要能力。
- 每个 job 固定 `run_as_role` 和 session/project/global scope；创建者不能让 job 运行成更高权限角色。
- dangerous operation 需要项目所有者明确创建可审计授权。
- Git push、删除、shell、文件写入和外部 MCP 均不是默认权限。
- credential 通过 `credential_refs` 引用环境变量或安全配置 ID；job payload 和日志不保存值。
- prompt、tool output 和外部文档不能修改 job 权限。
- workspace cleanup 只能操作 allowlisted 根目录，并防止 symlink/path traversal。
- scheduler service 使用单实例 lease 或等价机制，避免多个进程重复 claim。

## 10. Loop Prevention

定时 agent 可能调用创建 cron 的工具，因此必须限制：

- `max_child_run_depth`。
- 同一 root run 可创建的 job 数。
- job 创建后的最早触发时间。
- 相同 job/payload 的短期去重窗口。
- scheduler-origin run 默认不能修改自身 schedule。
- v0.2/v0.3 的 scheduled Session/Project Agent 不能执行跨 session Root action。
- scheduled Root Agent action 在 v0.5 前默认禁用；启用后也必须绑定具体 capability、scope、expiry 和审计。
- agent 不能在一次 scheduled run 中同步等待自己创建的 job 完成。

检测到循环时将 run 标记 `blocked`，记录 root run chain，不自动重试。

## 11. Persistence and Files

建议权威 job/run 数据使用 SQLite，`.ya/cron/` 保存：

```text
.ya/cron/
  scheduler.db
  exports/          # 可选 UTF-8 job export，不含 secret
  state/            # lease/checkpoint
```

日志写入 `.ya/logs/cron/` 或统一日志 store；`JobRun.log_ref` 只保存引用。

所有导入/导出配置使用 UTF-8。Python I/O 显式 `encoding="utf-8"`。export 必须经过 secret scanner/redaction。

## 12. Interfaces

CLI `add` 应支持交互参数或配置文件，但配置 schema 必须相同。`remove` 默认要求确认；自动化环境可使用显式 `--yes`。

FastAPI 目标：

```text
GET    /api/cron/status
GET    /api/cron/jobs
POST   /api/cron/jobs
GET    /api/cron/jobs/{job_id}
DELETE /api/cron/jobs/{job_id}
POST   /api/cron/jobs/{job_id}/pause
POST   /api/cron/jobs/{job_id}/resume
POST   /api/cron/jobs/{job_id}/run
GET    /api/cron/jobs/{job_id}/runs
```

TUI/Web UI 显示：

- scheduler running/degraded/stopped。
- enabled/paused job。
- next run、last status、attempt。
- permission profile 和风险标签。
- logs/result summary。

界面不得显示 resolved secret。

## 13. Observability

每个事件包含：

- scheduler instance ID。
- job/run/occurrence/root run ID。
- scheduled/start/finish/next run time。
- attempt、status、duration。
- job type、risk、permission decision。
- error category 和 log reference。

默认日志保留策略需可配置。删除 job 不应立即删除其审计记录；按 retention policy 独立清理。

## 14. Acceptance Baseline

- 服务重启后 job 与 next run 保持。
- pause 后不会 claim 新 occurrence；resume 正确计算下一次时间。
- 并发 scheduler 不能重复执行同一 occurrence。
- retry、timeout、misfire 和 loop limit 有自动测试。
- dangerous job 无授权时失败且有日志。
- UTF-8 名称、prompt、报告路径和 export 不乱码。
- job/config/log 中不存在 token 明文。
