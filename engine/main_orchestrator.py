"""
main_orchestrator.py — 主控调度器

职责：
  实现 generate_chapter() 完整流程：
    1. 读大纲
    2. 构建上下文
    3. Writer 生成初稿
    4. Critic 评审循环（while attempts < 3）
    5. 定稿
    6. Archivist 提取状态变更
    7. 保存正文 + 更新 state_db

用法：
  python -m engine.main_orchestrator --chapter 6
  python -m engine.main_orchestrator --chapter 6 --outline "节拍B6：探索森林..."
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# 模块导入
from engine.state_manager import (
    build_context,
    load_characters,
    load_plot_timeline,
    apply_state_updates,
    save_characters,
    save_plot_timeline,
)
from engine.agent_callers import (
    call_writer,
    call_critic,
    call_archivist,
    CriticResult,
)


# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------

CHAPTERS_DIR = Path(__file__).parent.parent / "chapters"
SUMMARY_DIR = Path(__file__).parent.parent / "summary"
PLOT_DIR = Path(__file__).parent.parent / "plot"


# ---------------------------------------------------------------------------
# 大纲读取
# ---------------------------------------------------------------------------

def read_outline(chapter_number: int) -> str:
    """
    从 plot/ 目录读取对应章节的节拍大纲。

    搜索策略：
      1. 遍历 plot/vol*/act*.md
      2. 找到包含该章节号的节拍
      3. 提取该节拍内容

    如果找不到，返回通用大纲。
    """
    # 简化实现：让用户直接传入大纲，或从文件读取
    # 这里先尝试从 plot 目录的 act 文件中查找
    vol_dirs = sorted(PLOT_DIR.glob("vol*"))

    for vol_dir in vol_dirs:
        act_files = sorted(vol_dir.glob("act*.md"))
        for act_file in act_files:
            try:
                content = act_file.read_text(encoding="utf-8")
                # 简单查找包含章节号的内容
                # 实际使用时建议通过大纲参数传入
                if f"Ch.{chapter_number}" in content or f"ch{chapter_number:03d}" in content:
                    # 提取相关段落（简化版）
                    return content
            except Exception:
                continue

    return f"（未找到第 {chapter_number} 章的详细大纲，请手动提供）"


# ---------------------------------------------------------------------------
# 正文保存
# ---------------------------------------------------------------------------

def save_chapter(chapter_number: int, text: str, volume: int = 1) -> Path:
    """保存正文到 chapters/ 目录。"""
    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"vol{volume}-ch{chapter_number:03d}.md"
    filepath = CHAPTERS_DIR / filename
    filepath.write_text(text, encoding="utf-8")
    print(f"  [save] 正文已保存: {filepath.name} ({len(text)} 字符)")
    return filepath


def save_summary(chapter_number: int, timeline_entry: dict, volume: int = 1) -> Path:
    """保存章节摘要到 summary/ 目录。"""
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"vol{volume}-ch{chapter_number:03d}.md"
    filepath = SUMMARY_DIR / filename

    title = timeline_entry.get("title", f"第{chapter_number}章")
    synopsis = timeline_entry.get("synopsis", "")
    events = timeline_entry.get("key_events", [])
    chars = timeline_entry.get("characters_present", [])

    content = f"# Ch.{chapter_number} {title} — 章节摘要\n\n"
    content += f"## 摘要\n{synopsis}\n\n"
    if events:
        content += f"## 关键事件\n" + "\n".join(f"- {e}" for e in events) + "\n\n"
    if chars:
        content += f"## 出场角色\n" + ", ".join(chars) + "\n"

    filepath.write_text(content, encoding="utf-8")
    print(f"  [save] 摘要已保存: {filepath.name}")
    return filepath


# ---------------------------------------------------------------------------
# 主控循环
# ---------------------------------------------------------------------------

def generate_chapter(
    chapter_number: int,
    outline: Optional[str] = None,
    volume: int = 1,
    max_attempts: int = 3,
    critic_threshold: int = 8,
) -> str:
    """
    生成一章的完整流程。

    参数:
        chapter_number: 章节号
        outline: 章节大纲（可选，不传则从 plot/ 目录读取）
        volume: 卷号（默认 1）
        max_attempts: Critic 最大重试次数
        critic_threshold: Critic 通过阈值

    返回:
        最终定稿文本

    流程:
        1. 准备大纲
        2. 构建上下文（Context Builder）
        3. Writer 生成初稿
        4. Critic 评审循环（while attempts < max_attempts）
        5. 定稿
        6. Archivist 提取状态变更
        7. 应用更新到 state_db
        8. 保存正文和摘要
    """
    start_time = time.time()
    print(f"\n{'='*60}")
    print(f"📖 开始生成第 {chapter_number} 章")
    print(f"{'='*60}")

    # ------------------------------------------------------------------
    # Step 1: 准备大纲
    # ------------------------------------------------------------------
    print(f"\n[Step 1/7] 准备大纲...")
    if outline is None:
        outline = read_outline(chapter_number)
    print(f"  大纲: {outline[:100]}..." if len(outline) > 100 else f"  大纲: {outline}")

    # ------------------------------------------------------------------
    # Step 2: 构建上下文
    # ------------------------------------------------------------------
    print(f"\n[Step 2/7] 构建上下文...")
    try:
        context = build_context(outline)
    except Exception as e:
        print(f"  ❌ 上下文构建失败: {e}")
        raise

    # ------------------------------------------------------------------
    # Step 3: Writer 生成初稿
    # ------------------------------------------------------------------
    print(f"\n[Step 3/7] Writer 生成初稿...")
    try:
        writer_result = call_writer(context, outline)
        draft = writer_result.text
    except Exception as e:
        print(f"  ❌ Writer 调用失败: {e}")
        raise

    # ------------------------------------------------------------------
    # Step 4: Critic 评审循环
    # ------------------------------------------------------------------
    print(f"\n[Step 4/7] Critic 评审循环...")
    attempts = 0
    critique = None
    final_text = draft

    while attempts < max_attempts:
        try:
            critique = call_critic(outline, final_text)
        except Exception as e:
            print(f"  ❌ Critic 调用失败 (attempt {attempts+1}): {e}")
            attempts += 1
            if attempts >= max_attempts:
                print(f"  ⚠️ Critic 多次失败，使用当前版本")
                break
            continue

        if critique.score >= critic_threshold:
            print(f"  ✅ 通过! score={critique.score} >= {critic_threshold}")
            break

        # 未通过，让 Writer 修改
        print(f"  🔄 score={critique.score} < {critic_threshold}，Writer 修改中... "
              f"(attempt {attempts+1}/{max_attempts})")

        feedback_text = "\n".join([
            "## 问题:",
            *[f"- {w}" for w in critique.weaknesses],
            "## 修改建议:",
            *[f"- {f}" for f in critique.actionable_feedback],
        ])

        try:
            writer_result = call_writer(context, outline, revision_feedback=feedback_text)
            final_text = writer_result.text
        except Exception as e:
            print(f"  ❌ Writer 修改失败: {e}")
            # 保持上一版
            break

        attempts += 1

    # 最终检查
    if critique and critique.score < critic_threshold:
        print(f"\n  ⚠️ {max_attempts} 轮后仍未达标 (score={critique.score})，标记为需人工审核")

    # ------------------------------------------------------------------
    # Step 5: 定稿（清理 AI 标记词）
    # ------------------------------------------------------------------
    print(f"\n[Step 5/7] 定稿...")
    if critique and critique.ai_flags:
        for flag in critique.ai_flags:
            print(f"  🏷️ AI标记: {flag}")
    print(f"  正文长度: {len(final_text)} 字符")

    # ------------------------------------------------------------------
    # Step 6: Archivist 提取状态变更
    # ------------------------------------------------------------------
    print(f"\n[Step 6/7] Archivist 提取状态变更...")
    try:
        characters_data = load_characters()
        archivist_result = call_archivist(final_text, characters_data)

        # 构建完整更新包
        updates = {
            "character_updates": archivist_result.character_updates,
            "new_characters": archivist_result.new_characters,
            "timeline_entry": archivist_result.timeline_entry,
            "foreshadowing_changes": archivist_result.foreshadowing_changes,
        }
        if archivist_result.raw_json.get("current_location"):
            updates["current_location"] = archivist_result.raw_json["current_location"]

        # 应用更新
        apply_state_updates(updates)
    except Exception as e:
        print(f"  ❌ Archivist 失败: {e}")
        print(f"  ⚠️ 状态未更新，正文已保存")
        updates = None

    # ------------------------------------------------------------------
    # Step 7: 保存
    # ------------------------------------------------------------------
    print(f"\n[Step 7/7] 保存...")
    try:
        save_chapter(chapter_number, final_text, volume)
        if updates and updates.get("timeline_entry"):
            save_summary(chapter_number, updates["timeline_entry"], volume)
    except Exception as e:
        print(f"  ❌ 保存失败: {e}")
        raise

    # ------------------------------------------------------------------
    # 完成
    # ------------------------------------------------------------------
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"✅ 第 {chapter_number} 章生成完成")
    print(f"   耗时: {elapsed:.1f}s")
    if critique:
        print(f"   评分: {critique.score}/10")
    print(f"   正文: {len(final_text)} 字符")
    print(f"{'='*60}\n")

    return final_text


# ---------------------------------------------------------------------------
# CLI 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Novel Engine — 章节生成器")
    parser.add_argument("--chapter", type=int, required=True, help="章节号")
    parser.add_argument("--volume", type=int, default=1, help="卷号（默认1）")
    parser.add_argument("--outline", type=str, default=None, help="章节大纲（不传则从文件读取）")
    parser.add_argument("--max-attempts", type=int, default=3, help="Critic 最大重试次数")
    parser.add_argument("--threshold", type=int, default=8, help="Critic 通过阈值")

    args = parser.parse_args()

    # 环境检查
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ 请设置环境变量 OPENAI_API_KEY")
        print("   export OPENAI_API_KEY='your-key'")
        print("   export OPENAI_BASE_URL='https://api.openai.com/v1'  (可选)")
        print("   export NOVEL_ENGINE_MODEL='gpt-4o'  (可选)")
        sys.exit(1)

    try:
        final_text = generate_chapter(
            chapter_number=args.chapter,
            outline=args.outline,
            volume=args.volume,
            max_attempts=args.max_attempts,
            critic_threshold=args.threshold,
        )
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 生成失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
