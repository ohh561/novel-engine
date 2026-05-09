"""
macro_director.py — 宏观调度与动态节奏控制器

职责：
  1. Rhythm Director: 规划卷级剧情节点，按吸引力评分分配章节预算
  2. Fractal Outliner: 将大节点拆解为连续微节拍
  3. 主调度循环: 按节点顺序推动生成

核心理念：
  - 高吸引力事件 → 大量章节，充分展开
  - 低吸引力事件 → 极少章节，快速带过
  - 不是每个事件都值得写10章
"""

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from engine.agent_callers import _call_llm, _parse_json_response
from engine.state_manager import (
    load_characters, load_plot_timeline, load_world_lore,
    save_json, load_json,
)
from engine.agent_callers import _call_llm, _parse_json_response


# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------

VOLUME_PLAN_FILE = Path(__file__).parent.parent / "state_db" / "volume_plan.json"
BEATS_DIR = Path(__file__).parent.parent / "state_db" / "beats"


# ---------------------------------------------------------------------------
# 数据类
# ---------------------------------------------------------------------------

@dataclass
class PlotNode:
    """剧情节点"""
    node_id: str
    node_title: str
    event_description: str
    appeal_score: float
    chapter_budget: int
    expansion_status: str  # pending, in_progress, completed
    narrative_function: str = ""
    hooks: list[str] = field(default_factory=list)


@dataclass
class MicroBeat:
    """微节拍（对应1章）"""
    beat_id: str
    chapter_number: int
    beat_title: str
    outline: str
    characters_present: list[str]
    location: str
    conflict: str
    emotion: str
    hook: str
    foreshadowing: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# volume_plan.json 读写
# ---------------------------------------------------------------------------

def load_volume_plan() -> dict:
    return load_json(VOLUME_PLAN_FILE)


def save_volume_plan(data: dict) -> None:
    save_json(VOLUME_PLAN_FILE, data)


def get_current_volume() -> dict:
    """获取当前卷的节点列表。"""
    plan = load_volume_plan()
    vol_num = plan.get("current_volume", 1)
    return plan.get("volumes", {}).get(str(vol_num), {})


def get_all_nodes() -> list[PlotNode]:
    """获取当前卷的所有 PlotNode。"""
    vol = get_current_volume()
    nodes = []
    for n in vol.get("nodes", []):
        nodes.append(PlotNode(
            node_id=n["node_id"],
            node_title=n["node_title"],
            event_description=n["event_description"],
            appeal_score=n["appeal_score"],
            chapter_budget=n["chapter_budget"],
            expansion_status=n["expansion_status"],
            narrative_function=n.get("narrative_function", ""),
            hooks=n.get("hooks", []),
        ))
    return nodes


def get_next_pending_node() -> Optional[PlotNode]:
    """获取下一个待展开的节点。"""
    nodes = get_all_nodes()
    for node in nodes:
        if node.expansion_status == "pending":
            return node
    return None


def mark_node_status(node_id: str, status: str) -> None:
    """更新节点状态。"""
    plan = load_volume_plan()
    vol_num = plan.get("current_volume", 1)
    nodes = plan["volumes"][str(vol_num)]["nodes"]
    for node in nodes:
        if node["node_id"] == node_id:
            node["expansion_status"] = status
            break
    save_volume_plan(plan)


# ---------------------------------------------------------------------------
# Rhythm Director Agent
# ---------------------------------------------------------------------------

