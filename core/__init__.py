"""
Core business logic modules - Framework-agnostic.

This package contains the core business logic that is independent
of any UI framework (Streamlit, Chainlit, etc.).
"""

from core.conversation import (
    ConversationState,
    get_next_speaker_key,
    get_next_speaker_display_name,
    calculate_turn_count,
)
from core.message_builder import (
    load_system_prompt,
    build_prompt,
    build_prompt_from_messages,
)
from core.turn_executor import TurnExecutor, TurnResult
from core.session_manager import SessionManager, BaseSessionManager

__all__ = [
    "ConversationState",
    "get_next_speaker_key",
    "get_next_speaker_display_name",
    "calculate_turn_count",
    "load_system_prompt",
    "build_prompt",
    "build_prompt_from_messages",
    "TurnExecutor",
    "TurnResult",
    "SessionManager",
    "BaseSessionManager",
]

