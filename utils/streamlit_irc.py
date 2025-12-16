"""
Streamlit IRC-Style Message Rendering Module

Handles IRC-style plain text message rendering with color-coded speakers.
Lightweight and optimized for performance - no bubble infrastructure needed.

Supports both static and streaming message rendering.

Format: [timestamp] <speaker> message content [chars]
"""

from typing import Dict, Any, List, Optional
import streamlit as st
import textwrap
import html
from utils.streamlit_ui import SPEAKER_INFO
from utils.logging_config import get_logger

logger = get_logger(__name__)

# IRC line width for wrapping (characters)
# Typical terminal width is 80, but we use 100 for better readability
IRC_LINE_WIDTH = 100

# Speaker color mapping for IRC text
# Header colors (speaker names) - darker, more vibrant
SPEAKER_HEADER_COLORS = {
    "host": "#10b981",      # Emerald green (original darker)
    "gpt_a": "#3b82f6",     # Bright blue (original darker)
    "gpt_b": "#ef4444",     # Bright red (original darker)
}

# Content colors (message text) - lighter for better readability
SPEAKER_TEXT_COLORS = {
    "host": "#6ee7b7",      # Very light emerald green
    "gpt_a": "#93c5fd",     # Very light blue
    "gpt_b": "#fca5a5",     # Very light red/coral
}


def _wrap_irc_line(prefix: str, content: str, suffix: str = "", continuation_indent: int = 4) -> List[str]:
    """
    Wrap a long IRC line at word boundaries with proper indentation.
    
    Args:
        prefix: The IRC prefix (icon, timestamp, speaker) - e.g., "🟢 [12:34:56] <Host>"
        content: The message content to wrap
        suffix: Optional suffix (not used currently)
        continuation_indent: Number of spaces for continuation lines
    
    Returns:
        List of wrapped lines
    """
    # Calculate available width for content
    prefix_len = len(prefix)
    suffix_len = len(suffix) if suffix else 0
    available_width = IRC_LINE_WIDTH - prefix_len - suffix_len - 2  # -2 for safety margin
    
    if available_width < 20:  # Too narrow, use minimum
        available_width = 20
    
    # Wrap content at word boundaries
    wrapped_content = textwrap.wrap(content, width=available_width, break_long_words=True, break_on_hyphens=True)
    
    if not wrapped_content:
        # Empty content, return just prefix + suffix (with space if suffix exists)
        if suffix:
            return [f"{prefix} {suffix}"]
        return [f"{prefix}"]
    
    lines = []
    for i, line in enumerate(wrapped_content):
        if i == 0:
            # First line: prefix + content + suffix
            lines.append(f"{prefix} {line}{suffix}")
        else:
            # Continuation lines: indentation only (cleaner look)
            indent = " " * continuation_indent
            lines.append(f"{indent}{line}")
    
    return lines


def _format_irc_header_html(header_line: str, speaker_key: str) -> str:
    """
    Format the header line (speaker name + timestamp) with color coding.
    Uses darker colors for speaker names to maintain distinction.
    
    Args:
        header_line: Header line text (e.g., "🔵 GPT-A (The Analyst) • 13:28:21")
        speaker_key: Speaker key for color coding
    
    Returns:
        HTML-formatted header line
    """
    import re
    
    # Use darker header colors for speaker names
    speaker_color = SPEAKER_HEADER_COLORS.get(speaker_key, "#cbd5e1")
    
    # Get selected font from settings
    selected_font = st.session_state.get("irc_font", "Hack")
    font_stack = f"'{selected_font}', 'Courier New', monospace"
    
    # Parse header: icon speaker_name • timestamp
    pattern = r'^([🟢🔵🔴⚪])\s+(.+?)\s+•\s+([\d:]+)$'
    match = re.match(pattern, header_line)
    
    if match:
        icon, speaker_name, timestamp = match.groups()
        colored_header = (
            f'{icon} <span style="color: {speaker_color}; font-weight: 600; font-family: {font_stack};">{html.escape(speaker_name)}</span> '
            f'<span style="color: #94a3b8; font-size: 0.85em; font-family: {font_stack};">• {html.escape(timestamp)}</span>'
        )
        return colored_header
    else:
        # Fallback: color the entire header
        escaped = html.escape(header_line)
        return f'<span style="color: {speaker_color}; font-weight: 600; font-family: {font_stack};">{escaped}</span>'