RHYTHM_DIRECTOR_PROMPT = """你是一个百万字长篇网文的节奏导演，拥有"起点白金作家"级别的商业嗅觉。

你将收到一卷大纲。你的任务：将本卷拆解为 10-30 个剧情节点（Plot Nodes），并为每个节点分配吸引力评分和章节预算。

核心原则：吸引力决定篇幅。
- 高吸引力事件（战斗、反转、身份揭露、感情高潮）→ 大量章节（40-100章）
- 低吸引力事件（赶路、修整、设定解释）→ 极少章节（1-2章快速带过）

评分标准 appeal_score (0-10):
- 9-10: 核心爽点/大高潮（最终决战、反杀、身份暴露）→ 40-100章
- 7-8: 高吸引力（遭遇强敌、获得新能力、信任危机）→ 15-40章
- 5-6: 中等吸引力（探索新区域、学习技能）→ 5-15章
- 3-4: 低吸引力（赶路、信息收集）→ 2-5章
- 1-2: 过渡（设定解释、回忆）→ 1章带过

黄金节奏：低→中→高→更高→喘息→再高→最高→余韵

你必须输出以下 JSON 格式：
{
  "volume": 1,
  "volume_title": "初遇",
  "total_chapters_estimate": 200,
  "nodes": [
    {
      "node_id": "V1_N01",
      "node_title": "节点标题",
      "event_description": "一句话描述事件",
      "appeal_score": 7.0,
      "chapter_budget": 15,
      "expansion_status": "pending",
      "narrative_function": "叙事功能（开篇/高潮/过渡/收尾等）",
      "hooks": ["钩子1", "钩子2"]
    }
  ]
}"""


def call_rhythm_director(volume_outline: str) -> list[PlotNode]:
    """
    调用 Rhythm Director 规划卷级剧情节点。

    参数:
        volume_outline: 本卷大纲文本

    返回:
        PlotNode 列表
    """
    # 组装上下文
    characters = load_characters()
    timeline = load_plot_timeline()

    chars_summary = {}
    for cid, cdata in characters.get("characters", {}).items():
        chars_summary[cid] = {
            "name": cdata.get("name"),
            "role": cdata.get("role"),
            "arc_stage": cdata.get("arc_stage"),
        }

    user_prompt = (
        f"## 角色状态\n\n{json.dumps(chars_summary, ensure_ascii=False, indent=2)}\n\n"
        f"## 全局摘要\n\n{timeline.get('global_synopsis', '（新故事）')}\n\n"
        f"## 本卷大纲\n\n{volume_outline}"
    )

    print("  [rhythm_director] 规划剧情节点...")
    raw = _call_llm(
        system_prompt=RHYTHM_DIRECTOR_PROMPT,
        user_prompt=user_prompt,
        temperature=0.7,
        max_tokens=8000,
        json_mode=True,
    )

    try:
        data = _parse_json_response(raw)
    except ValueError:
        print("  [rhythm_director] ⚠️ JSON 解析失败，重试...")
        raw = _call_llm(
            system_prompt=RHYTHM_DIRECTOR_PROMPT + "\n\n请务必输出合法 JSON。",
            user_prompt=user_prompt,
            temperature=0.5,
            max_tokens=8000,
            json_mode=False,
        )
        data = _parse_json_response(raw)

    nodes = []
    for n in data.get("nodes", []):
        nodes.append(PlotNode(
            node_id=n["node_id"],
            node_title=n["node_title"],
            event_description=n["event_description"],
            appeal_score=float(n["appeal_score"]),
            chapter_budget=int(n["chapter_budget"]),
            expansion_status="pending",
            narrative_function=n.get("narrative_function", ""),
            hooks=n.get("hooks", []),
        ))

    print(f"  [rhythm_director] 完成，{len(nodes)} 个节点，"
          f"预估 {sum(n.chapter_budget for n in nodes)} 章")
    return nodes


def plan_volume(volume_outline: str, volume_number: int = 1) -> list[PlotNode]:
    """
    规划一卷的剧情节点并保存到 volume_plan.json。

    参数:
        volume_outline: 本卷大纲文本
        volume_number: 卷号

    返回:
        PlotNode 列表
    """
    nodes = call_rhythm_director(volume_outline)

    # 构建 volume_plan 数据
    plan = load_volume_plan()
    plan["current_volume"] = volume_number
    if "volumes" not in plan:
        plan["volumes"] = {}

    plan["volumes"][str(volume_number)] = {
        "volume_title": f"第{volume_number}卷",
        "total_chapters_estimate": sum(n.chapter_budget for n in nodes),
        "nodes": [
            {
                "node_id": n.node_id,
                "node_title": n.node_title,
                "event_description": n.event_description,
                "appeal_score": n.appeal_score,
                "chapter_budget": n.chapter_budget,
                "expansion_status": n.expansion_status,
                "narrative_function": n.narrative_function,
                "hooks": n.hooks,
            }
            for n in nodes
        ],
    }

    save_volume_plan(plan)
    print(f"  [macro] volume_plan.json 已更新：{len(nodes)} 个节点")
    return nodes


# ---------------------------------------------------------------------------
# Fractal Outliner Agent
# ---------------------------------------------------------------------------

FRACTAL_OUTLINER_PROMPT = """你是一个长篇网文的章节规划师。你的任务是把一个大剧情节点拆成 N 个连续的微小节拍，每个节拍对应 1 章。

你将收到：
1. 剧情节点信息（事件描述、吸引力评分、章节预算）
2. 角色当前状态
3. 最近章节摘要

拆解原则：

高吸引力节点 (score ≥ 7)：
- 战前铺垫（紧张感建立）
- 战中分阶段（试探→劣势→底牌→逆转→再逆转）
- 战后余波（伤势、战利品、配角反应）
- 每 3-5 章要有一个小高潮

低吸引力节点 (score ≤ 4)：
- 快速带过，但每章至少一个钩子
- 用"意外发现"或"伏笔"提升吸引力

每章节拍格式：
{
  "beat_id": "V1_N07_B01",
  "chapter_number": 45,
  "beat_title": "节拍标题",
  "outline": "详细的章节大纲，200-300字",
  "characters_present": ["角色id"],
  "location": "场景地点",
  "conflict": "本章的核心冲突",
  "emotion": "情绪起点→终点",
  "hook": "读者为什么要继续读下一章"
}

输出 JSON 格式：
{
  "node_id": "V1_N07",
  "node_title": "节点标题",
  "total_beats": 25,
  "beats": [ ... ]
}"""


def call_fractal_outliner(node: PlotNode) -> list[MicroBeat]:
    """
    调用 Fractal Outliner 将大节点拆解为微节拍。

    参数:
        node: 要拆解的 PlotNode

    返回:
        MicroBeat 列表
    """
    characters = load_characters()
    timeline = load_plot_timeline()

    # 简化角色数据
    chars_summary = {}
    for cid, cdata in characters.get("characters", {}).items():
        chars_summary[cid] = {
            "name": cdata.get("name"),
            "current_status": cdata.get("current_status"),
            "active_goals": cdata.get("active_goals"),
        }

    user_prompt = (
        f"## 剧情节点\n\n"
        f"- ID: {node.node_id}\n"
        f"- 标题: {node.node_title}\n"
        f"- 事件: {node.event_description}\n"
        f"- 吸引力: {node.appeal_score}/10\n"
        f"- 章节预算: {node.chapter_budget} 章\n"
        f"- 叙事功能: {node.narrative_function}\n"
        f"- 钩子: {', '.join(node.hooks)}\n\n"
        f"## 角色状态\n\n{json.dumps(chars_summary, ensure_ascii=False, indent=2)}\n\n"
        f"## 最近章节\n\n"
    )

    recent = timeline.get("recent_chapters", [])
    if recent:
        for ch in recent[-3:]:
            user_prompt += f"Ch.{ch['chapter']} {ch.get('title','')}: {ch.get('synopsis','')}\n"
    else:
        user_prompt += "（无前情）\n"

    print(f"  [fractal_outliner] 拆解 {node.node_id} ({node.chapter_budget} 章)...")
    raw = _call_llm(
        system_prompt=FRACTAL_OUTLINER_PROMPT,
        user_prompt=user_prompt,
        temperature=0.7,
        max_tokens=12000,
        json_mode=True,
    )

    try:
        data = _parse_json_response(raw)
    except ValueError:
        print("  [fractal_outliner] ⚠️ JSON 解析失败，重试...")
        raw = _call_llm(
            system_prompt=FRACTAL_OUTLINER_PROMPT + "\n\n请务必输出合法 JSON。",
            user_prompt=user_prompt,
            temperature=0.5,
            max_tokens=12000,
            json_mode=False,
        )
        data = _parse_json_response(raw)

    beats = []
    for b in data.get("beats", []):
        beats.append(MicroBeat(
            beat_id=b["beat_id"],
            chapter_number=b["chapter_number"],
            beat_title=b["beat_title"],
            outline=b["outline"],
            characters_present=b.get("characters_present", []),
            location=b.get("location", ""),
            conflict=b.get("conflict", ""),
            emotion=b.get("emotion", ""),
            hook=b.get("hook", ""),
            foreshadowing=b.get("foreshadowing", []),
        ))

    print(f"  [fractal_outliner] 完成，{len(beats)} 个微节拍")
    return beats


