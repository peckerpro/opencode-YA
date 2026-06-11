# Memory

## Goals

YA 以 Markdown 保存长期记忆，兼容 Obsidian，并支持人类直接阅读、Git 同步和索引重建。

## Storage Boundary

```text
.ya/memory/ or ~/.ya/memory/
  daily/YYYY/MM/YYYY-MM-DD.md
  projects/<project>/index.md
  topics/<topic>.md
  episodes/<year>/<id>.md
```

Markdown 是长期记忆事实源。SQLite 可保存运行 metadata，vector index 是可重建投影。

## Format

```yaml
---
id: mem-...
title: ...
created_at: 2026-06-11T00:00:00Z
updated_at: 2026-06-11T00:00:00Z
type: semantic
tags: [ya, project]
projects: [YA]
source: conversation
---
```

正文支持 tag、`[[wikilink]]`、普通 Markdown 链接和中文。所有文件使用 UTF-8，Python I/O 显式编码。

## Memory Types

- episodic：一次对话、任务或事件的经验。
- task：当前/历史项目任务上下文。
- semantic：稳定事实、偏好和总结。
- daily：按日期记录的日常内容。

写入 memory 前应区分事实、推断和用户偏好；不把未经确认的模型推断写成用户事实。

## Retrieval

检索可以组合：

- frontmatter/filter。
- full-text search。
- backlink/wikilink。
- embedding/vector search。
- recency 和 project/topic ranking。

返回结果必须包含 memory ID、路径和引用片段。索引损坏时可以从 Markdown 重建。

访问按 scope：

- Session Agent 只检索 session policy 允许的 memory namespace。
- Project Agent 默认只访问 project memory。
- Root Agent 可跨 namespace 检索摘要，但私密原文仍受 capability/privacy policy。
- Coding Agent 不能直接写全局 memory；由 Document Agent 提议并经 Root Agent/用户批准。

## GitHub Sync

`SyncBackend` 提供 status、pull/rebase、commit、push 和冲突报告。

- token 只从安全配置读取。
- 默认同步到用户明确指定的私有仓库。
- push 属于 guarded/dangerous 操作。
- 冲突不得静默覆盖；保留双方并生成报告。
- scheduler 自动 push 在 v0.3 启用，必须绑定权限 profile。

## Retention and Privacy

- 用户可删除或归档 memory。
- 删除 Markdown 后索引必须同步删除。
- 日志不复制完整敏感 memory。
- RAG/LLM 注入只取必要片段并记录来源。
- memory repo 的 remote、branch 和同步策略由用户配置，不写死。