def _format_irc_content_html(content_line: str, speaker_key: str) -> str:
    """
    Format message content line with color coding.
    
    Args:
        content_line: Content line (may be indented)
        speaker_key: Speaker key for color coding
    
    Returns:
        HTML-formatted content line
    """
    speaker_color = SPEAKER_TEXT_COLORS.get(speaker_key, "#cbd5e1")
    
    # Get selected font from settings
    selected_font = st.session_state.get("irc_font", "Hack")
    font_stack = f"'{selected_font}', 'Courier New', monospace"
    
    escaped = html.escape(content_line)
    return f'<span style="color: {speaker_color}; font-family: {font_stack};">{escaped}</span>'


def _format_irc_line_html(line: str, speaker_key: str, is_continuation: bool = False) -> str:
    """
    Format an IRC line with HTML color coding for the speaker and content.
    
    Args:
        line: The IRC line text (may include prefix, content, suffix)
        speaker_key: Speaker key (host, gpt_a, gpt_b) for color coding
        is_continuation: Whether this is a continuation line (indented)
    
    Returns:
        HTML-formatted line with color coding
    """
    import re
    
    # Get speaker color
    speaker_color = SPEAKER_TEXT_COLORS.get(speaker_key, "#cbd5e1")  # Default to gray
    
    # For continuation lines, we just color the content
    if is_continuation:
        # Continuation lines: color the entire indented content
        escaped_line = html.escape(line)
        return f'<span style="color: {speaker_color};">{escaped_line}</span>'
    
    # First line: parse and color speaker label and content separately
    # Format: "🟢 [12:34:56] <Speaker> content"
    # We'll color the speaker label and content, keep timestamp neutral
    
    # Match pattern: icon [timestamp] <speaker> content [suffix]
    # More flexible pattern to handle various formats
    pattern = r'^([🟢🔵🔴⚪])\s*(\[[\d:]+\])\s*(<[^>]+>)\s*(.+?)(\s*\[.*?\])?$'
    match = re.match(pattern, line)
    
    if match:
        icon, timestamp, speaker_label, content, suffix = match.groups()
        suffix = suffix or ""
        
        # Color the icon, speaker label, and content
        colored_line = (
            f'{icon} <span style="color: #94a3b8;">{html.escape(timestamp)}</span> '
            f'<span style="color: {speaker_color}; font-weight: 600;">{html.escape(speaker_label)}</span> '
            f'<span style="color: {speaker_color};">{html.escape(content)}</span>'
            f'{html.escape(suffix)}'
        )
        return colored_line
    else:
        # Fallback: try simpler pattern or color the entire line
        # Check if line contains speaker label pattern
        if '<' in line and '>' in line:
            # Try to split at the speaker label
            parts = re.split(r'(<[^>]+>)', line, maxsplit=1)
            if len(parts) >= 3:
                before_label, speaker_label, after_label = parts[0], parts[1], parts[2]
                colored_line = (
                    f'{html.escape(before_label)}'
                    f'<span style="color: {speaker_color}; font-weight: 600;">{html.escape(speaker_label)}</span>'
                    f'<span style="color: {speaker_color};">{html.escape(after_label)}</span>'
                )
                return colored_line
        
        # Final fallback: color the entire line
        escaped_line = html.escape(line)
        return f'<span style="color: {speaker_color};">{escaped_line}</span>'


