---
date: 2026-03-20
description: 细节选型登记 — 每个技术决策的理由与待考察边界
status: active
---

# Design Decisions

每个选型都登记 decision / rationale / boundary，方便后续复审和社区讨论。

## D01: CLI 框架 — click

- **Decision**: 用 `click`，不用 `typer`
- **Rationale**: typer 是 click 的 wrapper，多一层间接 + 多一个依赖，但没带来实际收益。click 更显式，调试更透明。
- **Boundary**: typer 的 type-hint 自动补全确实更优雅。如果未来 CLI 参数变复杂（嵌套子命令、动态选项），可能值得重新评估。

## D02: YAML+Markdown 解析 — python-frontmatter

- **Decision**: 用 `python-frontmatter` 库
- **Rationale**: 这个库就是干"YAML frontmatter + markdown body"这件事的，成熟稳定，API 简洁。
- **Boundary**: 不保留 YAML 注释（底层用 PyYAML）。如果用户手写注释被吞掉会不会引发抱怨？`ruamel.yaml` 可以保留注释但引入更重的依赖。

## D03: 表格输出 — 自写 ASCII

- **Decision**: 自己画 `│` `─` 表格，不依赖 `rich`
- **Rationale**: 少一个依赖 = 安装更轻、攻击面更小。board.md 的表格够简单，不需要颜色/emoji 渲染。
- **Boundary**: 中文字符宽度计算目前用 `len()`，CJK 字符实际占 2 列宽，表格对齐会跑偏。如果中文用户多，需要引入 `wcwidth` 或 `unicodedata.east_asian_width` 修正。

## D04: 通知后端 — ntfy.sh via stdlib urllib

- **Decision**: 只支持 ntfy.sh，用标准库 `urllib` 发 HTTP POST
- **Rationale**: 零额外依赖。ntfy.sh 零账号、零服务器、内置定时（`At` header），一行 curl 等效。
- **Boundary**: ntfy.sh 是单一依赖方。如果 ntfy.sh 挂了或改 API，提醒就断了。后续可能需要 pluggable 后端（Telegram、飞书、Apprise），但现在不做（YAGNI）。

## D05: 任务 ID — 3 位零填充自增

- **Decision**: `001`, `002`, ..., `999`，文件名 `{id}_{slug}.md`
- **Rationale**: 简单、可排序、ls 自然有序、grep 友好。比 UUID 短得多，适合 CLI 手敲。
- **Boundary**: 上限 999 个任务。对个人项目板绰绰有余，但如果有人用来管大项目就不够了。溢出时可以扩到 4 位（`0001`），但需要迁移已有文件名——这违反"不改数据格式"的承诺吗？不算，因为 ID 是文件名约定，不是 frontmatter schema。

## D06: 文件名 slug

- **Decision**: `re.sub` 清洗 + 截断 40 字符
- **Rationale**: 保证文件名合法，同时保留人可读性。
- **Boundary**: 中文标题 slugify 后变成 `训练基线模型`（保留 unicode \w），不做拼音转换。这在 macOS/Linux 上没问题（UTF-8 文件系统），但 Windows 旧版 cmd 可能显示乱码。暂不处理。

## D07: current_task 存储位置 — frontmatter

- **Decision**: `current_task` 作为 frontmatter 字段，不写进 body 的 `## Current Task` section
- **Rationale**: CLI 修改 frontmatter 是原子操作（读-改-写整个文件），修改 body 中的 section 需要做 markdown 解析和 section 定位，脆弱且容易破坏用户手写的内容。
- **Boundary**: AGENTS.md 的 spec 示例里 `## Current Task` 在 body 中。两者有不一致。如果用户期望在 body 里看到 current task（比如用 Obsidian 浏览时），frontmatter 字段不够直观。可能需要在 `show` 命令或文件生成时把 frontmatter 的 `current_task` 渲染到 body。

## D08: Python 版本 — >=3.9

- **Decision**: 支持 Python 3.9+
- **Rationale**: 开发机系统 Python 是 3.9.6，用 `from __future__ import annotations` 兜住类型语法。
- **Boundary**: 3.9 是 2025-10 EOL 的版本。pip 安装时不会报错但安全更新已停。长期应该提到 3.10+，但这会逼用户装 pyenv/nvm 等版本管理器，增加上手摩擦。

## D09: 异常处理 — bare Exception (notify)

- **Decision**: `except Exception` catch 所有异常
- **Rationale**: `urllib` 在不同错误场景下抛不同异常（URLError, HTTPError, OSError, timeout），mock 测试环境抛 `Exception`。catch 宽泛一些保证通知失败不会炸掉整个 CLI。
- **Boundary**: 吞掉了所有异常，包括 bug 导致的 TypeError 等。调试时可能不方便。可以加 `logging.debug` 记录原始异常但不暴露给用户。

## D10: 不做 MCP

- **Decision**: 不提供 MCP server，只提供 CLI
- **Rationale**: 2026 社区基准测试显示 CLI 比 MCP 省 35x token，任务完成率高 28%。CLI 是任何 AI agent（Claude Code、Codex、Cursor、Gemini CLI）的通用接口——能调 bash 就能用。
- **Boundary**: MCP 在 OAuth/多用户权限场景有真实价值。如果 board.md 未来需要团队协作（共享看板 + 权限控制），纯 CLI 就不够了。但这违反 zen philosophy（不做服务端），所以大概率永远不做。