def expand_node(node: PlotNode) -> list[MicroBeat]:
    """
    展开一个 Plot Node：拆解为微节拍并保存。

    参数:
        node: 要展开的 PlotNode

    返回:
        MicroBeat 列表
    """
    if node.chapter_budget <= 1:
        # 只有1章，不需要拆解，直接生成一个微节拍
        beat = MicroBeat(
            beat_id=f"{node.node_id}_B01",
            chapter_number=0,  # 由主循环分配
            beat_title=node.node_title,
            outline=node.event_description,
            characters_present=[],
            location="",
            conflict="",
            emotion="",
            hook=node.hooks[0] if node.hooks else "",
        )
        return [beat]

    beats = call_fractal_outliner(node)

    # 保存到 beats 目录
    BEATS_DIR.mkdir(parents=True, exist_ok=True)
    beats_file = BEATS_DIR / f"{node.node_id}.json"
    beats_data = {
        "node_id": node.node_id,
        "node_title": node.node_title,
        "total_beats": len(beats),
        "beats": [
            {
                "beat_id": b.beat_id,
                "chapter_number": b.chapter_number,
                "beat_title": b.beat_title,
                "outline": b.outline,
                "characters_present": b.characters_present,
                "location": b.location,
                "conflict": b.conflict,
                "emotion": b.emotion,
                "hook": b.hook,
                "foreshadowing": b.foreshadowing,
            }
            for b in beats
        ],
    }
    save_json(beats_file, beats_data)

    # 更新节点状态
    mark_node_status(node.node_id, "in_progress")

    return beats


# ---------------------------------------------------------------------------
# 主调度循环
# ---------------------------------------------------------------------------

def generate_volume(volume_outline: str, volume_number: int = 1) -> None:
    """
    生成一卷的完整流程。

    参数:
        volume_outline: 本卷大纲
        volume_number: 卷号
    """
    from engine.main_orchestrator import generate_chapter

    print(f"\n{'='*60}")
    print(f"📚 开始生成第 {volume_number} 卷")
    print(f"{'='*60}")

    # Step 1: Rhythm Director 规划节点
    print(f"\n[Phase 1] Rhythm Director 规划剧情节点...")
    nodes = plan_volume(volume_outline, volume_number)

    # 打印节点计划
    print(f"\n{'─'*60}")
    print(f"{'节点':<12} {'吸引力':>6} {'章节':>6} {'状态':<10} 标题")
    print(f"{'─'*60}")
    for n in nodes:
        bar = "█" * int(n.appeal_score)
        print(f"{n.node_id:<12} {n.appeal_score:>5.1f} {n.chapter_budget:>5}章 "
              f"{'pending':<10} {n.node_title} {bar}")
    print(f"{'─'*60}")
    print(f"总计: {sum(n.chapter_budget for n in nodes)} 章")
    print(f"{'─'*60}")

    # Step 2: 逐节点展开
    global_chapter = 1  # 全局章节计数器

    for node in nodes:
        print(f"\n[Phase 2] 展开节点 {node.node_id}: {node.node_title} "
              f"(score={node.appeal_score}, budget={node.chapter_budget})")

        # Fractal Outliner 拆解
        beats = expand_node(node)

        # 为每个微节拍分配全局章节号
        for i, beat in enumerate(beats):
            beat.chapter_number = global_chapter + i

        # Step 3: 逐章生成
        for beat in beats:
            print(f"\n  ── 生成 Ch.{beat.chapter_number}: {beat.beat_title} ──")
            try:
                generate_chapter(
                    chapter_number=beat.chapter_number,
                    outline=beat.outline,
                    volume=volume_number,
                )
            except Exception as e:
                print(f"  ❌ Ch.{beat.chapter_number} 生成失败: {e}")
                # 标记节点为失败，但继续
                mark_node_status(node.node_id, "failed")
                break

        global_chapter += len(beats)

        # 标记节点完成
        mark_node_status(node.node_id, "completed")
        print(f"  ✅ {node.node_id} 完成 ({len(beats)} 章)")

    print(f"\n{'='*60}")
    print(f"✅ 第 {volume_number} 卷生成完成")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# World-Builder Agent：跨卷世界观重置
