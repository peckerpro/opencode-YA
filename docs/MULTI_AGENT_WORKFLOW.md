# Multi-agent Workflow

## Agent Levels

- Root Agent：跨 session/project 的全局秘书和管理入口。
- Session Agent：当前 session 内的普通助手。
- Project Multi-Agent Team：绑定单一 project workspace 的角色团队。

Root Agent 负责全局观察和授权后的协调；Project Coordinator 只管理 team 内任务；Session Agent 不默认拥有跨 session 能力。完整 capability/scope 模型见 [AGENT_ROLES_AND_PERMISSIONS.md](AGENT_ROLES_AND_PERMISSIONS.md)。

## Roles

- Planner：拆分任务、维护优先级和依赖。
- Coding：一次实现一个已领取任务。
- Review：检查行为、架构、安全、范围和过度设计。
- Test：独立执行验收与失败路径。
- Document：维护 alignment、decision、changelog 和稳定文档。
- Coordinator：原子 claim、状态流转、lease、恢复和循环限制。

详细执行规范见根 [AGENTS.md](../AGENTS.md)。

## Engineering Files vs Runtime Files

项目源码文档：

```text
docs/
plans/
reports/
TASK_BOARD.md
WHITEBOARD.md
```

runtime 协作状态：

```text
.ya/workspace/
  TASK_BOARD.md
  WHITEBOARD.md
  TODO.project.md
  TODO.agent.md
  reports/
  events.jsonl
  locks/
```

根任务板只管理 YA 仓库开发；runtime 任务板管理 YA 运行时接手的项目。二者不自动双写。

## Task Contract

每个 task package 包含目标、输入、文件范围、实现要求、测试要求、验收标准、非目标和输出交接。Coding Agent 不从模糊 TODO 直接开始编码。

## State Flow

```text
Backlog -> Ready -> In Progress -> Review -> Testing -> Done
                       |             |          |
                       +-----------> Blocked <--+
```

- 一个任务同一时刻一个 owner。
- claim/transition 使用 lock/transaction。
- 状态变化写 append-only event。
- Review/Testing 最多退回两轮，之后升级给 Planner/用户。
- Done 必须有 test evidence 和文档处理结论。

## Shared Files

- `TASK_BOARD.md`：人类可读投影。
- `WHITEBOARD.md`：短期假设和跨 agent 注意事项。
- `TODO.project.md`：未形成任务卡的项目候选。
- `TODO.agent.md`：当前 agent 的短期步骤。
- `reports/`：review、test、stage 和 alignment 报告。

共享汇总文件只有一个 merge owner。其他 agent 写独立报告，禁止无锁覆盖。

## Project Role Boundaries

- Planner 维护 project plan/board，默认不写产品代码。
- Coding 只修改任务允许文件，不能写全局 memory 或跨 project。
- Review 默认只读；小修必须显式授权。
- Test 可写测试/报告并运行 allowlisted 命令；危险 shell 需确认。
- Document 可写 project 文档，不擅自修改产品代码。
- Coordinator 可调度 team agent，但不能执行 Root Agent 的 global/session 管理。

每个 project task 绑定 `project_id`、`workspace_id`、owner、role 和 scope。

## Scheduler and Coordinator

Scheduler 负责按时间触发 task board check、daily review、report 和 cleanup；Coordinator 负责把任务分给角色。二者职责不同：

- Scheduler 不判断任务优先级。
- Coordinator 不自行形成周期。
- scheduled agent run 同样受 owner、max steps、timeout 和权限限制。
- scheduled task board check 默认只报告，不自动将大量 Backlog 全部启动。
- Scheduler 不能代替 Root Agent 获得跨 session 权限；scheduled root action 需要独立持久授权。

## Reporting to Root Agent

Coordinator 向 Root Agent 提供 project/team summary，而不是直接共享全部内部消息。Root Agent 如需 inspect 原始内容，仍需通过对应 privacy/scope policy。

## Stage Closure

阶段结束时：

1. Test Agent 汇总执行证据。
2. Document Agent 使用 `reports/ALIGNMENT_TEMPLATE.md`。
3. 偏差按 Local/Architecture/Scope 分类。
4. Architecture/Scope 偏差进入 `DECISIONS.md`。
5. 真实完成内容进入 `CHANGELOG.md`。
6. 未完成项由 Planner 重新安排，不自动视为下一版承诺。
