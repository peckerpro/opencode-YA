# Runtime Reports

本目录保存当前 runtime 项目的：

- `<task-id>-coding.md`
- `<task-id>-review.md`
- `<task-id>-test.md`
- `<task-id>-document.md`
- `<milestone>-alignment.md`

优先使用项目根 `reports/STAGE_REPORT_TEMPLATE.md` 和 `reports/ALIGNMENT_TEMPLATE.md`。每个 agent 写独立文件，汇总由指定 merge owner 完成。

报告使用 UTF-8，不包含 secret、完整认证 header 或不必要的敏感 tool output。
每份报告记录 agent、role、owner、session/project/workspace scope 和 permission decision/profile。
