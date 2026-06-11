# Alignment Report: <milestone or task>

- Report ID:
- Scope:
- Date (UTC):
- Prepared by:
- Reviewed by:
- Related plan:
- Related tasks:
- Code revision:
- Overall result: Met | Partially Met | Not Met

## 1. Executive Summary

用 3-6 条事实说明：

- 实际交付了什么。
- 没有交付什么。
- 是否可发布/进入下一阶段。
- 最大剩余风险。

## 2. Planned vs Implemented

| Plan item | Status | Implementation evidence | Test evidence | Notes |
|---|---|---|---|---|
| <item> | Met / Partial / Not Met | file/commit/run | report/command | <difference> |

不得只写“完成”。证据应可由另一 agent 重现。

## 3. Acceptance Criteria

| Task ID | Criterion | Result | Evidence | Gap/Follow-up |
|---|---|---|---|---|
| YA-... | <criterion> | Pass / Fail / Not Run | <evidence> | <action> |

## 4. Architecture Alignment

逐项检查：

- [ ] 依赖方向符合 `docs/ARCHITECTURE.md`。
- [ ] provider/adapter 类型未泄漏到 domain/application。
- [ ] 权威存储与投影边界一致。
- [ ] agent loop 有终止条件。
- [ ] tool 权限和风险策略未绕过。
- [ ] 每个 run/task 有 owner、role 和 session/project/workspace scope。
- [ ] Session/Project Agent 没有跨 scope 访问。
- [ ] Root/cross-session action 经过 capability、确认和 audit。
- [ ] delegated instruction 未向目标传递 source/root 高权限。
- [ ] 默认网络监听与安全基线一致。
- [ ] UTF-8 与 secret 规则满足。

说明不适用项和证据：

<text>

## 5. Deviations

| Deviation ID | Planned | Implemented | Reason | Impact | Classification | Decision |
|---|---|---|---|---|---|---|
| DEV-... | ... | ... | ... | ... | Local / Architecture / Scope | DEC-... / N/A |

没有偏差时明确写“None observed”，不要删除本节。

## 6. Quality and Test Results

| Check | Command/environment | Result | Evidence/notes |
|---|---|---|---|
| Unit tests | | | |
| Integration tests | | | |
| Type/lint | | | |
| UTF-8 tests | | | |
| Security/secret scan | | | |
| Manual smoke | | | |

### Tests Not Run

- 测试：
- 原因：
- 风险：
- 后续 owner：

## 7. Security Review

- Secret handling:
- Dangerous tool controls:
- External content trust boundary:
- Network binding:
- Logging/redaction:
- Known risks:

## 8. Documentation Updates

| Document | Updated? | Reason |
|---|---|---|
| `README.md` | Yes/No | |
| `docs/ARCHITECTURE.md` | Yes/No | |
| `docs/ROADMAP.md` / plan | Yes/No | |
| `TASK_BOARD.md` | Yes/No | |
| `WHITEBOARD.md` | Yes/No | |
| `DECISIONS.md` | Yes/No | |
| `CHANGELOG.md` | Yes/No | 仅真实完成内容 |

## 9. Remaining Work

| Item | Target version/task | Priority | Owner | Blocking? |
|---|---|---|---|---|
| | | | | |

## 10. Recommendation

- Release/advance decision: Go | Conditional Go | No-Go
- Conditions:
- Next task/milestone:
- Owner approval:
