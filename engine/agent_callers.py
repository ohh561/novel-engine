"""
agent_callers.py — 多 Agent API 调用模块

职责：
  1. Writer: 生成/修改章节正文
  2. Critic: 评审初稿，返回结构化 JSON 评分
  3. Archivist: 从定稿中提取状态变更，返回 JSON 更新指令

所有 Agent 使用 OpenAI 兼容 API（支持 OpenAI / DeepSeek / 本地模型等）。
"""

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI, APITimeoutError, APIError


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

# 从环境变量读取 API 配置
API_KEY = os.environ.get("OPENAI_API_KEY", "")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.environ.get("NOVEL_ENGINE_MODEL", "gpt-4o")

# 超时和重试
API_TIMEOUT = 120  # 秒
MAX_API_RETRIES = 2  # API 调用本身的重试次数


def _get_client() -> OpenAI:
    """创建 OpenAI 客户端。"""
    return OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=API_TIMEOUT)


def _call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 8000,
    json_mode: bool = False,
) -> str:
    """
    底层 LLM 调用封装。带重试和错误处理。

    参数:
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        temperature: 温度
        max_tokens: 最大输出 token
        json_mode: 是否要求 JSON 输出

    返回:
        模型输出文本

    异常:
        RuntimeError: API 调用失败且重试耗尽
    """
    client = _get_client()
    kwargs = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    last_error = None
    for attempt in range(MAX_API_RETRIES + 1):
        try:
            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("模型返回空内容")
            return content.strip()
        except APITimeoutError as e:
            last_error = e
            wait = 2 ** attempt
            print(f"  [api] 超时，{wait}s 后重试 ({attempt+1}/{MAX_API_RETRIES+1})")
            time.sleep(wait)
        except APIError as e:
            last_error = e
            if e.status_code == 429:  # Rate limit
                wait = 5 * (attempt + 1)
                print(f"  [api] 限速，{wait}s 后重试")
                time.sleep(wait)
            else:
                raise RuntimeError(f"API 错误 ({e.status_code}): {e.message}")
        except Exception as e:
            raise RuntimeError(f"API 调用异常: {e}")

    raise RuntimeError(f"API 调用失败，已重试 {MAX_API_RETRIES} 次: {last_error}")


# ---------------------------------------------------------------------------
# JSON 解析辅助
# ---------------------------------------------------------------------------

def _parse_json_response(raw: str) -> dict:
    """
    从模型输出中提取 JSON。

    处理情况：
      1. 纯 JSON → 直接解析
      2. JSON 包在 ```json ... ``` 中 → 提取后解析
      3. JSON 夹在其他文本中 → 尝试找 { ... } 块

    异常:
        ValueError: 无法提取有效 JSON
    """
    # 情况1：直接解析
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 情况2：从代码块中提取
    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 情况3：找最外层的 { ... }
    brace_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法从模型输出中提取 JSON:\n{raw[:500]}...")


# ---------------------------------------------------------------------------
# Agent 调用结果
# ---------------------------------------------------------------------------

@dataclass
class WriterResult:
    text: str  # 正文内容


@dataclass
class CriticResult:
    score: int
    passed: bool
    breakdown: dict
    strengths: list[str]
    red_flags: list[str]
    weaknesses: list[str]
    actionable_feedback: list[str]
    ai_flags: list[str]
    raw_json: dict


@dataclass
class ArchivistResult:
    character_updates: dict
    new_characters: list
    timeline_entry: Optional[dict]
    foreshadowing_changes: list
    combat_log: Optional[dict] = None
    resource_changes: Optional[dict] = None
    raw_json: dict = None


# ---------------------------------------------------------------------------
# Writer Agent
# ---------------------------------------------------------------------------

WRITER_SYSTEM_PROMPT = """你是一个长篇小说的作者。你将收到：
1. 上下文包：故事状态、角色卡片、世界规则、开放伏笔
2. 章节大纲：本章要写的节拍

你的任务：写出 3000-5000 字的章节正文。

核心原则：
- Show, Don't Tell：用感官细节代替抽象描述
- 角色一致性：严格按照角色卡片中的性格、技能、目标写作
- 节奏变化：紧张场景用短句，舒缓场景用长句，不要每段都差不多长
- 闲笔：每章至少一个和情节无关但有味道的细节
- 态度：通过主角的眼睛看世界，不要中立
- 叙事钩子：每章至少一个信息缺口或悬念

禁用词：仿佛、犹如、宛若、一丝、一抹、些许、几分、隐约、缓缓、不禁、微微、轻轻、淡淡、眼中闪过、嘴角勾起、眉头微皱、心中一动、心头一震、心中暗道、不由得、突然、瞬间、不由自主、终于明白了、一切都变了

输出格式：直接输出正文，不要加任何解释。以 # 第X章 {标题} 开头。"""

WRITER_REVISE_SUFFIX = """

---
Critic 的评审反馈如下，请根据这些意见修改你的正文：

{feedback}

---
请输出修改后的完整正文（不要加解释）。"""


def call_writer(context: str, outline: str, revision_feedback: Optional[str] = None) -> WriterResult:
    """
    调用 Writer Agent 生成或修改章节。

    参数:
        context: 上下文包（build_context 的输出）
        outline: 章节大纲
        revision_feedback: 如果是修改轮次，传入 Critic 的反馈

    返回:
        WriterResult 包含生成的正文
    """
    user_prompt = f"## 上下文\n\n{context}\n\n## 章节大纲\n\n{outline}"

    if revision_feedback:
        user_prompt += WRITER_REVISE_SUFFIX.format(feedback=revision_feedback)

    print("  [writer] 生成中..." if not revision_feedback else "  [writer] 修改中...")
    raw = _call_llm(
        system_prompt=WRITER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.8,  # 写作需要一点创造力
        max_tokens=10000,
    )
    print(f"  [writer] 完成，{len(raw)} 字符")
    return WriterResult(text=raw)


# ---------------------------------------------------------------------------
# Critic Agent
# ---------------------------------------------------------------------------

CRITIC_SYSTEM_PROMPT = """你是一个严苛的文学编辑。你将收到：
1. 章节大纲：这章应该写什么
2. 章节草稿：作者写的初稿

你的任务：评估草稿质量，输出 JSON 格式的评审报告。

=== 绝对红线（违反任意一条，score ≤ 5，直接打回重写） ===

红线1：禁用句式依赖
全文严禁出现"不是...而是/是..."来解释角色心理的句式。
例如："不是因为害怕，而是因为警惕"、"不是开心的笑，是那种..."、"不是勇敢，是做不到"
如果角色警惕，请描写他的动作（拔掉网线、屏住呼吸）。禁止用旁白解释内心动机！

红线2：行为连续性与应激反应
当角色遭遇极端惊悚/异常事件时，必须保持高度应激状态。
严禁：发现外星造物后去煮面、洗碗、发呆。全网被封杀后淡定吃面条。
他可以为了掩饰而做动作，但不能真的放松下来。

红线3：戒绝"装逼式冷笑"
永久封禁主角动不动就"笑了一下"的油腻描写。
高智商理智型主角面对巨大危机时，反应应当是极度专注、病态的计算欲、或生理性应激，不是笑。

=== 评估维度（加权） ===

- friction（阻力与压迫感）30%：主角行动是否遭遇真实阻力？敌人是否像NPC？危机是否被轻易化解？
- humanity（人味）20%：角色面临高压时是否有真实生理反应？主角是否像没有感情的机器人？
- dialogue_tension（对话交锋感）20%：对话是否有潜台词和目的冲突？是否在互相试探？
- pacing_visual（节奏与画面感）15%：有没有无聊的地方？句式变化？感官细节？
- character_deai（角色一致性与去AI味）15%：角色言行是否一致？有没有禁用词？

红线规则：
- 红线触发任意一条 → 总分 ≤ 5
- friction < 6 或 humanity < 7 → 总分 ≤ 6

禁用词：仿佛、犹如、宛若、一丝、一抹、些许、几分、隐约、缓缓、不禁、微微、轻轻、淡淡、眼中闪过、嘴角勾起、眉头微皱、心中一动、心头一震、心中暗道、不由得、突然、瞬间、不由自主、终于明白了、一切都变了

总分 = friction×0.30 + humanity×0.20 + dialogue_tension×0.20 + pacing_visual×0.15 + character_deai×0.15

你必须严格输出以下 JSON 格式，不要输出任何其他内容：
{
  "score": 7,
  "breakdown": {
    "friction": 7,
    "humanity": 7,
    "dialogue_tension": 6,
    "pacing_visual": 8,
    "character_deai": 7
  },
  "strengths": ["具体优点1", "具体优点2"],
  "red_flags": ["红线触发描述，无则留空数组"],
  "weaknesses": ["具体问题1", "具体问题2"],
  "actionable_feedback": ["具体修改建议1", "具体修改建议2"],
  "ai_flags": ["第N段'某个词' — 建议替换为xxx"]
}"""


