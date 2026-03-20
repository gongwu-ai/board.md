---
date: 2026-03-20
description: board.md 立项调研 — 知识管理工具全景、通知方案对比、agent 注入标准
status: active
---

# board.md 立项调研

## 调研背景

从 Notion Board 多项目管理看板规划出发，调研了现有开源工具生态，最终决定自建轻量 CLI 工具。

## 关键发现

### 1. 现有工具的空位

生态中存在一个明确空位：**markdown-native 项目看板 CLI，为 AI agent 时代设计**。

- 重型工具（AppFlowy 68k stars, AFFiNE 62k, Plane 46k）都在做 Notion/Jira 替代品 — 红海
- 轻型 CLI（Taskwarrior, todo.txt, ai-todo）不够结构化或已转 SQLite
- Obsidian 做知识管理好用，做任务管理"插件依赖 + 脆弱"（Projects 插件 2025-05 停更）

### 2. 死法图鉴（不做清单的依据）

| 死法 | 案例 | 教训 |
|------|------|------|
| 作者不用了 | Obsidian Projects 插件 | 寄生生态位，动力耦合于宿主 |
| 没找到 PMF | Dendron | VC 驱动 → 停更 |
| 平台方放弃 | Focalboard (Mattermost) | 大公司副产品 |
| 范围膨胀 | Kanboard, WeKan | 功能堆砌，solo 维护不动 |
| 格式迁移 | Logseq md→SQLite | 数据格式是社会契约 |

### 3. 通知方案对比

| 方案 | 成本 | 设置时间 | 手机推送 | 需服务器 |
|------|------|---------|---------|---------|
| **ntfy.sh** | 免费 | 1 分钟 | Yes | No |
| Telegram bot | 免费 | 5 分钟 | Yes | No |
| Discord webhook | 免费 | 3 分钟 | Yes | No |
| 飞书 bot | 免费* | 10 分钟 | Yes | No |
| Resend email（现有方案） | 免费* | 已搭建 | Yes | Yes（腾讯云 cron） |

**结论：ntfy.sh** — 零账号、内置定时、任何机器一行 curl。

### 4. Agent 注入标准

- **AGENTS.md** 是 Linux Foundation 下的跨工具标准（Codex, Cursor, Copilot, Gemini CLI 支持）
- Claude Code 尚未原生支持，symlink AGENTS.md → CLAUDE.md 即可
- **CLI > MCP**：35x 省 token，28% 更高任务完成率（ScaleKit 基准测试）
- 设计原则：`noun verb` 结构、`--json` 输出、`--help` 自文档、`--yes` 非交互

### 5. 社区评价：Obsidian vs Notion

- Notion：涨价趋势 + 锁定风险 + 无端到端加密，solo 开发者社区不推荐
- Obsidian：知识管理强，任务管理弱，插件生态脆弱
- 2026 共识：Obsidian + Claude Code 做笔记，专门工具做任务——两者分离

## 定位

board.md = 那个"专门工具"，但不做重型 PM 系统。
一个 CLI + 一个文件格式规范。数据是 markdown，永不变。

## 调研来源

7 路 Opus agent 并行调研，覆盖：
- Notion API 能力与官方 Claude Code 插件
- Obsidian 插件生态与 MCP server
- Linear / GitHub Projects / Todoist / Taskwarrior 等替代方案
- Obsidian vs Notion 社区真实评价（Reddit, HN, 博客）
- Obsidian 长期使用开发者反馈
- 开源知识管理工具全景（30+ 工具状态）
- 通知方案（ntfy, Telegram, 飞书, Discord 等 10 种）
- Harness-agnostic agent skill 注入标准（AGENTS.md, OpenSpec）
