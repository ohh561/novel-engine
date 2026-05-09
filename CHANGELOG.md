# Changelog

## v5.0 (2026-05-09)

### 架构重构：动态有状态多Agent系统

**核心变化**：从"全量注入"转向"动态查询"。不再每次把整本书塞进 context，而是通过 JSON 状态数据库按需拉取，精准喂给写作 Agent。

### Added
- `state_db/world_lore.json` — 静态世界观规则（结构化 JSON）
- `state_db/characters.json` — 动态角色注册表（状态、目标、关系、秘密）
- `state_db/plot_timeline.json` — 滚动叙事记忆（全局摘要+最近3章+伏笔）
- `agents/writer.md` — Writer Agent 系统提示（Show Don't Tell、感官优先、节奏变化）
- `agents/critic.md` — Critic Agent 系统提示（5维评审、JSON输出、score阈值）
- `agents/archivist.md` — Archivist Agent 系统提示（状态变更提取）
- `context_builder.md` — 动态上下文组装器（RAG-lite，≤8k tokens）
- `orchestration.md` — 三Agent循环逻辑（Writer→Critic→Archivist）

### Changed
- `engine.md` — 更新为 v5.0 架构总纲
- `config.md` — 新增 Agent 参数（token预算、Critic阈值、循环次数）
- `template/` — 新增 state_db/ 和 agents/ 模板

### Token 效率
- 旧方案：~100k tokens/章（全量注入）
- 新方案：~8k tokens/章（动态构建）
- **节省 ~90%**

## v4.0 (2026-05-09)

### 轻量化重构

砍掉冗余追踪系统（persistent/），聚焦写作质量。

### Removed
- `persistent/` 目录（dashboard/foreshadow/index/monitor/reader-journey/timeline）
- `writing/quality.md`、`writing/revision.md`、`writing/update-checklist.md`

## v3.1 (2026-05-08)

- naming.md, persistent/index.md, persistent/dashboard.md, config.md, template/

## v3.0 (2026-05-08)

- engine.md, persistent/reader-journey.md, persistent/monitor.md, writing/critic.md

## v2.0 (2026-05-08)

- 五卷迁移到新结构，情节优先，灵活分幕

## v1.0 (2026-05-08)

- 初始框架