def call_critic(outline: str, draft: str) -> CriticResult:
    """
    调用 Critic Agent 评审初稿。

    参数:
        outline: 章节大纲
        draft: Writer 生成的初稿

    返回:
        CriticResult 包含评分和反馈

    异常:
        ValueError: Critic 返回的 JSON 无法解析
    """
    user_prompt = f"## 章节大纲\n\n{outline}\n\n## 章节草稿\n\n{draft}"

    print("  [critic] 评审中...")
    raw = _call_llm(
        system_prompt=CRITIC_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3,  # 评审需要稳定
        max_tokens=3000,
        json_mode=True,
    )

    try:
        data = _parse_json_response(raw)
    except ValueError as e:
        print(f"  [critic] ⚠️ JSON 解析失败，尝试非 JSON 模式重试")
        # 重试一次，不用 json_mode
        raw = _call_llm(
            system_prompt=CRITIC_SYSTEM_PROMPT + "\n\n请务必输出合法 JSON。",
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=3000,
            json_mode=False,
        )
        data = _parse_json_response(raw)

    score = int(data.get("score", 0))
    result = CriticResult(
        score=score,
        passed=score >= 8,
        breakdown=data.get("breakdown", {}),
        strengths=data.get("strengths", []),
        red_flags=data.get("red_flags", []),
        weaknesses=data.get("weaknesses", []),
        actionable_feedback=data.get("actionable_feedback", []),
        ai_flags=data.get("ai_flags", []),
        raw_json=data,
    )
    print(f"  [critic] 评分: {score}/10 {'✅ 通过' if result.passed else '❌ 需修改'}")
    if result.weaknesses:
        for w in result.weaknesses[:2]:
            print(f"    - {w}")
    return result


# ---------------------------------------------------------------------------
# Archivist Agent
# ---------------------------------------------------------------------------

ARCHIVIST_SYSTEM_PROMPT = """你是一个精确的档案管理员。你将收到：
1. 定稿章节：经过审核的最终文本
2. 当前角色状态：characters.json 的当前数据

你的任务：从定稿中提取叙事状态变更，输出 JSON 更新指令。

提取规则：
- current_status 变化：location, health, equipment, mood, communication
- active_goals 变化：新增、完成、改变
- relationships 变化：新增或改变的关系
- hidden_secrets 变化：暴露或新增的秘密
- last_appeared：更新为当前章节号
- timeline_entry：50-100字摘要 + 3-5个关键事件
- foreshadowing_changes：新增、推进或回收的伏笔

只提取有实际变化的字段。没变的不要写。

你必须输出以下 JSON 格式，不要输出任何其他内容：
{
  "character_updates": {
    "角色id": {
      "current_status": { "仅写变化的字段": "..." },
      "active_goals": ["仅写变化时"],
      "last_appeared": "chNNN"
    }
  },
  "new_characters": [],
  "timeline_entry": {
    "chapter": 6,
    "title": "章节标题",
    "synopsis": "50-100字摘要",
    "key_events": ["事件1", "事件2"],
    "characters_present": ["角色id"]
  },
  "foreshadowing_changes": [
    { "id": "F005", "action": "new", "content": "新伏笔内容" }
  ],
  "current_location": "新的当前位置（如有变化）",
  "combat_log": {
    "engagement": "交战描述（一句话）",
    "earth_forces": { "deployed": "投入兵力", "casualties": "伤亡", "equipment_status": "装备状态" },
    "enemy_forces": { "spotted": "已确认", "estimated": "预估" },
    "outcome": "交战结果"
  },
  "resource_changes": {
    "角色id": { "consumed": ["消耗项"], "gained": ["获得项"], "lost": ["丢失项"] }
  }
}"""


