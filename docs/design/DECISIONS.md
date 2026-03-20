---
date: 2026-03-20
description: 细节选型登记 — 每个技术决策的理由与待考察边界
status: active
---

# Design Decisions

每个选型都登记 decision / rationale / boundary，方便后续复审和社区讨论。

## D01: CLI 框架 — typer

- **Decision**: 用 `typer`
- **Rationale**: type-hint 驱动的参数声明，自动生成 `--help`，自动补全。比 click 更符合现代 Python 风格。typer 底层仍是 click，稳定性有保证。
- **Boundary**: typer 在 Python 3.9 下不能用 `from __future__ import annotations`（运行时需检查类型注解），cli.py 必须显式写 `Optional[str]`。如果后续提升到 3.10+ 可以简化。

## D02: YAML+Markdown 解析 — python-frontmatter

- **Decision**: 用 `python-frontmatter` 库，task schema 含 `description` 字段
- **Rationale**: 标准库干标准事。`description` 提供一行式任务摘要，区别于 `title`（名称）和 body（详细笔记）。
- **Boundary**: 不保留 YAML 注释（底层用 PyYAML）。如果用户手写注释被吞掉会不会引发抱怨？`ruamel.yaml` 可以保留注释但引入更重的依赖。

## D03: 表格输出 — 自写 ASCII + wcwidth CJK 对齐

- **Decision**: 自己画 `│` `─` 表格，用 `wcwidth` 计算 CJK 字符显示宽度
- **Rationale**: 少一个重型依赖（不引入 `rich`），但正确处理中文/日文/韩文双宽字符对齐。
- **Boundary**: 目前是纯 CLI 文本输出，没有可视化看板 UI。如果需要看板视图，可考虑：(a) 生成静态 HTML 看板，(b) 与 Obsidian Kanban 插件兼容，(c) 作为独立 side project 提供 Web UI。board.md 本体不做 GUI。

## D04: 通知后端 — pluggable（ntfy + 飞书）

- **Decision**: 支持多通知后端，通过 `.board.json` 中 `notify_backend` 字段切换。首批支持 ntfy.sh 和飞书 webhook。
- **Rationale**: ntfy.sh 零账号零服务器，适合国际用户。飞书 webhook 是中文开发者生态的主流选择，且免费。两者都只需一个 HTTP POST。
- **Boundary**: 飞书 webhook 不支持定时投递（`delay` 参数仅 ntfy 有效）。后续可扩展 Telegram、Discord、Apprise。新增后端只需在 `notify.py` 加一个 `_send_xxx()` 函数。

## D05: 任务 ID — 8 位零填充自增 + 前缀匹配

- **Decision**: `00000001`, `00000002`, ... 上限 99,999,999。支持前缀/简写：`board show 1` 自动解析为 `00000001`。
- **Rationale**: 8 位足够任何规模。前缀匹配让日常使用仍然简短。如果前缀有歧义则报错提示。
- **Boundary**: 前缀歧义在任务量大时会增多（`board show 1` 可能匹配 `10000000` 到 `19999999`）。实际上由于是自增的，只有在有 1 万+ 任务时才会出现，个人看板不太可能。

## D06: 文件名 slug — python-slugify + 可选自定义

- **Decision**: 用 `python-slugify`（`allow_unicode=True`）自动生成 slug，同时支持 `--slug` 手动指定。AI agent 也可通过 AGENTS.md 规则直接提供 slug。
- **Rationale**: python-slugify 是成熟的第三方库（10k+ stars），处理特殊字符、CJK 保留、截断等边界情况。不自己造轮子。
- **Boundary**: `allow_unicode=True` 在 Windows 旧版 cmd 可能显示乱码。跨平台场景下可考虑 `allow_unicode=False`（转写为 ASCII），但会丢失中文可读性。

## D07: current_task — 双写（frontmatter + body section）

- **Decision**: `current_task` 同时写入 frontmatter（数据查询用）和 body 的 `## Current Task` section（人类阅读用）。更新时用 `_update_body_section()` 精准替换目标 section，保留其他 section（如 `## Notes`）。
- **Rationale**: frontmatter 保证 CLI 查询的可靠性，body section 保证用 Obsidian/VS Code 打开文件时直接可读。两者一致性由 `update_task()` 函数维护。
- **Boundary**: 如果用户手动编辑了 body 中的 `## Current Task` section 但没改 frontmatter，两者会不一致。frontmatter 始终是 source of truth，body 是展示层。AGENTS.md 中需明确这一约定。

## D08: Python 版本 — >=3.9

- **Decision**: 支持 Python 3.9+，不要求用户安装新版 Python
- **Rationale**: 降低上手摩擦。macOS 自带 Python 3.9，大量 Linux 发行版默认也是 3.9。`from __future__ import annotations` 兜住类型语法（但 cli.py 因 typer 运行时检查不能用）。
- **Boundary**: 3.9 已 EOL（2025-10），安全更新已停。长期可能需要提到 3.10+。但作为轻量 CLI 工具，安全面小，可接受。

## D09: 异常处理 — 精确 catch + logging.debug

- **Decision**: catch 具体异常类型（`URLError`, `HTTPError`, `OSError`, `ConnectionError`, `json.JSONDecodeError`），用 `logging.debug` 记录原始错误。
- **Rationale**: 不吞掉非网络类 bug（如 TypeError），同时保证通知失败不会 crash CLI。开发者可通过 `PYTHONLOGLEVEL=DEBUG` 看到详细错误。
- **Boundary**: 普通用户看不到 debug 日志。如果通知静默失败且用户不知道原因，可能困惑。后续可在 CLI 加 `--verbose` flag。

## D10: 不做 MCP

- **Decision**: 不提供 MCP server，只提供 CLI
- **Rationale**: 2026 社区基准测试显示 CLI 比 MCP 省 35x token，任务完成率高 28%。CLI 是任何 AI agent（Claude Code、Codex、Cursor、Gemini CLI）的通用接口——能调 bash 就能用。
- **Boundary**: MCP 在 OAuth/多用户权限场景有真实价值。如果 board.md 未来需要团队协作（共享看板 + 权限控制），纯 CLI 就不够了。但这违反 zen philosophy（不做服务端），所以大概率永远不做。