# ---------------------------------------------------------------------------

WORLD_BUILDER_PROMPT = """你是一个跨卷世界观管理员。你将收到：
1. 上一卷的 world_lore.json（当前状态）
2. 上一卷的战斗结果摘要（从 combat_logs 提取）
3. 新一卷的大纲

你的任务：输出 world_lore.json 的更新指令。

提取规则：

1. earth_status_update：
   - current_volume: 新卷号
   - integrated_tech: 地球新获得的科技/能力列表
   - military_strength: 军事力量描述
   - special_capabilities: 新增特殊能力
   - casualties_total: 累计伤亡
   - global_mood: 全球情绪

2. archive_realm：
   - 将当前卷对手世界归档
   - 包含：world_id, world_name, world_type, outcome, battle_summary,
     territory_gained, tech_acquired, key_events, unresolved_threads

3. new_active_realm：
   - 从新卷大纲提取新对手世界设定
   - 最关键：current_power_dynamic
     - summary: 一句话战力对比
     - earth_advantage: 地球优势列表
     - enemy_advantage: 敌方优势列表
     - balance: earth_dominant / earth_slight_advantage / balanced / enemy_slight_advantage / enemy_dominant
     - risk_factor: 最大风险
   - key_threats: 主要威胁列表（name, level, note）

输出严格 JSON 格式：
{
  "earth_status_update": { ... },
  "archive_realm": { ... },
  "new_active_realm": { ... }
}"""


def call_world_builder(
    current_lore: dict,
    combat_summary: str,
    new_volume_outline: str,
) -> dict:
    """
    调用 World-Builder Agent 生成跨卷世界观更新指令。

    参数:
        current_lore: 当前 world_lore.json 数据
        combat_summary: 上一卷战斗结果摘要
        new_volume_outline: 新一卷大纲文本

    返回:
        更新指令 dict
    """
    user_prompt = (
        f"## 当前 world_lore.json\n\n{json.dumps(current_lore, ensure_ascii=False, indent=2)}\n\n"
        f"## 上一卷战斗结果\n\n{combat_summary}\n\n"
        f"## 新一卷大纲\n\n{new_volume_outline}"
    )

    print("  [world_builder] 生成跨卷更新...")
    raw = _call_llm(
        system_prompt=WORLD_BUILDER_PROMPT,
        user_prompt=user_prompt,
        temperature=0.5,
        max_tokens=6000,
        json_mode=True,
    )

    try:
        data = _parse_json_response(raw)
    except ValueError:
        print("  [world_builder] ⚠️ JSON 解析失败，重试...")
        raw = _call_llm(
            system_prompt=WORLD_BUILDER_PROMPT + "\n\n请务必输出合法 JSON。",
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=6000,
            json_mode=False,
        )
        data = _parse_json_response(raw)

    print("  [world_builder] 完成")
    return data


