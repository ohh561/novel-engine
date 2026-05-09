"""
smoke_test.py — 不需要 API Key 的冒烟测试

验证：
  1. 模块能正常导入
  2. state_manager 能读取 JSON 文件
  3. build_context 能组装上下文
  4. JSON 解析器能处理各种格式
"""

import sys
from pathlib import Path

# 确保能导入 engine 包
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """测试所有模块能正常导入。"""
    print("1. 测试模块导入...")
    try:
        from engine.state_manager import (
            load_characters, load_world_lore, load_plot_timeline,
            build_context, apply_state_updates,
        )
        from engine.agent_callers import (
            call_writer, call_critic, call_archivist,
            _parse_json_response,
            WriterResult, CriticResult, ArchivistResult,
        )
        from engine.main_orchestrator import generate_chapter, save_chapter, save_summary
        print("   ✅ 所有模块导入成功")
    except ImportError as e:
        print(f"   ❌ 导入失败: {e}")
        return False
    return True


def test_state_loading():
    """测试 JSON 状态文件加载。"""
    print("\n2. 测试状态文件加载...")
    try:
        from engine.state_manager import load_characters, load_world_lore, load_plot_timeline

        chars = load_characters()
        assert "characters" in chars, "characters.json 缺少 'characters' 键"
        print(f"   ✅ characters.json: {len(chars['characters'])} 个角色")

        lore = load_world_lore()
        assert "barrier" in lore, "world_lore.json 缺少 'barrier' 键"
        print(f"   ✅ world_lore.json: {len(lore.get('worlds', []))} 个世界")

        timeline = load_plot_timeline()
        assert "recent_chapters" in timeline, "plot_timeline.json 缺少 'recent_chapters' 键"
        print(f"   ✅ plot_timeline.json: {len(timeline['recent_chapters'])} 章记录")

    except Exception as e:
        print(f"   ❌ 加载失败: {e}")
        return False
    return True


def test_build_context():
    """测试上下文组装。"""
    print("\n3. 测试 build_context...")
    try:
        from engine.state_manager import build_context

        outline = """
        节拍 B6：探索森林
        - 发生什么：林晨在紫色森林中探索，发现水源和可食用植物
        - 谁：林晨
        - 在哪：紫色森林
        - 冲突：未知环境的危险
        - 情绪：紧张→好奇
        """

        context = build_context(outline)

        # 基本检查
        assert len(context) > 100, "上下文太短"
        assert "STORY STATE" in context, "缺少 STORY STATE 模块"
        assert "CHARACTER CARDS" in context, "缺少 CHARACTER CARDS 模块"
        assert "WORLD RULES" in context, "缺少 WORLD RULES 模块"
        assert "ACTIVE FORESHADOWING" in context, "缺少 FORESHADOWING 模块"
        assert "林晨" in context, "上下文中应该包含林晨"

        print(f"   ✅ 上下文组装成功: {len(context)} 字符")
        print(f"   包含模块: STORY STATE, CHARACTER CARDS, WORLD RULES, FORESHADOWING")

    except Exception as e:
        print(f"   ❌ 组装失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    return True


def test_json_parser():
    """测试 JSON 解析器处理各种格式。"""
    print("\n4. 测试 JSON 解析器...")
    try:
        from engine.agent_callers import _parse_json_response

        # 纯 JSON
        r1 = _parse_json_response('{"score": 8, "passed": true}')
        assert r1["score"] == 8

        # 带代码块
        r2 = _parse_json_response('```json\n{"score": 7}\n```')
        assert r2["score"] == 7

        # 夹在文本中
        r3 = _parse_json_response('Here is the result:\n{"score": 9}\nDone.')
        assert r3["score"] == 9

        # 无效输入
        try:
            _parse_json_response("no json here at all")
            assert False, "应该抛出 ValueError"
        except ValueError:
            pass

        print("   ✅ JSON 解析器测试全部通过")

    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        return False
    return True


def main():
    print("=" * 60)
    print("Novel Engine v5.0 — 冒烟测试")
    print("=" * 60)

    results = []
    results.append(test_imports())
    results.append(test_state_loading())
    results.append(test_build_context())
    results.append(test_json_parser())

    print(f"\n{'='*60}")
    passed = sum(results)
    total = len(results)
    if all(results):
        print(f"✅ 全部通过 ({passed}/{total})")
    else:
        print(f"❌ 部分失败 ({passed}/{total})")
    print(f"{'='*60}")

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
