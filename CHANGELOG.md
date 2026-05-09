# Changelog

## v4.0 (2026-05-09)

### 重构：轻量化，聚焦写作质量

**核心理念变化**：从"追踪一切"转向"写好故事"。砍掉冗余的监控/仪表盘/索引系统，把注意力放回怎么把每一章写好看。

### Added
- `system.md` — 故事框架（情节节拍+章节切分+伏笔规则）
- `writing/guide.md` v4.0 — 完全重写，聚焦去AI味、节奏变化、情感共鸣、角色声音
- 模板目录新增 `characters/`、`plot/vol1/world/`、`writing/` 空结构

### Removed
- `persistent/` 目录（dashboard/foreshadow/index/monitor/reader-journey/timeline）— 过度追踪，实际写作中用不上
- `writing/quality.md` — 内容合并入 guide.md
- `writing/revision.md` — 流程过度复杂化
- `writing/update-checklist.md` — 过度追踪，用 story-state.md 替代
- 模板中的 `persistent/` 目录

### Changed
- `engine.md` — 简化模块协作规则
- `config.md` — 精简配置
- `writing/critic.md` — 精简自检清单
- `writing/annotated-example.md` — 更新示例
- `template/README.md` — 更新模板说明
- `worldview/master.md` — 更新格式

## v3.1 (2026-05-08)

### Added
- `naming.md` — 统一命名规范
- `persistent/index.md` — 全局ID注册表
- `persistent/dashboard.md` — 健康检查仪表盘
- `config.md` — 引擎配置（集中管理参数）
- `template/` — 冷启动模板（8个空模板文件）
- `README.md` — 项目说明
- `CHANGELOG.md` — 版本记录
- `LICENSE` — MIT许可证
- `.gitignore`

### Changed
- `protagonist.md` — 拆分为"当前状态"（顶部）+"历史档案"（底部）
- `update-checklist.md` — 增加依赖顺序、中断恢复、故障影响分析
- `engine.md` — 增加数据源规则、自我丰富规则

## v3.0 (2026-05-08)

### Added
- `engine.md` — 引擎总纲（模块协作规则）
- `persistent/reader-journey.md` — 读者旅程（情绪曲线+子线+节奏热力图）
- `persistent/monitor.md` — 主线监控（节点追踪+偏差预警）
- `writing/update-checklist.md` — 每章更新清单
- `writing/critic.md` — 自审系统

### Changed
- `persistent/characters/protagonist.md` — 增加性格维度、技能树、携带物品、关系表
- `persistent/characters/cast.md` — 增加完整画像、关系矩阵
- `system.md` → `engine.md` — 重命名

## v2.1 (2026-05-08)

### Added
- `writing/critic.md` — 自审系统（逻辑/节奏/人物/伏笔检查）

## v2.0 (2026-05-08)

### Added
- 五卷全部迁移到新结构（outline.md + world/ + act files）
- 按吸引力评估重新划分幕和章节数

### Changed
- 情节优先，章节为切分单位
- 灵活分幕（每卷幕数不固定）
- 情节节拍格式增加"传递给下一节拍"字段
- 伏笔编号区分层级（B-/V{N}-/C-）
- 新世界设定拆分（geography.md + power.md）

## v1.0 (2026-05-08)

### Added
- 初始框架搭建
- 世界观圣经
- 五卷大纲
- 第一章正文（已重写去AI味）
- 写作指南
- 角色档案
- 伏笔系统
- 时间线
