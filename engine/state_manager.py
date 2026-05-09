"""
state_manager.py — 状态管理与动态上下文组装

职责：
  1. 读写 state_db/ 下的 JSON 文件
  2. build_context(): 根据大纲动态组装 ≤8k token 上下文包
"""

import json
import os
import re
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------

STATE_DB_DIR = Path(__file__).parent.parent / "state_db"
CHARACTERS_FILE = STATE_DB_DIR / "characters.json"
WORLD_LORE_FILE = STATE_DB_DIR / "world_lore.json"
PLOT_TIMELINE_FILE = STATE_DB_DIR / "plot_timeline.json"


# ---------------------------------------------------------------------------
# JSON 读写
# ---------------------------------------------------------------------------

def load_json(filepath: Path) -> dict:
    """读取 JSON 文件，返回 dict。文件不存在则返回空 dict。"""
    if not filepath.exists():
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"JSON 解析失败: {filepath} — {e}")


def save_json(filepath: Path, data: dict) -> None:
    """写入 JSON 文件，自动创建目录。"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [state] 已写入 {filepath.name} ({filepath.stat().st_size} bytes)")


def load_characters() -> dict:
    return load_json(CHARACTERS_FILE)


def load_world_lore() -> dict:
    return load_json(WORLD_LORE_FILE)


def load_plot_timeline() -> dict:
    return load_json(PLOT_TIMELINE_FILE)


def save_characters(data: dict) -> None:
    save_json(CHARACTERS_FILE, data)


def save_world_lore(data: dict) -> None:
    save_json(WORLD_LORE_FILE, data)


def save_plot_timeline(data: dict) -> None:
    save_json(PLOT_TIMELINE_FILE, data)


# ---------------------------------------------------------------------------
# 实体提取：从大纲文本中识别角色名和地点
# ---------------------------------------------------------------------------

def _extract_entities(outline: str, characters_data: dict) -> tuple[list[str], list[str]]:
    """
    从大纲文本中提取出场角色 ID 和地点关键词。

    匹配逻辑：
      - 遍历 characters.json 中每个角色的 id 和 name
      - 如果大纲文本中包含该 name 或 id → 标记为出场角色
      - 地点：从大纲的 "在哪" 字段提取
    """
    chars = characters_data.get("characters", {})
    present_char_ids: list[str] = []
    mentioned_names: list[str] = []

    outline_lower = outline.lower()

    for char_id, char_info in chars.items():
        char_name = char_info.get("name", "")
        # 匹配 name（中文名）或 id（英文 id）
        if char_name and char_name in outline:
            present_char_ids.append(char_id)
            mentioned_names.append(char_name)
        elif char_id in outline_lower:
            present_char_ids.append(char_id)
            mentioned_names.append(char_id)

    # 提取地点：找 "在哪" 或 "位置" 后面的内容
    locations: list[str] = []
    loc_match = re.search(r"(?:在哪|位置|地点)[：:]\s*(.+?)(?:\n|$)", outline)
    if loc_match:
        locations.append(loc_match.group(1).strip())

    # 如果没有匹配到任何角色，默认包含主角
    if not present_char_ids:
        for char_id, char_info in chars.items():
            if char_info.get("role") == "主角":
                present_char_ids.append(char_id)
                mentioned_names.append(char_info.get("name", char_id))
                break

    return present_char_ids, locations


# ---------------------------------------------------------------------------
# 角色卡片格式化
# ---------------------------------------------------------------------------

def _format_character_card(char_id: str, char_data: dict) -> str:
    """将单个角色数据格式化为紧凑的文本卡片。"""
    lines = [f"### {char_data.get('name', char_id)}"]

    # 基础信息
    status = char_data.get("current_status", {})
    status_parts = []
    if status.get("health"):
        status_parts.append(f"健康:{status['health']}")
    if status.get("location"):
        status_parts.append(f"位置:{status['location']}")
    if status.get("mood"):
        status_parts.append(f"情绪:{status['mood']}")
    if status_parts:
        lines.append("状态: " + " | ".join(status_parts))

    # 装备
    equipment = status.get("equipment", [])
    if equipment:
        lines.append("装备: " + ", ".join(equipment))

    # 目标
    goals = char_data.get("active_goals", [])
    if goals:
        lines.append("目标: " + " / ".join(goals))

    # 性格（仅主角和重要角色）
    personality = char_data.get("personality")
    if personality:
        lines.append(f"性格: {personality}")

    # 技能
    skills = char_data.get("skills", {})
    if skills:
        skill_str = ", ".join(f"{k}({v})" for k, v in skills.items())
        lines.append(f"技能: {skill_str}")

    # 秘密（仅 hidden_secrets 中读者不知道的）
    secrets = char_data.get("hidden_secrets", [])
    if secrets:
        lines.append("秘密: " + " / ".join(secrets))

    # 与出场角色的关系
    relationships = char_data.get("relationships", {})
    if relationships:
        rel_strs = []
        for rel_id, rel_info in relationships.items():
            rel_type = rel_info.get("type", "")
            note = rel_info.get("note", "")
            rel_strs.append(f"{rel_id}({rel_type}:{note})" if note else f"{rel_id}({rel_type})")
        lines.append("关系: " + ", ".join(rel_strs))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 世界规则过滤
# ---------------------------------------------------------------------------

def _filter_world_rules(locations: list[str], world_lore: dict) -> str:
    """根据地点关键词，提取相关的世界规则子集。"""
    lines = []

    # 基础设定（总是包含）
    setting = world_lore.get("setting", {})
    if setting:
        lines.append(f"时间: {setting.get('start_date', '未知')}")
        lines.append(f"视角: {setting.get('perspective', '未知')}")

    # 屏障规则（总是包含，因为是核心机制）
    barrier = world_lore.get("barrier", {})
    if barrier:
        props = barrier.get("properties", {})
        lines.append(f"屏障: {props.get('transparency', '')}")
        lines.append(f"匹配: {props.get('top_match', {}).get('name', '')} "
                      f"({props.get('top_match', {}).get('match_rate', 0)*100}%)")

    # 时间规则
    time_rules = world_lore.get("time_rules", {})
    if time_rules:
        lines.append(f"时间比例: {time_rules.get('earth_to_alien_ratio', '')}")

    # 世界列表 — 只提取当前相关的世界
    worlds = world_lore.get("worlds", [])
    for world in worlds:
        world_name = world.get("name", "")
        # 如果地点中提到了这个世界，或者世界状态是 active
        if world.get("status") == "active" or any(world_name in loc for loc in locations):
            features = ", ".join(world.get("features", []))
            lines.append(f"世界·{world_name}: {world.get('type', '')} — {features}")

    # 穹顶基地（总是包含，前期相关）
    dome = world_lore.get("dome_base", {})
    if dome:
        lines.append(f"穹顶: {dome.get('location', '')}, {dome.get('personnel', '')}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 伏笔格式化
# ---------------------------------------------------------------------------

def _format_foreshadowing(plot_timeline: dict) -> str:
    """提取 status=open 的伏笔。"""
    foreshadows = plot_timeline.get("foreshadowing", [])
    open_items = [f for f in foreshadows if f.get("status") == "open"]
    if not open_items:
        return "（无开放伏笔）"
    lines = []
    for item in open_items:
        lines.append(f"- [{item['id']}] {item['content']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 最近章节摘要格式化
# ---------------------------------------------------------------------------

def _format_recent_chapters(plot_timeline: dict) -> str:
    """格式化最近 N 章摘要。"""
    chapters = plot_timeline.get("recent_chapters", [])
    if not chapters:
        return "（这是第一章，无前情）"
    lines = []
    for ch in chapters:
        ch_num = ch.get("chapter", "?")
        title = ch.get("title", "")
        synopsis = ch.get("synopsis", "")
        events = ", ".join(ch.get("key_events", []))
        lines.append(f"Ch.{ch_num} {title}: {synopsis}")
        if events:
            lines.append(f"  关键事件: {events}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 核心：build_context
# ---------------------------------------------------------------------------

def build_context(outline: str) -> str:
    """
    根据大纲文本，动态组装 ≤8k token 的上下文包。

    流程：
      1. 加载三个 JSON
      2. 从大纲中提取出场角色和地点
      3. 过滤并格式化各模块
      4. 拼装成最终 context string

    参数:
        outline: 章节大纲文本（节拍描述）

    返回:
        组装好的上下文字符串
    """
    # 加载数据
    characters_data = load_characters()
    world_lore = load_world_lore()
    plot_timeline = load_plot_timeline()

    # 提取实体
    char_ids, locations = _extract_entities(outline, characters_data)

    # 组装各模块
    sections = []

    # 1. 故事状态
    sections.append("## STORY STATE")
    sections.append(f"当前位置: {plot_timeline.get('current_location', '未知')}")
    sections.append(f"\n全局摘要:\n{plot_timeline.get('global_synopsis', '无')}")
    sections.append(f"\n最近章节:\n{_format_recent_chapters(plot_timeline)}")

    # 2. 角色卡片（仅出场角色）
    chars = characters_data.get("characters", {})
    if char_ids:
        sections.append("\n## CHARACTER CARDS")
        for cid in char_ids:
            if cid in chars:
                sections.append(_format_character_card(cid, chars[cid]))

    # 3. 世界规则（过滤后）
    sections.append("\n## WORLD RULES")
    sections.append(_filter_world_rules(locations, world_lore))

    # 4. 开放伏笔
    sections.append("\n## ACTIVE FORESHADOWING")
    sections.append(_format_foreshadowing(plot_timeline))

    # 5. 章节大纲
    sections.append("\n## CHAPTER OUTLINE")
    sections.append(outline)

    context = "\n".join(sections)

    # Token 粗略检查（1 中文字 ≈ 2 tokens）
    char_count = len(context)
    estimated_tokens = char_count * 1.5  # 粗略估计
    if estimated_tokens > 8000:
        print(f"  [context] ⚠️ 上下文约 {int(estimated_tokens)} tokens，超过 8k 限制")
    else:
        print(f"  [context] 上下文约 {int(estimated_tokens)} tokens，{char_count} 字符")

    return context


# ---------------------------------------------------------------------------
# Archivist 调用：应用状态更新
# ---------------------------------------------------------------------------

def apply_state_updates(updates: dict) -> None:
    """
    将 Archivist 输出的 JSON 更新应用到 state_db。

    参数:
        updates: Archivist 输出的 JSON dict，格式见 agents/archivist.md
    """
    # 更新 characters.json
    char_updates = updates.get("character_updates", {})
    if char_updates:
        characters_data = load_characters()
        chars = characters_data.get("characters", {})
        for char_id, changes in char_updates.items():
            if char_id in chars:
                # 深度合并 current_status
                if "current_status" in changes:
                    chars[char_id].setdefault("current_status", {}).update(changes["current_status"])
                # 替换 active_goals
                if "active_goals" in changes:
                    chars[char_id]["active_goals"] = changes["active_goals"]
                # 合并 relationships
                if "relationships" in changes:
                    chars[char_id].setdefault("relationships", {}).update(changes["relationships"])
                # 替换 hidden_secrets
                if "hidden_secrets" in changes:
                    chars[char_id]["hidden_secrets"] = changes["hidden_secrets"]
                # 更新 last_appeared
                if "last_appeared" in changes:
                    chars[char_id]["last_appeared"] = changes["last_appeared"]
                # 更新 arc_stage
                if "arc_stage" in changes:
                    chars[char_id]["arc_stage"] = changes["arc_stage"]
            else:
                # 新角色
                chars[char_id] = changes
        characters_data["characters"] = chars
        save_characters(characters_data)

    # 更新 plot_timeline.json
    timeline_entry = updates.get("timeline_entry")
    if timeline_entry:
        plot_data = load_plot_timeline()
        # 添加到 recent_chapters（保留最近 3 章）
        recent = plot_data.get("recent_chapters", [])
        recent.append(timeline_entry)
        if len(recent) > 3:
            recent = recent[-3:]
        plot_data["recent_chapters"] = recent
        # 更新 current_chapter
        plot_data["current_chapter"] = timeline_entry.get("chapter", plot_data.get("current_chapter", 0))
        # 更新 current_location
        if "current_location" in updates:
            plot_data["current_location"] = updates["current_location"]
        save_plot_timeline(plot_data)

    # 更新伏笔
    foreshadow_changes = updates.get("foreshadowing_changes", [])
    if foreshadow_changes:
        plot_data = load_plot_timeline()
        foreshadows = plot_data.get("foreshadowing", [])
        for change in foreshadow_changes:
            action = change.get("action")
            if action == "new":
                foreshadows.append({
                    "id": change["id"],
                    "content": change["content"],
                    "planted_at": f"ch{updates.get('timeline_entry', {}).get('chapter', '???'):03d}",
                    "status": "open"
                })
            elif action == "advance":
                for f in foreshadows:
                    if f["id"] == change["id"]:
                        f["note"] = change.get("note", "")
            elif action == "close":
                for f in foreshadows:
                    if f["id"] == change["id"]:
                        f["status"] = "closed"
        plot_data["foreshadowing"] = foreshadows
        save_plot_timeline(plot_data)

    # 追加战斗日志
    combat_log = updates.get("combat_log")
    if combat_log:
        plot_data = load_plot_timeline()
        plot_data.setdefault("combat_logs", []).append(combat_log)
        save_plot_timeline(plot_data)

    # 追加资源变更记录
    resource_changes = updates.get("resource_changes")
    if resource_changes:
        plot_data = load_plot_timeline()
        chapter_num = updates.get("timeline_entry", {}).get("chapter", 0)
        change_record = {"chapter": chapter_num, "changes": resource_changes}
        plot_data.setdefault("resource_log", []).append(change_record)
        save_plot_timeline(plot_data)

    print("  [state] 状态更新完成")


# ---------------------------------------------------------------------------
# 测试入口
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # 测试 build_context
    test_outline = """
    节拍 B6：探索森林
    - 发生什么：林晨在紫色森林中探索，发现水源和可食用植物
    - 谁：林晨
    - 在哪：紫色森林
    - 冲突：未知环境的危险
    - 情绪：紧张→好奇
    """
    ctx = build_context(test_outline)
    print("\n" + "=" * 60)
    print(ctx)
