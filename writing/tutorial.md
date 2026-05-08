# 从零开始：用 Novel Engine 写一部长篇小说

> 本教程带你从零开始，用 Novel Engine 完成一部长篇小说的规划和写作。

---

## Step 1：想清楚你要写什么（30分钟）

在打开任何文件之前，先想清楚：

1. **一句话概括**：你的小说讲什么？
   - 例："一个被选中的普通青年，在高等文明的斗兽场中，从棋子变成掀翻棋盘的人。"

2. **核心主题**：你想探讨什么？
   - 例："自由意志 vs 命运操控"

3. **情绪走向**：读者读完应该有什么感受？
   - 例："从兴奋到沉重到绝望到超越"

4. **大约多长**：计划写多少章？
   - 例："500章左右"

---

## Step 2：搭建世界观（1小时）

填写 `worldview/master.md`：

- 基本设定（时间、地点）
- 核心规则（这个世界最重要的规则是什么）
- 世界结构（几个世界？什么关系？）

---

## Step 3：规划卷结构（1小时）

1. 决定写几卷
2. 每卷写什么故事
3. 每卷的基调是什么

填写 `plot/vol1/outline.md` 到 `plot/volN/outline.md`

---

## Step 4：搭建第一卷的世界（1小时）

填写第一卷的世界设定：
- `plot/vol1/world/geography.md` — 地理、文明、势力
- `plot/vol1/world/power.md` — 力量体系

---

## Step 5：规划第一卷的情节节拍（2小时）

1. 决定第一卷分几幕
2. 每幕有哪些情节节拍
3. 每个节拍的内容、人物、冲突、伏笔、情绪
4. 按吸引力分配章节数

填写 `plot/vol1/act1.md` 到 `plot/vol1/actN.md`

---

## Step 6：创建主角档案（30分钟）

填写 `persistent/characters/protagonist.md`：
- 基础信息
- 性格锚点
- 说话风格
- 成长曲线
- 初始状态

---

## Step 7：创建角色库（30分钟）

填写 `persistent/characters/cast.md`：
- 所有计划出场的角色
- 每个角色的画像
- 关系矩阵

---

## Step 8：规划伏笔（30分钟）

填写 `persistent/foreshadow.md`：
- 全书级伏笔
- 第一卷伏笔

---

## Step 9：初始化监控系统（15分钟）

填写：
- `persistent/monitor.md` — 主线节点
- `persistent/reader-journey.md` — 情绪曲线+子线
- `persistent/dashboard.md` — 仪表盘
- `persistent/index.md` — 登记所有ID

---

## Step 10：开始写第一章！

1. 读 `plot/vol1/act1.md` 找到第一章的节拍
2. 读 `persistent/` 所有文件了解当前状态
3. 读 `writing/guide.md` 了解写作要求
4. 按 `config.md` 的参数写作
5. 写完后按 `writing/critic.md` 自审
6. 按 `writing/update-checklist.md` 更新所有文件
7. 保存到 `chapters/vol1-ch001.md`

---

## 常见问题

**Q：一定要按这个流程来吗？**
A：不一定。这是理想流程。你可以边写边补设定，但建议至少完成 Step 1-5 再开始写。

**Q：写到一半想改设定怎么办？**
A：改设定文件，然后检查所有引用了这个设定的章节，确认是否需要连带修改。

**Q：一章写多长合适？**
A：`config.md` 设定的是 3000-5000 字。核心场景可以更长，过渡章节可以更短。

**Q：自审没通过怎么办？**
A：修改后重新自审。直到通过才更新文档和保存正文。

---

*版本：v1.0*
