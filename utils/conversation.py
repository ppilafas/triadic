"""
Conversation logic helpers - DEPRECATED.

This module is kept for backward compatibility. All functions have been
moved to the core package. Please update imports to use core modules:

- from core.conversation import get_next_speaker_key, get_next_speaker_display_name, calculate_turn_count
- from core.message_builder import load_system_prompt, build_prompt, build_prompt_from_messages

This module will be removed in a future version.
"""

import warnings
from typing import List, Dict, Tuple

# Re-export from core for backward compatibility
from core.conversation import (
    get_next_speaker_key,
    get_next_speaker_display_name,
    calculate_turn_count,
)
from core.message_builder import (
    load_system_prompt,
    build_prompt,
    build_prompt_from_messages,
)

# Deprecation warning
warnings.warn(
    "utils.conversation is deprecated. Use core.conversation and core.message_builder instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    "get_next_speaker_key",
    "get_next_speaker_display_name",
    "calculate_turn_count",
    "load_system_prompt",
    "build_prompt",
    "build_prompt_from_messages",
]