def apply_volume_transition(transition_data: dict) -> None:
    """
    将 World-Builder 的输出应用到 world_lore.json。

    参数:
        transition_data: call_world_builder 的输出
    """
    from engine.state_manager import load_world_lore, save_world_lore

    lore = load_world_lore()

    # 1. 更新 earth_status
    earth_update = transition_data.get("earth_status_update", {})
    if earth_update:
        earth = lore.get("earth_status", {})
        for key, value in earth_update.items():
            earth[key] = value
        lore["earth_status"] = earth

    # 2. 归档当前对手世界
    archive = transition_data.get("archive_realm", {})
    if archive:
        archived = lore.get("archived_realms", {"realms": []})
        archived["realms"].append(archive)
        lore["archived_realms"] = archived

    # 3. 重置 active_realm
    new_realm = transition_data.get("new_active_realm", {})
    if new_realm:
        lore["active_realm"] = new_realm

    # 更新时间戳
    lore.setdefault("_meta", {})["last_updated"] = time.strftime("%Y-%m-%d")

    save_world_lore(lore)
    print("  [world_builder] world_lore.json 已更新")


def build_transition_context(current_volume: int, new_volume_outline: str) -> str:
    """
    构建 World-Builder 的输入上下文。

    参数:
        current_volume: 当前卷号
        new_volume_outline: 新一卷大纲

    返回:
        combat_summary 文本
    """
    from engine.state_manager import load_world_lore, load_plot_timeline

    lore = load_world_lore()
    timeline = load_plot_timeline()

    # 提取战斗日志摘要
    combat_logs = timeline.get("combat_logs", [])
    if combat_logs:
        combat_lines = []
        for log in combat_logs[-5:]:  # 最近5次战斗
            engagement = log.get("engagement", "?")
            outcome = log.get("outcome", "?")
            combat_lines.append(f"- {engagement}: {outcome}")
        combat_summary = "最近战斗：\n" + "\n".join(combat_lines)
    else:
        combat_summary = "（无战斗记录）"

    return combat_summary


