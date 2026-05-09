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
| `engine.md` | 总纲 | 一般不需要改 |
| `system.md` | 故事框架 | 一般不需要改 |
| `config.md` | 可调参数 | 按需调整 |
| `naming.md` | 命名规范 | 一般不需要改 |
| `story-state.md` | 状态追踪 | 每章写完更新 |
| `worldview/master.md` | 顶层世界观 | 填入你的世界观设定 |
| `plot/vol1/outline.md` | 第一卷大纲 | 填入故事梗概 |
| `plot/vol1/world/geography.md` | 世界地理 | 填入地理+文明 |
| `plot/vol1/world/power.md` | 力量体系 | 填入力量等级表 |
| `plot/vol1/act1.md` | 第一幕 | 填入情节节拍 |
| `characters/protagonist.md` | 主角档案 | 填入主角设定 |
| `characters/cast.md` | 角色库 | 填入角色设定 |
| `writing/guide.md` | 写作指南 | 一般不需要改 |
| `writing/critic.md` | 自审清单 | 一般不需要改 |

## 最小启动

最少只需要填：

1. `worldview/master.md` — 世界观
2. `plot/vol1/outline.md` — 第一卷大纲
3. `plot/vol1/act1.md` — 第一幕节拍
4. `characters/protagonist.md` — 主角

其他文件可以边写边填。
