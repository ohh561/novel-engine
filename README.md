# 🖊️ Novel Engine — 长篇小说写作引擎 v5.0

一个**动态、有状态、多 Agent** 的长篇小说写作系统。

## 这是什么？

Novel Engine 是一套 AI 驱动的写作引擎，帮你规划、写作、监控一部长篇小说。

**v5.0 核心变化**：从"全量注入"转向"动态查询"——不再每次把整本书塞进 prompt，而是通过结构化状态数据库 + RAG-lite 上下文组装，精准喂给写作 Agent。

## 核心特性

- **三 Agent 循环** — Writer 写 → Critic 审 → Archivist 记，自动优化到合格
- **动态上下文** — Context Builder 按需组装 ≤8k tokens 的精准上下文包
- **结构化状态** — JSON 状态数据库，精确查询，不会越写越乱
- **Token 节省 ~90%** — 从 ~100k 降到 ~8k 每章
- **自审系统** — Critic Agent 自动评审，score < 8 自动返回修改

## 快速开始

```bash
git clone https://github.com/ohh561/novel-engine.git
cd novel-engine
cp -r template/ my-novel/
cd my-novel/
```

## 目录结构

```
novel-engine/
├── engine.md              ← 总纲（架构说明）
├── orchestration.md       ← 三Agent循环逻辑
├── context_builder.md     ← 动态上下文组装器
├── system.md              ← 故事框架（金字塔结构）
├── config.md              ← 可调参数（token预算、Critic阈值等）
├── naming.md              ← 命名规范
│
├── state_db/              ← 状态数据库
│   ├── world_lore.json    ← 静态世界观
│   ├── characters.json    ← 动态角色注册表
│   └── plot_timeline.json ← 滚动叙事记忆
│
├── agents/                ← Agent 系统提示
│   ├── writer.md          ← Writer：写故事
│   ├── critic.md          ← Critic：审故事
│   └── archivist.md       ← Archivist：记状态
│
├── worldview/             ← 世界观设定
├── writing/               ← 写作指南
│   ├── guide.md           ← 怎么去AI味、怎么写情感共鸣
│   ├── critic.md          ← 人工自审清单
│   ├── tutorial.md        ← 从零教程
│   └── annotated-example.md
└── template/              ← 冷启动模板
```

## 写一章的流程

```
1. 读大纲 → 确定写哪章
2. Context Builder → 组装 ≤8k 上下文包
3. Writer → 生成初稿
4. Critic → 评审 → score < 8? → Writer 修改 → 再评（最多3轮）
5. score ≥ 8 → 定稿
6. Archivist → 提取状态变更 → 更新 state_db
7. 保存正文和摘要
```

## 系统版本

| 版本 | 说明 |
|------|------|
| v1.0-v3.1 | 传统框架（全量注入+手动追踪） |
| v4.0 | 轻量化重构 |
| **v5.0** | **动态有状态多Agent系统（state_db + 三Agent循环 + RAG-lite）** |

## 许可证

MIT License

---

*Built with ❤️ for writers who think in systems.*