def transition_to_next_volume(
    current_volume: int,
    new_volume_outline: str,
    new_volume_number: int,
) -> None:
    """
    跨卷世界观重置协议。

    流程：
      1. 读取上一卷的 world_lore.json 和战斗结果
      2. 调用 World-Builder Agent 生成更新指令
      3. 应用更新：归档旧世界、提取新世界、重置战力对比
      4. 重置 volume_plan.json 和 plot_timeline.json

    参数:
        current_volume: 当前（刚结束的）卷号
        new_volume_outline: 新一卷大纲文本
        new_volume_number: 新卷号
    """
    from engine.state_manager import load_world_lore

    print(f"\n{'='*60}")
    print(f"🔄 跨卷世界观重置：第 {current_volume} 卷 → 第 {new_volume_number} 卷")
    print(f"{'='*60}")

    # Step 1: 读取当前状态
    print("\n[Step 1/4] 读取当前世界状态...")
    lore = load_world_lore()
    combat_summary = build_transition_context(current_volume, new_volume_outline)
    print(f"  当前对手: {lore.get('active_realm', {}).get('world_name', '?')}")
    print(f"  战斗记录: {len(lore.get('archived_realms', {}).get('realms', []))} 个已归档")

    # Step 2: 调用 World-Builder
    print("\n[Step 2/4] 调用 World-Builder Agent...")
    transition_data = call_world_builder(lore, combat_summary, new_volume_outline)

    # Step 3: 应用更新
    print("\n[Step 3/4] 应用世界观更新...")
    apply_volume_transition(transition_data)

    # Step 4: 重置卷级状态
    print("\n[Step 4/4] 重置卷级状态...")
    plan = load_volume_plan()
    plan["current_volume"] = new_volume_number
    plan["volumes"][str(new_volume_number)] = {
        "volume_title": f"第{new_volume_number}卷",
        "total_chapters_estimate": 0,
        "nodes": [],
    }
    save_volume_plan(plan)

    # 打印摘要
    new_realm = transition_data.get("new_active_realm", {})
    power = new_realm.get("current_power_dynamic", {})
    print(f"\n{'─'*60}")
    print(f"新对手: {new_realm.get('world_name', '?')} ({new_realm.get('world_type', '?')})")
    print(f"战力对比: {power.get('balance', '?')}")
    print(f"摘要: {power.get('summary', '?')}")
    print(f"地球优势: {', '.join(power.get('earth_advantage', []))}")
    print(f"敌方优势: {', '.join(power.get('enemy_advantage', []))}")
    print(f"风险: {power.get('risk_factor', '?')}")
    print(f"{'─'*60}")

    print(f"\n✅ 第 {new_volume_number} 卷世界观重置完成\n")


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Novel Engine — 宏观调度器")
    subparsers = parser.add_subparsers(dest="command")

    # plan-volume: 规划一卷的节点
    plan_parser = subparsers.add_parser("plan-volume", help="规划卷级剧情节点")
    plan_parser.add_argument("--volume", type=int, default=1, help="卷号")
    plan_parser.add_argument("--outline", type=str, required=True, help="卷大纲文本或文件路径")

    # expand-node: 展开一个节点
    expand_parser = subparsers.add_parser("expand-node", help="展开一个剧情节点")
    expand_parser.add_argument("--node-id", type=str, required=True, help="节点ID (如 V1_N07)")

    # generate-volume: 生成整卷
    gen_parser = subparsers.add_parser("generate-volume", help="生成整卷")
    gen_parser.add_argument("--volume", type=int, default=1, help="卷号")
    gen_parser.add_argument("--outline", type=str, required=True, help="卷大纲文本或文件路径")

    # transition-volume: 跨卷世界观重置
    trans_parser = subparsers.add_parser("transition-volume", help="跨卷世界观重置")
    trans_parser.add_argument("--current-volume", type=int, required=True, help="当前卷号")
    trans_parser.add_argument("--new-volume", type=int, required=True, help="新卷号")
    trans_parser.add_argument("--new-outline", type=str, required=True, help="新卷大纲文本或文件路径")

    # status: 查看当前计划状态
    subparsers.add_parser("status", help="查看当前卷计划状态")

    args = parser.parse_args()

    if args.command == "plan-volume":
        outline = args.outline
        if Path(outline).exists():
            outline = Path(outline).read_text(encoding="utf-8")
        plan_volume(outline, args.volume)

    elif args.command == "expand-node":
        nodes = get_all_nodes()
        target = None
        for n in nodes:
            if n.node_id == args.node_id:
                target = n
                break
        if not target:
            print(f"❌ 节点 {args.node_id} 不存在")
            return
        expand_node(target)

    elif args.command == "generate-volume":
        outline = args.outline
        if Path(outline).exists():
            outline = Path(outline).read_text(encoding="utf-8")
        generate_volume(outline, args.volume)

    elif args.command == "transition-volume":
        outline = args.new_outline
        if Path(outline).exists():
            outline = Path(outline).read_text(encoding="utf-8")
        transition_to_next_volume(args.current_volume, outline, args.new_volume)

    elif args.command == "status":
        plan = load_volume_plan()
        vol_num = plan.get("current_volume", 1)
        vol = plan.get("volumes", {}).get(str(vol_num), {})
        nodes = vol.get("nodes", [])
        print(f"\n第 {vol_num} 卷: {vol.get('volume_title', '')}")
        print(f"预估章节: {vol.get('total_chapters_estimate', '?')}\n")
        for n in nodes:
            status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}.get(
                n["expansion_status"], "❓"
            )
            print(f"  {status_icon} {n['node_id']}: {n['node_title']} "
                  f"(score={n['appeal_score']}, budget={n['chapter_budget']}章) "
                  f"[{n['expansion_status']}]")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
