"""
Streamlit-specific UI helpers for HTML generation, styling, and settings management.

Phase 3: Full Native Alignment
- Avatar loading optimized with @st.cache_resource
- Native Streamlit patterns throughout
- Performance optimizations applied
"""

import base64
from pathlib import Path
from typing import Dict, Any, Optional
import streamlit as st
from config import speaker_config
from utils.logging_config import get_logger
# Audio functions moved to utils/streamlit_audio.py
# Banner functions moved to utils/streamlit_banners.py
# Settings functions moved to utils/streamlit_session.py

logger = get_logger(__name__)

# Module-level cache for avatar paths (final result cache)
# This prevents re-encoding on every call, even though encoding is cached
_AVATAR_PATH_CACHE: Dict[str, str] = {}

@st.cache_resource
def _load_avatar_image(speaker_key: str) -> Optional[bytes]:
    """
    Load avatar image file as bytes (cached with @st.cache_resource).
    
    This is a resource that should be cached across reruns but can be cleared
    if needed. Using @st.cache_resource is appropriate for file I/O operations.
    
    Args:
        speaker_key: Speaker key (host, gpt_a, gpt_b)
    
    Returns:
        Avatar image bytes if found, None otherwise
    """
    avatar_filenames = {
        "host": ["Host.png", "host.png"],
        "gpt_a": ["gpt_a.png", "GPT-A.png"],
        "gpt_b": ["gpt_b.png", "GPT-B.png"]
    }
    
    filenames = avatar_filenames.get(speaker_key, [])
    
    # Check if custom avatar exists in public/avatars/
    for filename in filenames:
        avatar_path = Path("public/avatars") / filename
        if avatar_path.exists():
            try:
                with open(avatar_path, "rb") as img_file:
                    return img_file.read()
            except Exception as e:
                logger.warning(f"Failed to load avatar {avatar_path}: {e}")
                break
    
    return None


@st.cache_data
def _encode_avatar_data_uri(img_data: bytes) -> str:
    """
    Encode avatar image bytes as base64 data URI (cached with @st.cache_data).
    
    This caches the base64 encoding operation which is relatively expensive.
    The image bytes themselves are already cached via @st.cache_resource.
    
    Args:
        img_data: Avatar image bytes
    
    Returns:
        Base64 data URI string
    """
    img_base64 = base64.b64encode(img_data).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"


def get_avatar_path(speaker_key: str) -> str:
    """
    Get the avatar for a speaker, using custom PNG if available, otherwise Material Symbol.
    
    For Streamlit, we encode the image as base64 data URI since Streamlit doesn't
    automatically serve files from public/ directory like Chainlit does.
    
    Uses multiple layers of caching:
    - @st.cache_resource for image file loading (prevents disk I/O on every call)
    - @st.cache_data for base64 encoding (prevents re-encoding on every call)
    - Module-level cache for final result (prevents function call overhead)
    
    This ensures 5-6MB avatar files are only loaded and encoded once, not on every turn.
    
    Args:
        speaker_key: Speaker key (host, gpt_a, gpt_b)
    
    Returns:
        Avatar as base64 data URI string or Material Symbol string
    """
    # Check module-level cache first (fastest - no function call overhead)
    if speaker_key in _AVATAR_PATH_CACHE:
        return _AVATAR_PATH_CACHE[speaker_key]
    
    # Try to load custom avatar (cached image bytes via @st.cache_resource)
    img_data = _load_avatar_image(speaker_key)
    
    if img_data:
        try:
            # Cache the base64 encoding operation (via @st.cache_data)
            avatar_path = _encode_avatar_data_uri(img_data)
            # Store in module-level cache for instant future access
            _AVATAR_PATH_CACHE[speaker_key] = avatar_path
            logger.debug(f"Avatar loaded and cached for {speaker_key} ({len(img_data)} bytes)")
            return avatar_path
        except Exception as e:
            logger.warning(f"Failed to encode avatar for {speaker_key}: {e}")
    
    # Fallback to Material Symbol if custom avatar not found
    fallback_map = {
        "host": ":material/person:",
        "gpt_a": ":material/smart_toy:",
        "gpt_b": ":material/sentiment_satisfied:"
    }
    fallback = fallback_map.get(speaker_key, ":material/help:")
    # Cache fallback too (Material Symbols are lightweight)
    _AVATAR_PATH_CACHE[speaker_key] = fallback
    logger.debug(f"Custom avatar not found for {speaker_key}, using Material Symbol fallback")
    return fallback

