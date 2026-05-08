# 写作引擎模板

> 新建小说时，复制本目录到新项目，填入具体内容即可。

## 使用方法

```bash
cp -r template/ my-new-novel/
cd my-new-novel/
```

然后逐个文件填入你的小说设定。

## 文件清单

| 文件 | 说明 | 需要填什么 |
|------|------|-----------|
| `engine.md` | 引擎总纲 | 一般不需要改 |
| `naming.md` | 命名规范 | 一般不需要改 |
| `worldview/master.md` | 顶层世界观 | 填入你的世界观设定 |
| `plot/vol1/outline.md` | 第一卷大纲 | 填入故事梗概 |
| `plot/vol1/world/geography.md` | 世界地理 | 填入地理+文明 |
| `plot/vol1/world/power.md` | 力量体系 | 填入力量等级表 |
| `plot/vol1/act1.md` | 第一幕 | 填入情节节拍 |
| `persistent/foreshadow.md` | 伏笔系统 | 填入伏笔规划 |
| `persistent/timeline.md` | 时间线 | 填入时间设定 |
| `persistent/characters/protagonist.md` | 主角档案 | 填入主角设定 |
| `persistent/characters/cast.md` | 角色库 | 填入角色设定 |
| `persistent/reader-journey.md` | 读者旅程 | 填入情绪曲线规划 |
| `persistent/monitor.md` | 主线监控 | 填入主线节点 |
| `persistent/dashboard.md` | 健康仪表盘 | 初始化所有指标 |
| `writing/guide.md` | 写作指南 | 一般不需要改 |
| `writing/critic.md` | 自审系统 | 一般不需要改 |
| `writing/update-checklist.md` | 更新清单 | 一般不需要改 |

## 最小启动

如果不想一次填完所有文件，最少只需要填：

1. `worldview/master.md` — 世界观
2. `plot/vol1/outline.md` — 第一卷大纲
3. `plot/vol1/act1.md` — 第一幕节拍
4. `persistent/characters/protagonist.md` — 主角

其他文件可以边写边填。
