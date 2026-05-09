# 小说写作引擎 v4.0

> 为写好看的故事而设计，不是为填表而设计。

---

## 设计原则

1. **故事好看是唯一目标** — 不是流程正确、不是文件齐全
2. **最少文件，最高信号** — 每个文件都有明确用途，没有冗余
3. **给 AI 自由空间** — 指引方向，不限制即兴发挥
4. **态度 > 技巧** — 有观点、有偏见、有情绪的文章才有味道

---

## 文件结构

```
novel/
├── engine.md              ← 本文件（总纲）
├── system.md              ← 故事框架（金字塔结构）
├── config.md              ← 可调参数
├── naming.md              ← 命名规范
├── story-state.md         ← 唯一的状态追踪文件
├── worldview/             ← 世界观设定
├── plot/                  ← 情节大纲（卷→幕→节拍）
├── characters/            ← 角色档案
├── writing/
│   ├── guide.md           ← 写作指南（核心）
│   └── critic.md          ← 自审清单
├── chapters/              ← 正文
└── template/              ← 冷启动模板
```

**已删除的文件：**
- ~~persistent/dashboard.md~~ → 合并入 story-state.md
- ~~persistent/monitor.md~~ → 合并入 story-state.md
- ~~persistent/reader-journey.md~~ → 合并入 story-state.md
- ~~persistent/index.md~~ → 不需要全局索引
- ~~persistent/timeline.md~~ → 合并入 story-state.md
- ~~writing/update-checklist.md~~ → 流程太重，砍掉
- ~~writing/quality.md~~ → 合并入 critic.md
- ~~writing/revision.md~~ → 简化，不需要单独文件

---

## 写一章的流程

### 写之前（2分钟）

1. 读 `story-state.md` — 知道"现在到哪了"
2. 读最近 1 章原文 — 知道"上一章什么感觉"
3. 看大纲里这一段的节拍方向 — 知道"这章该往哪走"

### 写

- 按方向写，不用管"有没有按场景-续接模型"
- 允许即兴发挥 — 好东西常常是写到一半冒出来的
- 不追求完美 — 初稿的任务是"有故事"，不是"好故事"

### 写完（2分钟）

1. 更新 `story-state.md`
2. 完了

---

## 模块协作（简化版）

```
大纲（方向）
  ↓
story-state.md（当前状态）
  ↓
写作指南（怎么写好看）
  ↓
正文
  ↓
自审（快速检查）
  ↓
更新 story-state.md
```

没有仪表盘、没有监控、没有读者旅程、没有全局索引。
**只有三件事：知道方向、写好故事、记住发生了什么。**

---

*版本：v4.0*
