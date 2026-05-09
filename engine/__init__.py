"""
Novel Engine v5.0 — 动态有状态多 Agent 写作系统

核心模块：
  - state_manager: 状态管理 + 动态上下文组装
  - agent_callers: Writer / Critic / Archivist API 调用
  - main_orchestrator: 主控调度循环
"""

from engine.main_orchestrator import generate_chapter
from engine.state_manager import build_context, apply_state_updates
from engine.agent_callers import call_writer, call_critic, call_archivist
from engine.macro_director import plan_volume, expand_node, generate_volume, get_next_pending_node

__version__ = "5.1.0"
__all__ = [
    "generate_chapter",
    "build_context",
    "apply_state_updates",
    "call_writer",
    "call_critic",
    "call_archivist",
    "plan_volume",
    "expand_node",
    "generate_volume",
    "get_next_pending_node",
]
