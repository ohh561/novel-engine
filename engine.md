# 小说写作引擎 v5.0

> 动态、有状态、多 Agent 写作系统。

---

## 设计原则

1. **状态驱动** — 不再每次塞入整本书，而是动态查询状态数据库
2. **三 Agent 循环** — Writer 写、Critic 改、Archivist 记，自动优化
3. **最少 token，最高信号** — 上下文 ≤8k，精准打击
4. **故事好看是唯一目标** — 所有架构为这一件事服务

---

## 文件结构

```
novel/
├── engine.md              ← 本文件（总纲）
├── orchestration.md       ← 三 Agent 循环逻辑
├── context_builder.md     ← 动态上下文组装器
├── system.md              ← 故事框架（金字塔结构）
├── config.md              ← 可调参数
├── naming.md              ← 命名规范
│
├── state_db/              ← 结构化状态数据库
│   ├── world_lore.json    ← 静态世界观（极少变动）
│   ├── characters.json    ← 动态角色注册表（每章更新）
│   └── plot_timeline.json ← 滚动叙事记忆（每章更新）
│
├── agents/                ← Agent 系统提示
│   ├── writer.md          ← Writer：写故事
│   ├── critic.md          ← Critic：审故事
│   └── archivist.md       ← Archivist：记状态
│
├── worldview/             ← 世界观原始设定（输入 → world_lore.json）
├── plot/                  ← 情节大纲（输入 → orchestration）
├── characters/            ← 角色原始档案（输入 → characters.json）
├── writing/
│   ├── guide.md           ← 写作指南
│   └── critic.md          ← 自审清单（人类用）
├── chapters/              ← 正文（输出）
├── summary/               ← 章节摘要（输出）
└── template/              ← 冷启动模板
```

---

## 写一章的流程

### 旧方案 vs 新方案

| | 旧方案 (v4.0) | 新方案 (v5.0) |
|---|---|---|
| 上下文 | 读所有设定文件 + 前几章原文 | 动态查询 state_db，≤8k tokens |
| 写作 | 一次性写完 | Writer → Critic → 修改循环 |
| 状态更新 | 手动更新 story-state.md | Archivist 自动提取变更 |
| token 消耗 | ~100k+ | ~8k |
| 质量保证 | 人工自审 | 自动 Critic 评审 |

### 新流程

```
1. 读大纲 → 确定写哪章
2. Context Builder → 组装 ≤8k 上下文包
3. Writer → 生成初稿
4. Critic → 评审 → score < 8? → Writer 修改 → 再评
5. score ≥ 8 → 定稿
6. Archivist → 提取状态变更 → 更新 state_db
7. 保存正文和摘要
```

详见 `orchestration.md`。

---

## 状态管理

### state_db/ — 结构化状态数据库

| 文件 | 内容 | 更新频率 |
|------|------|---------|
| world_lore.json | 静态世界观规则 | 极少变动 |
| characters.json | 角色状态、目标、关系 | 每章更新 |
| plot_timeline.json | 全局摘要 + 最近3章 + 伏笔 | 每章更新 |

**为什么用 JSON 而不是 Markdown？**
- 可以精确查询（"只拉林晨的卡片"）
- 可以结构化更新（"修改林晨的 location"）
- 不会越写越长（Markdown 文件会膨胀）

### 状态来源

```
worldview/master.md → 解析 → world_lore.json
characters/*.md     → 解析 → characters.json
story-state.md      → 迁移 → plot_timeline.json
```

---

## Agent 系统

### Writer（写作 Agent）

- 输入：上下文包 + 章节大纲
- 输出：3000-5000 字正文
- 核心指令：Show Don't Tell、感官优先、角色一致性、节奏变化、闲笔、态度

### Critic（评审 Agent）

- 输入：章节大纲 + 初稿
- 输出：JSON 评审报告（score + actionable_feedback）
- 核心指令：节奏、对话、角色、情感、去AI味
- 通过阈值：8/10

### Archivist（档案 Agent）

- 输入：定稿 + 当前 state_db
- 输出：JSON 更新指令
- 核心指令：只提取变更，不猜测，保持兼容

详见 `agents/` 目录。

---

## 模块协作

```
世界观（world_lore.json）──┐
角色（characters.json）────┤
叙事记忆（plot_timeline）──┼──→ Context Builder ──→ Writer ──→ Critic
大纲（plot/）──────────────┘         ↑                    │
                                     └────────────────────┘
                                          (score < 8)
                                               │
                                          score ≥ 8
                                               ↓
                                         Archivist ──→ 更新 state_db
                                               ↓
                                         保存 chapters/ + summary/
```

---

## 从旧版迁移

如果你有旧版的 markdown 文件：

1. `worldview/master.md` + `bible/` → 解析为 `state_db/world_lore.json`
2. `characters/protagonist.md` + `cast.md` → 解析为 `state_db/characters.json`
3. `story-state.md` → 解析为 `state_db/plot_timeline.json`

原始 markdown 文件保留作为参考，但系统运行以 JSON 为准。

---

## 系统版本

| 版本 | 说明 |
|------|------|
| v1.0 | 基础框架 |
| v2.0 | 情节优先+灵活分幕 |
| v3.0 | 写作引擎（角色系统+读者旅程+主线监控） |
| v3.1 | 系统优化 |
| v4.0 | 轻量化重构（砍掉冗余追踪） |
| **v5.0** | **动态有状态多Agent系统（state_db + 三Agent循环 + RAG-lite上下文）** |

---

*版本：v5.0*
