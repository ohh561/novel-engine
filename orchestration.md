# 编排逻辑 — 三 Agent 循环

> 本文件定义写一章的完整流程。执行者（人类或 AI）按此流程操作。

---

## 总览

```
┌──────────────┐
│  1. 准备      │  读大纲，确定写哪章
└──────┬───────┘
       ↓
┌──────────────┐
│  2. 构建上下文 │  Context Builder 组装 ≤8k 上下文包
└──────┬───────┘
       ↓
┌──────────────┐
│  3. Writer    │  生成初稿
└──────┬───────┘
       ↓
┌──────────────┐
│  4. Critic    │  评估初稿 → score < 8 → 反馈 → Writer 修改
└──────┬───────┘       ↑                        │
       │               └────────────────────────┘
       │               (最多 3 轮)
       ↓
┌──────────────┐
│  5. 定稿      │  score ≥ 8 → 锁定正文
└──────┬───────┘
       ↓
┌──────────────┐
│  6. Archivist │  提取状态变更 → 更新 state_db
└──────┬───────┘
       ↓
┌──────────────┐
│  7. 保存      │  正文 → chapters/，摘要 → summary/
└──────────────┘
```

---

## Step 1: 准备

**输入**：要写的章节号

**操作**：
1. 读 `plot/vol{N}/act{M}.md` — 找到对应节拍
2. 读 `story-state.md`（或查询 `state_db/plot_timeline.json`）— 确认当前位置
3. 确认本章要覆盖哪个节拍

**输出**：章节大纲（节拍描述）

---

## Step 2: 构建上下文

**参考**：`context_builder.md`

**操作**：
1. 解析大纲，提取出场角色和场景地点
2. 查询 `state_db/characters.json` → 拉取出场角色卡片
3. 查询 `state_db/world_lore.json` → 拉取相关世界规则
4. 查询 `state_db/plot_timeline.json` → 拉取最近3章摘要 + 开放伏笔
5. 组装上下文包，控制在 ≤8k tokens

**输出**：context_string

---

## Step 3: Writer 生成初稿

**参考**：`agents/writer.md`

**输入**：
- 上下文包（Step 2 输出）
- 章节大纲（Step 1 输出）

**操作**：
- Writer 按照 writer.md 的指令生成 3000-5000 字初稿

**输出**：draft_text

---

## Step 4: Critic 评审

**参考**：`agents/critic.md`

**输入**：
- 章节大纲
- draft_text

**操作**：
- Critic 按照 critic.md 的指令评估初稿
- 输出 JSON 评审报告

**判断**：
```
if score >= 8:
    → 通过，进入 Step 5
else:
    → 将 actionable_feedback 返回 Writer
    → Writer 根据反馈修改初稿
    → 重新进入 Step 4
    → 最多 3 轮
    → 3 轮后仍未达标：使用最后一次修改的版本，标记为"需人工审核"
```

**输出**：final_text + critique_report

---

## Step 5: 定稿

**操作**：
- 确认 final_text 为最终版本
- 如果 Critic 标记了 ai_flags，快速清理禁用词

**输出**：locked_text

---

## Step 6: Archivist 更新状态

**参考**：`agents/archivist.md`

**输入**：
- locked_text
- 当前 state_db

**操作**：
- Archivist 按照 archivist.md 的指令提取状态变更
- 输出 JSON 更新指令
- 执行者将更新应用到：
  - `state_db/characters.json`
  - `state_db/plot_timeline.json`
  - `state_db/world_lore.json`（如果有世界观变更）

**输出**：更新后的 state_db

---

## Step 7: 保存

**操作**：
1. 正文保存到 `chapters/vol{N}-ch{NNN}.md`
2. 摘要保存到 `summary/vol{N}-ch{NNN}.md`（从 timeline_entry 提取）
3. 更新 `story-state.md`（同步 plot_timeline.json 的关键信息）

---

## 完整伪代码

```python
def generate_chapter(chapter_number):
    # Step 1: 准备
    outline = read_outline(chapter_number)
    
    # Step 2: 构建上下文
    context = build_context(outline, state_db)
    
    # Step 3: Writer 生成初稿
    draft = Writer.generate(context, outline)
    
    # Step 4: Critic 评审循环
    attempts = 0
    while attempts < 3:
        critique = Critic.evaluate(draft, outline)
        if critique.score >= 8:
            break
        draft = Writer.revise(draft, critique.actionable_feedback)
        attempts += 1
    
    # Step 5: 定稿
    final_text = draft
    if critique.score < 8:
        mark_for_human_review(final_text)
    
    # Step 6: Archivist 更新状态
    state_updates = Archivist.extract_changes(final_text, state_db)
    apply_updates(state_db, state_updates)
    
    # Step 7: 保存
    save_chapter(chapter_number, final_text)
    save_summary(chapter_number, state_updates.timeline_entry)
    update_story_state(state_db)
    
    return final_text
```

---

## Token 预算对比

| 方案 | 每章消耗 | 说明 |
|------|---------|------|
| 旧方案（全量注入） | ~100k+ | 把所有设定+历史章节塞进 prompt |
| 新方案（动态构建） | ~8k | 只拉相关角色+最近3章+相关规则 |

**节省 ~90% token 消耗，且上下文更精准。**

---

*版本：v1.0*
