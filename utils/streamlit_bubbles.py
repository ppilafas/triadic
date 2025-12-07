"""
Streamlit Bubble Rendering Module

Handles all bubble rendering logic including styling, HTML building, and rendering.
Separated from message history orchestration for better modularity.

Optimized for performance with pre-computed style caches and efficient lookups.

Phase 3: Full Native Alignment
- Native Streamlit components enabled by default
- Pre-computed style caches at module load (no runtime computation)
- Optimized feature flag checks (config-first, then session state)
- Hybrid system allows fallback to HTML rendering if needed
"""

from typing import Dict, Any
import streamlit as st
import html
from utils.streamlit_ui import SPEAKER_INFO
from config import ui_config

# ========== PERFORMANCE CACHES ==========

# Cache style attributes per speaker (only 3 speakers, so small cache)
_STYLE_ATTRS_CACHE: Dict[str, Dict[str, str]] = {}

# Cache base styles per speaker (pre-computed for speed)
_BASE_STYLE_CACHE: Dict[str, str] = {}

# Cache streaming base styles (with min-height)
_STREAMING_STYLE_CACHE: Dict[str, str] = {}

# Pre-compute all styles at module load
def _initialize_style_caches() -> None:
    """Pre-compute and cache all bubble styles for performance."""
    for speaker in ["host", "gpt_a", "gpt_b"]:
        meta = SPEAKER_INFO.get(speaker, SPEAKER_INFO["gpt_a"])
        attrs = {
            "bg_gradient": meta["bubble_bg"],
            "bg_fallback": meta.get("bubble_bg_fallback", meta["bubble_bg"]),
            "text_color": meta["text_color"],
            "shadow_color": meta.get("shadow_color", "rgba(0, 0, 0, 0.2)"),
            "border_color": meta.get("border_color", meta["color"]),
            "bubble_class": f"bubble-{speaker}"
        }
        _STYLE_ATTRS_CACHE[speaker] = attrs
        
        # Pre-compute base style
        base_style = f"""
        background: {attrs['bg_gradient']};
        background-color: {attrs['bg_fallback']};
        color: {attrs['text_color']};
        padding: 16px 20px;
        border-radius: 20px;
        margin: 16px 0;
        margin-left: 0;
        margin-right: auto;
        max-width: 100%;
        width: 100%;
        display: block;
        box-shadow: 0 6px 20px {attrs['shadow_color']}, 0 2px 8px rgba(0, 0, 0, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        border: 1.5px solid {attrs['border_color']}60;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        font-size: 15.5px;
        line-height: 1.65;
        word-wrap: break-word;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        backdrop-filter: blur(10px);
        """.strip()
        
        _BASE_STYLE_CACHE[speaker] = base_style
        _STREAMING_STYLE_CACHE[speaker] = base_style.replace("transition:", "min-height: 40px;\n            transition:")

# Initialize caches at module load
_initialize_style_caches()


# ========== BUBBLE STYLING HELPERS ==========

def _get_bubble_style_attrs(speaker: str) -> Dict[str, str]:
    """
    Get bubble styling attributes for a speaker (from pre-computed cache).
    
    Styles are pre-computed at module load time, so we just return from cache.
    No need for Streamlit cache since styles don't change at runtime.
    
    Args:
        speaker: Speaker key (host, gpt_a, gpt_b)
    
    Returns:
        Dictionary of style attributes
    """
    # Styles are pre-computed at module load, direct cache lookup
    return _STYLE_ATTRS_CACHE.get(speaker, _STYLE_ATTRS_CACHE["gpt_a"])


def _get_bubble_base_style(speaker: str, is_streaming: bool = False) -> str:
    """
    Get base inline style for bubble (cached for performance).
    
    Args:
        speaker: Speaker key (host, gpt_a, gpt_b)
        is_streaming: Whether this is a streaming bubble
    
    Returns:
        Inline style string
    """
    if is_streaming:
        return _STREAMING_STYLE_CACHE.get(speaker, _STREAMING_STYLE_CACHE["gpt_a"])
    return _BASE_STYLE_CACHE.get(speaker, _BASE_STYLE_CACHE["gpt_a"])


def _escape_html(text: str) -> str:
    """
    Escape HTML special characters for safe rendering.
    Optimized using html.escape() and manual newline replacement.
    """
    if not text:
        return ""
    # Use html.escape() for &, <, > (faster than multiple .replace() calls)
    escaped = html.escape(text, quote=False)
    # Replace newlines with <br> (html.escape doesn't handle newlines)
    return escaped.replace("\n", "<br>")


# ========== FEATURE FLAG HELPERS ==========

def _should_use_native_rendering() -> bool:
    """
    Check if native rendering should be used.
    
    Optimized: Checks config first (fast, no dict lookup), then session state only if needed.
    Since native is enabled by default, this is usually just a config attribute access.
    
    Returns:
        True if native rendering should be used, False for HTML fallback
    """
    # Check config first (fast, no dict lookup) - native is default
    if ui_config.USE_NATIVE_MESSAGE_BUBBLES:
        return True
    # Only check session state if config is False (allows per-session override)
    return st.session_state.get("use_native_message_bubbles", False)


# ========== HTML BUILDING (FALLBACK PATH) ==========