# Speaker info for Streamlit UI (extends config with UI-specific fields)
# Enhanced with modern gradients and better color schemes
# Note: avatar paths are resolved at runtime via get_avatar_path()
SPEAKER_INFO = {
    "host": {
        "label": "Host",
        "full_label": "Host (Panagiotis)",
        "icon": ":material/person:",
        "avatar": None,  # Will be set dynamically
        "color": "#10b981",  # Emerald green for accent
        "bubble_bg": "linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%)",  # Vibrant green gradient
        "bubble_bg_fallback": "#10b981",  # Fallback for browsers that don't support gradients
        "text_color": "#ffffff",
        "shadow_color": "rgba(16, 185, 129, 0.4)",
        "border_color": "#34d399",
        "glow_color": "rgba(16, 185, 129, 0.2)"
    },
    "gpt_a": {
        "label": "GPT-A",
        "full_label": "GPT-A (The Analyst)",
        "icon": ":material/psychology:",
        "avatar": None,  # Will be set dynamically
        "color": "#3b82f6",  # Bright blue for accent
        "bubble_bg": "linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #1e40af 100%)",  # Vibrant blue gradient
        "bubble_bg_fallback": "#3b82f6",
        "text_color": "#ffffff",
        "shadow_color": "rgba(59, 130, 246, 0.4)",
        "border_color": "#60a5fa",
        "glow_color": "rgba(59, 130, 246, 0.2)"
    },
    "gpt_b": {
        "label": "GPT-B",
        "full_label": "GPT-B (The Empath)",
        "icon": ":material/favorite:",
        "avatar": None,  # Will be set dynamically
        "color": "#ef4444",  # Bright red for accent
        "bubble_bg": "linear-gradient(135deg, #f87171 0%, #ef4444 50%, #dc2626 100%)",  # Vibrant red gradient
        "bubble_bg_fallback": "#f87171",
        "text_color": "#ffffff",
        "shadow_color": "rgba(239, 68, 68, 0.4)",
        "border_color": "#fca5a5",
        "glow_color": "rgba(239, 68, 68, 0.2)"
    },
}

# Use voice map from config
VOICE_FOR_SPEAKER = speaker_config.VOICE_MAP

# Note: Avatar paths are resolved lazily via get_avatar_path() which uses caching
# We don't initialize them at module load to avoid calling Streamlit functions
# at import time, which is a Streamlit best practice


# ========== CSS & STYLING ==========
# CSS injection is now handled by utils.streamlit_styles
# This import provides inject_custom_css() function


# ========== AUDIO FUNCTIONS ==========
# Audio functions have been moved to utils/streamlit_audio.py
# Import them when needed:
# from utils.streamlit_audio import autoplay_audio, transcribe_streamlit_audio

# ========== BANNER & STATUS ==========
# Banner functions have been moved to utils/streamlit_banners.py
# Import them when needed:
# from utils.streamlit_banners import render_app_banner, render_broadcast_banner

# ========== SETTINGS ==========
# Settings functions have been moved to utils/streamlit_session.py
# Import them when needed:
# from utils.streamlit_session import get_settings


# ========== SIDEBAR COMPONENTS ==========
# Sidebar components have been moved to utils/streamlit_sidebar.py
# Import them when needed:
# from utils.streamlit_sidebar import (
#     render_sidebar_main_controls,
#     render_sidebar_settings,
#     render_sidebar_knowledge_base
# )


# ========== MAIN AREA COMPONENTS ==========
# Banner rendering has been moved to utils/streamlit_banners.py


# Removed render_sticky_controls() - no longer needed
# Knowledge Base is accessible via sidebar "Add Documents" button
# Removed render_generate_topics_button() - replaced by dialog in utils/streamlit_topics.py
# Removed render_topic_suggestions() - replaced by dialog in utils/streamlit_topics.py
# Removed render_text_input() - moved to utils/streamlit_chat_input.py
# Removed render_voice_input() - moved to utils/streamlit_chat_input.py


# ========== MESSAGE RENDERING (DECOUPLED) ==========
# Bubble rendering functions are now in utils.streamlit_bubbles
# Message history orchestration is in utils.streamlit_messages
# Import them at the end to avoid circular imports (after SPEAKER_INFO is defined)
from utils.streamlit_bubbles import (
    render_styled_bubble,
    render_streaming_bubble,
    update_streaming_bubble
)
# Note: render_message_history is imported directly in app.py to avoid circular imports

