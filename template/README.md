# 冷启动模板

> 新建小说时，复制整个 `template/` 目录。

## 快速开始

```bash
cp -r template/ my-novel/
cd my-novel/
```

## 需要填写的文件

### 必填

1. `state_db/world_lore.json` — 世界观规则
2. `state_db/characters.json` — 主要角色
3. `state_db/plot_timeline.json` — 初始化为空故事
4. `worldview/master.md` — 世界观圣经（参考，系统以 JSON 为准）
5. `plot/vol1/outline.md` — 第一卷大纲
6. `plot/vol1/act1.md` — 第一幕节拍

### 可选

7. `characters/protagonist.md` — 主角详细档案（参考）
8. `characters/cast.md` — 角色索引（参考）

## 不需要改动的文件

- `engine.md` — 引擎总纲
- `orchestration.md` — 三Agent循环逻辑
- `context_builder.md` — 上下文组装器
- `agents/` — Agent 系统提示
- `writing/` — 写作指南和自审清单
- `config.md` — 配置参数（按需调整）
- `naming.md` — 命名规范
- `system.md` — 故事框架

## 目录结构

```
template/
├── state_db/              ← 填写：状态数据库
│   ├── world_lore.json    ← 世界观规则
│   ├── characters.json    ← 角色注册表
│   └── plot_timeline.json ← 叙事记忆
├── agents/                ← 不改：Agent 系统提示
│   ├── writer.md
│   ├── critic.md
│   └── archivist.md
├── worldview/             ← 填写：世界观设定
│   └── master.md
├── plot/                  ← 填写：情节大纲
│   └── vol1/
│       └── world/
├── characters/            ← 填写：角色档案
├── writing/               ← 不改：写作指南
├── chapters/              ← 输出：正文
└── summary/               ← 输出：章节摘要
```