def _build_bubble_html(
    content: str,
    speaker: str,
    is_streaming: bool = False,
    show_cursor: bool = False
) -> str:
    """
    Build complete bubble HTML with styles (optimized with caching).
    
    Args:
        content: HTML content to display in bubble
        speaker: Speaker key (host, gpt_a, gpt_b)
        is_streaming: Whether this is a streaming bubble
        show_cursor: Whether to show streaming cursor
    
    Returns:
        Complete HTML string with bubble markup and styles
    """
    attrs = _get_bubble_style_attrs(speaker)
    base_style = _get_bubble_base_style(speaker, is_streaming=is_streaming)
    
    cursor_html = '<span class="streaming-cursor">|</span>' if show_cursor else ''
    after_style = f"background: {attrs['bg_gradient']}; background-color: {attrs['bg_fallback']};"
    streaming_class = " streaming-bubble" if is_streaming else ""
    
    # Optimized: Use single f-string for better performance
    bubble_class = attrs["bubble_class"]
    return f'<div class="message-bubble-enhanced {bubble_class}{streaming_class}" style="{base_style}"><div style="position: relative; z-index: 1;">{content}{cursor_html}</div></div><style>.message-bubble-enhanced.{bubble_class}::after {{ {after_style} }}</style>'


# ========== BUBBLE RENDERING ==========

def render_styled_bubble_native(text: str, speaker: str) -> None:
    """
    Render message bubble using native Streamlit components (st.chat_message).
    
    This is the native Streamlit 1.51+ approach that uses st.chat_message()
    with CSS classes for custom styling. Better performance and accessibility.
    
    Note: This function is designed to be called from within st.chat_message() context,
    which is already established in render_message_history(). This function only
    renders the bubble content with proper styling.
    
    Args:
        text: Message text content
        speaker: Speaker key (host, gpt_a, gpt_b)
    """
    # Use native markdown with CSS class for styling
    # The CSS class maintains the visual appearance while using native components
    # This is called from within st.chat_message() context, so we just render the content
    st.markdown(
        f'<div class="bubble-content bubble-{speaker}">{_escape_html(text)}</div>',
        unsafe_allow_html=True
    )


def render_styled_bubble(text: str, speaker: str) -> None:
    """
    Renders a text bubble with speaker-specific background color and modern styling.
    
    Uses feature flag to choose between native Streamlit components or HTML rendering.
    
    Args:
        text: Message text content
        speaker: Speaker key (host, gpt_a, gpt_b)
    """
    if _should_use_native_rendering():
        render_styled_bubble_native(text, speaker)
    else:
        # HTML fallback rendering (for compatibility)
        html_text = _escape_html(text)
        bubble_html = _build_bubble_html(html_text, speaker, is_streaming=False)
        st.markdown(bubble_html, unsafe_allow_html=True)


def render_streaming_bubble_native(speaker: str) -> st.empty:
    """
    Create a placeholder for streaming bubble using native Streamlit components.
    
    Args:
        speaker: Speaker key (host, gpt_a, gpt_b)
    
    Returns:
        st.empty container that can be updated with streaming content
    """
    bubble_container = st.empty()
    # Use native rendering with streaming cursor
    bubble_container.markdown(
        f'<div class="bubble-content bubble-{speaker} streaming-bubble"><span class="streaming-cursor">|</span></div>',
        unsafe_allow_html=True
    )
    return bubble_container


def render_streaming_bubble(speaker: str) -> st.empty:
    """
    Create a placeholder for streaming bubble that can be updated in real-time.
    
    Uses feature flag to choose between native Streamlit components or HTML rendering.
    
    Args:
        speaker: Speaker key (host, gpt_a, gpt_b)
    
    Returns:
        st.empty container that can be updated with streaming content
    """
    if _should_use_native_rendering():
        return render_streaming_bubble_native(speaker)
    else:
        # HTML fallback rendering (for compatibility)
        bubble_container = st.empty()
        bubble_html = _build_bubble_html("", speaker, is_streaming=True, show_cursor=True)
        bubble_container.markdown(bubble_html, unsafe_allow_html=True)
        return bubble_container


def update_streaming_bubble_native(container: st.empty, text: str, speaker: str, show_cursor: bool = True) -> None:
    """
    Update the streaming bubble with new text content using native components.
    
    Args:
        container: st.empty container from render_streaming_bubble
        text: Current text content
        speaker: Speaker key (host, gpt_a, gpt_b)
        show_cursor: Whether to show the streaming cursor
    """
    cursor_html = '<span class="streaming-cursor">|</span>' if show_cursor else ''
    container.markdown(
        f'<div class="bubble-content bubble-{speaker} streaming-bubble">{_escape_html(text)}{cursor_html}</div>',
        unsafe_allow_html=True
    )


def update_streaming_bubble(container: st.empty, text: str, speaker: str, show_cursor: bool = True) -> None:
    """
    Update the streaming bubble with new text content.
    
    Uses feature flag to choose between native Streamlit components or HTML rendering.
    
    Args:
        container: st.empty container from render_streaming_bubble
        text: Current text content
        speaker: Speaker key (host, gpt_a, gpt_b)
        show_cursor: Whether to show the streaming cursor
    """
    if _should_use_native_rendering():
        update_streaming_bubble_native(container, text, speaker, show_cursor)
    else:
        # HTML fallback rendering (for compatibility)
        html_text = _escape_html(text)
        bubble_html = _build_bubble_html(html_text, speaker, is_streaming=True, show_cursor=show_cursor)
        container.markdown(bubble_html, unsafe_allow_html=True)

