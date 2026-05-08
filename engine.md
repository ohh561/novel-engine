# 小说写作引擎 v3.1

> 本系统是一个完整的长篇小说写作引擎，可以独立驱动一部500+章的长篇小说。
> 各模块互相协作，随剧情发展自动丰富，实时监控主线进展。

---

## 引擎架构

```
┌─────────────────────────────────────────────────┐
│                  调度层                           │
│  engine.md + naming.md + index.md               │
└─────────┬───────────────────────────────┬───────┘
          │                               │
    ┌─────▼──────┐                 ┌──────▼──────┐
    │  故事层     │                 │  写作层      │
    │            │                 │             │
    │ worldview   │                 │ guide       │
    │ plot        │◄───────────────►│ critic      │
    │ persistent  │    双向协作     │ update-list │
    │ characters  │                 │             │
    │ reader-journey               │             │
    │ monitor     │                 │             │
    │ dashboard   │                 │             │
    └────────────┘                 └─────────────┘
          │
    ┌─────▼──────┐
    │  模板层     │
    │ template/   │ ← 可复用，新建小说时复制
    └────────────┘
```

## 模块清单

| 模块 | 文件 | 职责 | 状态 |
|------|------|------|------|
| 引擎 | engine.md | 调度、协作规则 | ✅ |
| 命名规范 | naming.md | 统一命名 | ✅ |
| 全局索引 | persistent/index.md | 所有ID注册表 | ✅ |
| 世界观 | worldview/master.md | 顶层规则 | ✅ |
| 情节 | plot/volX/ | 故事梗概+节拍 | ✅ 五卷 |
| 伏笔 | persistent/foreshadow.md | 三级伏笔 | ✅ |
| 时间线 | persistent/timeline.md | 双时间轴 | ✅ |
| 主角 | persistent/characters/protagonist.md | 当前状态+历史 | ✅ |
| 角色库 | persistent/characters/cast.md | 角色画像+关系矩阵 | ✅ |
| 读者旅程 | persistent/reader-journey.md | 情绪+子线+节奏 | ✅ |
| 主线监控 | persistent/monitor.md | 主线进展+预警 | ✅ |
| 仪表盘 | persistent/dashboard.md | 健康检查总览 | ✅ |
| 写作指南 | writing/guide.md | 场景/钩子/去AI味 | ✅ |
| 自审 | writing/critic.md | 逻辑/节奏/人物检查 | ✅ |
| 更新清单 | writing/update-checklist.md | 每章更新+依赖+故障恢复 | ✅ |
| 模板 | template/ | 冷启动模板 | ✅ |

## 数据源规则（解决冗余问题）

| 数据类型 | 主数据源 | 副本 | 同步规则 |
|---------|---------|------|---------|
| 主角当前状态 | protagonist.md 顶部 | dashboard.md | 改主角→同步dashboard |
| 主角历史 | protagonist.md 底部 | 无 | 只在主角档案改 |
| 配角信息 | cast.md | 幕文件节拍 | 改cast→检查幕文件 |
| 伏笔 | foreshadow.md | 幕文件伏笔字段 | 改foreshadow→检查幕文件 |
| 时间线 | timeline.md | 幕文件时间字段 | 改timeline→检查幕文件 |
| 关系 | protagonist关系表+cast关系矩阵 | 无 | 改关系→同步两处 |
| 所有ID | index.md | 各自文件 | 新增ID→必须登记index |

## 写作引擎运行流程

```
1. 生成上下文包
   ├─ 读：当前节拍（plot/volX/actN.md）
   ├─ 读：世界设定（plot/volX/world/）
   ├─ 读：persistent/ 所有文件
   └─ 读：writing/guide.md

2. 写正文
   └─ 按写作指南执行

3. 自审（writing/critic.md）
   └─ 发现问题 → 纠正 → 重新自审

4. 更新文档（按 writing/update-checklist.md 顺序）
   ├─ timeline.md
   ├─ protagonist.md
   ├─ cast.md
   ├─ foreshadow.md
   ├─ index.md
   ├─ monitor.md
   ├─ reader-journey.md
   └─ dashboard.md

5. 主线监控（monitor.md）
   └─ 偏差 → 调整后续节拍

6. 读者旅程检查（reader-journey.md）
   └─ 断线/失衡 → 调整节奏

7. 保存正文
   └─ chapters/vol1-chXXX.md
```

## 模块协作矩阵

| 变化来源 | 必须检查 | 必须更新 |
|---------|---------|---------|
| plot推进 | monitor, reader-journey, foreshadow | timeline, protagonist, dashboard |
| 角色变化 | cast关系, plot后续 | protagonist, cast, dashboard |
| 伏笔回收 | plot节拍 | foreshadow, index, dashboard |
| 时间变化 | plot逻辑 | timeline |
| critic问题 | 所有受影响 | 对应模块 |
| monitor偏离 | plot当前幕 | plot, monitor |
| reader失衡 | plot后续 | plot, reader-journey |

## 自我丰富规则

| 触发事件 | 丰富什么 |
|---------|---------|
| 新角色出场 | cast.md + index.md |
| 角色关系变化 | protagonist关系表 + cast关系矩阵 |
| 新技能 | protagonist技能树 |
| 新物品 | protagonist携带物品 |
| 新伏笔 | foreshadow.md + index.md |
| 子线推进 | reader-journey子线表 |
| 节奏变化 | reader-journey热力图 |
| 主线推进 | monitor节点状态 |

---

*版本：v3.1*
