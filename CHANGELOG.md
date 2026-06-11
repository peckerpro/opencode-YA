# Changelog

本文件只记录已经实现、通过验收且对用户或开发者可观察的变化。未来计划、正在进行的工作、仅有设计的功能和未通过测试的实现不得写入。

格式参考 Keep a Changelog，版本遵循项目实际发布标签。

## [Unreleased]

### Added — v0.1.0 (2026-06-11)

- **Project Foundation**: pyproject.toml with hatchling build, pydantic + pydantic-settings config, uv package management (YA-001)
- **Typed Configuration**: Settings with env var override, SecretStr masking, YA_HOME path resolution, Chinese/UTF-8 path support (YA-001)
- **Observability**: Secret-redacting log formatter with configure_logging/get_logger API (YA-001)
- **LLM Provider Port**: Provider-neutral LLMProvider protocol with generate/generate_stream (YA-002)
- **MiniMax Adapter**: OpenAI-compatible streaming adapter with tool call reconstruction, error normalization (auth→401, rate→429, timeout→retryable) (YA-002)
- **Session Persistence**: SQLite store with WAL mode, schema migration v1, full CRUD for sessions/messages/runs/agent-events, Chinese content support (YA-003)
- **Tool Registry**: Unified registry with enable/disable, schema validation, duplicate detection (YA-004)
- **Safety Policy**: safe/guarded/dangerous risk levels, PermissionPolicy with allowlist override, disabled tool rejection (YA-004)
- **Builtin Tool**: UtcTimeTool — deterministic UTC ISO 8601 safe tool (YA-004)
- **Agent Loop**: Bounded ReAct-style loop with max steps, cancellation, timeout, tool call execution, correlation ID tracking (YA-005)
- **Task Workspace**: File-based task store with exclusive locks (O_CREAT|O_EXCL), append-only events.jsonl, state machine (Backlog→Ready→InProgress→Review→Testing→Done→Blocked) (YA-007)
- **CLI**: ya (--help/--version), ya chat, ya run, ya doctor, ya tools — typer + rich interface (YA-006)
- **Testing**: 84 tests (69 unit + 3 integration + 10 CLI + 2 misc), ruff clean, mypy strict mode clean, 82% coverage

### Added — v0.2.0 (2026-06-12)

- **Markdown Memory**: Obsidian-compatible YAML frontmatter, daily/project/topic/episodic paths, full-text search, tag filter, Chinese content, wikilink-ready (V2-001)
- **Document Parser**: TextParser (line-by-line) + MarkdownParser (headings, code blocks, section tracking), UTF-8 safe (V2-002)
- **RAG Pipeline**: Volcengine doubao-embedding adapter, SQLite + numpy cosine vector store, ingest (parse→chunk→embed→store), query with namespace isolation, content hash + source tracking (V2-003)
- **FastAPI**: /health, /api/tools, /api/config, /api/memory, /api/cron, /api/rag/query, /api/root/sessions, /docs (V2-004, V2-008)
- **Web UI**: Single-page console with Chat, Tools, Tasks, RAG, Cron panels, dark theme, vanilla JS (V2-005)
- **Scheduler Core**: CronJob/JobRun models, cron/interval/daily/weekly/monthly schedule calculation, SQLite persistence, occurrence dedup, due job query (V2-006)
- **Scheduler Runner**: Job execution with run records, SchedulerService tick loop, ya cron CLI (list/add/remove/pause/resume/run/logs) (V2-007)
- **Root API**: Session list/inspect/status, memory overview, `ya serve` command (127.0.0.1:8000) (V2-008)
- **Testing**: 129 tests total, 83% coverage, ruff + mypy clean on 57 source files

<!--
真实功能完成后使用以下分类：

### Added
### Changed
### Fixed
### Security
### Removed

每条应包含任务 ID，并能链接到测试或 alignment evidence。
-->