def call_archivist(final_text: str, current_characters: dict) -> ArchivistResult:
    """
    调用 Archivist Agent 提取状态变更。

    参数:
        final_text: 定稿正文
        current_characters: 当前 characters.json 数据

    返回:
        ArchivistResult 包含状态更新指令

    异常:
        ValueError: Archivist 返回的 JSON 无法解析
    """
    # 简化角色数据，只传必要信息
    chars_summary = {}
    for cid, cdata in current_characters.get("characters", {}).items():
        chars_summary[cid] = {
            "name": cdata.get("name"),
            "current_status": cdata.get("current_status"),
            "active_goals": cdata.get("active_goals"),
            "last_appeared": cdata.get("last_appeared"),
        }

    user_prompt = (
        f"## 定稿章节\n\n{final_text}\n\n"
        f"## 当前角色状态\n\n{json.dumps(chars_summary, ensure_ascii=False, indent=2)}"
    )

    print("  [archivist] 提取状态变更中...")
    raw = _call_llm(
        system_prompt=ARCHIVIST_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,  # 档案员需要精确
        max_tokens=3000,
        json_mode=True,
    )

    try:
        data = _parse_json_response(raw)
    except ValueError:
        print("  [archivist] ⚠️ JSON 解析失败，重试...")
        raw = _call_llm(
            system_prompt=ARCHIVIST_SYSTEM_PROMPT + "\n\n请务必输出合法 JSON。",
            user_prompt=user_prompt,
            temperature=0.1,
            max_tokens=3000,
            json_mode=False,
        )
        data = _parse_json_response(raw)

    result = ArchivistResult(
        character_updates=data.get("character_updates", {}),
        new_characters=data.get("new_characters", []),
        timeline_entry=data.get("timeline_entry"),
        foreshadowing_changes=data.get("foreshadowing_changes", []),
        combat_log=data.get("combat_log"),
        resource_changes=data.get("resource_changes"),
        raw_json=data,
    )
    print(f"  [archivist] 完成，{len(result.character_updates)} 个角色更新, "
          f"{len(result.foreshadowing_changes)} 个伏笔变更")
    return result


# ---------------------------------------------------------------------------
# 测试
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== agent_callers 模块测试 ===")
    print(f"API: {BASE_URL}")
    print(f"Model: {MODEL}")
    print(f"Key: {'已设置' if API_KEY else '❌ 未设置 OPENAI_API_KEY'}")

    if not API_KEY:
        print("\n请设置环境变量后重试：")
        print("  export OPENAI_API_KEY='your-key'")
        print("  export OPENAI_BASE_URL='https://api.openai.com/v1'")
        print("  export NOVEL_ENGINE_MODEL='gpt-4o'")
    else:
        # 简单测试 Critic
        try:
            result = call_critic(
                outline="测试大纲：林晨在森林中探索",
                draft="# 测试\n\n林晨走在森林里。树很紫。他觉得很饿。",
            )
            print(f"\n测试结果: {result.raw_json}")
        except Exception as e:
            print(f"测试失败: {e}")