def render_irc_style_history(messages: List[Dict[str, Any]]) -> None:
    """
    Render message history in clean IRC-style format with color-coded speakers.
    
    Only renders completed messages. Streaming messages are shown in a separate container
    (render_irc_streaming_container) to avoid duplication.
    
    Uses HTML with color coding for each speaker's text.
    
    Format (more readable):
      🔵 GPT-A (The Analyst) • 13:28:21
        Message content here that wraps nicely...
    
    Args:
        messages: List of completed message dictionaries with 'speaker', 'content', etc.
    """
    if not messages:
        st.info("**Start the conversation** by typing a message or selecting a topic.", icon=":material/chat:")
        return
    
    # Build IRC-style text output with color coding
    # Note: Streaming messages are shown in a separate container (render_irc_streaming_container)
    # to avoid duplication with completed messages
    irc_lines_html = []
    speaker_colors = {
        "host": "🟢",
        "gpt_a": "🔵", 
        "gpt_b": "🔴"
    }
    
    for idx, m in enumerate(messages):
        speaker_key = m.get("speaker", "unknown")
        speaker_meta = SPEAKER_INFO.get(speaker_key, SPEAKER_INFO.get("gpt_a", {}))
        timestamp = m.get("timestamp", "00:00:00")
        content = m.get("content", "").strip()
        
        # More readable format: Header line with speaker info, then content on next lines
        speaker_label = speaker_meta.get("short_label") or speaker_meta.get("full_label") or speaker_key.upper()
        color_icon = speaker_colors.get(speaker_key, "⚪")
        
        # Header line: Icon + Speaker Name + Timestamp (more readable format)
        header_line = f"{color_icon} {speaker_label} • {timestamp}"
        header_html = _format_irc_header_html(header_line, speaker_key)
        
        # Content lines: Wrap message content with indentation
        # Use 2 spaces indentation for content (cleaner than 4)
        content_indent = 2
        wrapped_content = textwrap.wrap(content, width=IRC_LINE_WIDTH - content_indent, 
                                       break_long_words=True, break_on_hyphens=True)
        
        content_lines_html = []
        for line in wrapped_content:
            if line:  # Only add non-empty lines
                indented_line = " " * content_indent + line
                content_lines_html.append(_format_irc_content_html(indented_line, speaker_key))
        
        # Wrap each message in a div with margin-bottom for spacing
        # This ensures spacing is preserved even after reruns (more reliable than empty strings)
        message_html = "\n".join([header_html] + content_lines_html)
        # Add margin-bottom to create spacing between messages (except last one)
        margin_bottom = "0.5em" if idx < len(messages) - 1 else "0"
        irc_lines_html.append(f'<div style="margin-bottom: {margin_bottom};">{message_html}</div>')
    
    # Combine all HTML lines (each message is wrapped in a div with spacing)
    # Divs with margin-bottom provide reliable spacing that persists through reruns
    irc_html = "\n".join(irc_lines_html) if irc_lines_html else ""
    
    if irc_html:
        # Get selected font from settings (default to Hack for cyberpunk aesthetic)
        selected_font = st.session_state.get("irc_font", "Hack")
        # Create font stack with fallbacks
        font_stack = f"'{selected_font}', 'Courier New', monospace"
        
        # Use <pre> tag for monospace font and preserve formatting
        # Each message is wrapped in a div with margin-bottom for consistent spacing
        # This approach is more reliable than empty strings for preserving spacing through reruns
        # Font is applied directly to each span element, so we just need it on the pre as fallback
        html_output = f"""<pre style="font-family: {font_stack}; font-size: 0.9rem; line-height: 1.6; background-color: transparent; color: #f1f5f9; white-space: pre-wrap; word-wrap: break-word; margin: 0; padding: 0;">{irc_html}</pre>"""
        st.markdown(html_output, unsafe_allow_html=True)


def render_irc_streaming_line(speaker: str, timestamp: str, content: str, show_cursor: bool = True) -> str:
    """
    Render a single IRC-style line for streaming display.
    
    Note: This function is used for simple cases. For wrapped lines, use _wrap_irc_line directly.
    
    Args:
        speaker: Speaker key (host, gpt_a, gpt_b)
        timestamp: Timestamp string (HH:MM:SS)
        content: Message content (may be partial during streaming)
        show_cursor: Whether to show streaming cursor
    
    Returns:
        Formatted IRC line string
    """
    speaker_colors = {
        "host": "🟢",
        "gpt_a": "🔵", 
        "gpt_b": "🔴"
    }
    
    speaker_meta = SPEAKER_INFO.get(speaker, SPEAKER_INFO.get("gpt_a", {}))
    speaker_label = speaker_meta.get("short_label") or speaker_meta.get("full_label") or speaker.upper()
    color_icon = speaker_colors.get(speaker, "⚪")
    
    cursor = "|" if show_cursor else ""
    return f"{color_icon} [{timestamp}] <{speaker_label}> {content}{cursor}"


def render_irc_thinking_indicator(streaming_speaker: str, streaming_timestamp: str, 
                                  container: Optional[st.empty] = None) -> None:
    """
    Render a blinking "thinking" indicator while waiting for the model to start generating.
    
    Args:
        streaming_speaker: Speaker key for the message being generated
        streaming_timestamp: Timestamp for the message
        container: Optional existing container to update (if None, uses session state)
    """
    # Use provided container or get from session state
    if container is None:
        container = st.session_state.get("irc_streaming_container")
        if container is None:
            return  # No container available, skip rendering
    
    speaker_colors = {
        "host": "🟢",
        "gpt_a": "🔵", 
        "gpt_b": "🔴"
    }
    speaker_meta = SPEAKER_INFO.get(streaming_speaker, SPEAKER_INFO.get("gpt_a", {}))
    speaker_label = speaker_meta.get("short_label") or speaker_meta.get("full_label") or streaming_speaker.upper()
    color_icon = speaker_colors.get(streaming_speaker, "⚪")
    
    # Header line: Icon + Speaker Name + Timestamp
    header_line = f"{color_icon} {speaker_label} • {streaming_timestamp}"
    
    # Get selected font from settings
    selected_font = st.session_state.get("irc_font", "Hack")
    font_stack = f"'{selected_font}', 'Courier New', monospace"
    
    # Thinking indicator with blinking animation
    # Format matches IRC style: header + indented content
    thinking_text = "thinking..."
    content_indent = 2
    indented_thinking = " " * content_indent + thinking_text
    
    thinking_html = f"""
    <pre style="font-family: {font_stack}; font-size: 0.9rem; line-height: 1.6; background-color: transparent; color: #f1f5f9; white-space: pre-wrap; word-wrap: break-word; margin: 0; padding: 0;">
    {_format_irc_header_html(header_line, streaming_speaker)}
    <span style="color: {SPEAKER_TEXT_COLORS.get(streaming_speaker, '#cbd5e1')}; font-family: {font_stack};">
      <span class="irc-thinking-blink">{html.escape(indented_thinking)}</span>
    </span>
    </pre>
    <style>
    @keyframes irc-blink {{
        0%, 50% {{ opacity: 1; }}
        51%, 100% {{ opacity: 0.3; }}
    }}
    .irc-thinking-blink {{
        animation: irc-blink 1.5s ease-in-out infinite;
    }}
    </style>
    """
    
    container.markdown(thinking_html, unsafe_allow_html=True)


def render_irc_streaming_container(messages: List[Dict[str, Any]], streaming_speaker: Optional[str] = None, 
                                   streaming_content: str = "", streaming_timestamp: str = "", 
                                   show_cursor: bool = True, container: Optional[st.empty] = None,
                                   is_thinking: bool = False) -> None:
    """
    Render ONLY the streaming message line in a container with color coding.
    
    Note: Completed messages are already rendered by render_irc_style_history().
    This function only shows the currently streaming message to avoid duplicates.
    
    Args:
        messages: List of completed message dictionaries (used for reference, not rendered)
        streaming_speaker: Optional speaker key for currently streaming message
        streaming_content: Current content of streaming message
        streaming_timestamp: Timestamp for streaming message
        show_cursor: Whether to show streaming cursor
        container: Optional existing container to update (if None, uses session state)
        is_thinking: If True, show thinking indicator instead of content
    """
    # Use provided container or get from session state
    if container is None:
        container = st.session_state.get("irc_streaming_container")
        if container is None:
            return  # No container available, skip rendering
    
    # Show thinking indicator if requested
    if is_thinking and streaming_speaker:
        render_irc_thinking_indicator(streaming_speaker, streaming_timestamp, container)
        return
    
    # Only render streaming line if active (don't duplicate completed messages)
    if streaming_speaker and streaming_content:
        # Use new readable format: header + content lines
        speaker_colors = {
            "host": "🟢",
            "gpt_a": "🔵", 
            "gpt_b": "🔴"
        }
        speaker_meta = SPEAKER_INFO.get(streaming_speaker, SPEAKER_INFO.get("gpt_a", {}))
        speaker_label = speaker_meta.get("short_label") or speaker_meta.get("full_label") or streaming_speaker.upper()
        color_icon = speaker_colors.get(streaming_speaker, "⚪")
        
        # Header line: Icon + Speaker Name + Timestamp
        header_line = f"{color_icon} {speaker_label} • {streaming_timestamp}"
        irc_lines_html = [_format_irc_header_html(header_line, streaming_speaker)]
        
        # Content lines: Wrap message content with indentation
        content_indent = 2
        cursor = "|" if show_cursor else ""
        content_with_cursor = streaming_content + cursor
        
        wrapped_content = textwrap.wrap(content_with_cursor, width=IRC_LINE_WIDTH - content_indent,
                                       break_long_words=True, break_on_hyphens=True)
        
        for line in wrapped_content:
            if line:  # Only add non-empty lines
                indented_line = " " * content_indent + line
                irc_lines_html.append(_format_irc_content_html(indented_line, streaming_speaker))
        
        irc_html = "\n".join(irc_lines_html)
        
        # Get selected font from settings (default to Hack for cyberpunk aesthetic)
        selected_font = st.session_state.get("irc_font", "Hack")
        # Create font stack with fallbacks
        font_stack = f"'{selected_font}', 'Courier New', monospace"
        
        # Use <pre> tag for monospace font and preserve formatting
        # Font is applied directly to each span element, so we just need it on the pre as fallback
        html_output = f"""
        <pre style="font-family: {font_stack}; font-size: 0.9rem; line-height: 1.6; 
                    background-color: transparent; color: #f1f5f9; white-space: pre-wrap; 
                    word-wrap: break-word; margin: 0; padding: 0;">
        {irc_html}
        </pre>
        """
        
        with container.container():
            st.markdown(html_output, unsafe_allow_html=True)
    else:
        # No streaming active, clear container to avoid showing stale content
        container.empty()
    
    return container

