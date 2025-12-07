"""
Chainlit-specific UI helpers for HTML generation and settings management.
"""

import re
from typing import Dict, Any
import chainlit as cl
from config import model_config, timing_config
from utils.logging_config import get_logger
from utils.validators import (
    validate_model_name,
    validate_reasoning_effort,
    validate_auto_delay
)
from exceptions import ValidationError

logger = get_logger(__name__)

# Speaker color mapping for CSS classes
SPEAKER_CSS_CLASSES = {
    "host": "message-host",
    "gpt_a": "message-gpt-a",
    "gpt_b": "message-gpt-b",
    "system": "message-system"
}


def create_styled_message_html(content: str, speaker_key: str) -> str:
    """
    Create HTML for a styled message bubble based on speaker.
    
    Args:
        content: Message content (may contain markdown like **bold**)
        speaker_key: Speaker key (host, gpt_a, gpt_b, system)
    
    Returns:
        HTML string with styled message bubble
    """
    css_class = SPEAKER_CSS_CLASSES.get(speaker_key, "message-system")
    
    # Convert markdown to HTML
    # Replace **text** with <strong>text</strong>
    content_with_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
    
    # Escape HTML but preserve <strong> tags
    parts = re.split(r'(<strong>.*?</strong>)', content_with_html, flags=re.DOTALL)
    escaped_parts = []
    for part in parts:
        if part.startswith('<strong>'):
            escaped_parts.append(part)  # Don't escape strong tags
        else:
            # Escape HTML entities in text content
            escaped_part = part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            escaped_parts.append(escaped_part)
    escaped_content = ''.join(escaped_parts)
    # Convert newlines to <br>
    formatted_content = escaped_content.replace("\n", "<br>")
    
    return f'<div class="{css_class} message-content">{formatted_content}</div>'


def create_on_air_badge(speaker_name: str, effort: str) -> str:
    """
    Create HTML for ON AIR badge with status.
    
    Args:
        speaker_name: Name of the speaker
        effort: Reasoning effort level
    
    Returns:
        HTML string for ON AIR badge
    """
    effort_class = f"status-badge-{effort.lower()}" if effort.lower() in ["low", "medium", "high"] else "status-badge-low"
    return f'''
    <div style="margin: 8px 0;">
        <span class="on-air-badge">🔴 ON AIR</span>
        <span class="status-badge {effort_class}">{speaker_name} • {effort} Effort</span>
    </div>
    '''


def get_settings() -> Dict[str, Any]:
    """
    Retrieves settings and INJECTS the Vector Store ID if present.
    Validates settings and applies defaults.
    
    Returns:
        Dictionary of settings with validated values
    """
    defaults = {
        "model_name": model_config.DEFAULT_MODEL,
        "reasoning_effort": model_config.DEFAULT_REASONING_EFFORT,
        "auto_run": False,
        "tts_enabled": False,
        "auto_delay": timing_config.DEFAULT_AUTO_DELAY
    }
    current = cl.user_session.get("settings", {})
    combined = {**defaults, **current}
    
    # Validate settings
    try:
        combined["model_name"] = validate_model_name(combined["model_name"])
        combined["reasoning_effort"] = validate_reasoning_effort(combined["reasoning_effort"])
        combined["auto_delay"] = validate_auto_delay(float(combined.get("auto_delay", timing_config.DEFAULT_AUTO_DELAY)))
    except ValidationError as e:
        logger.warning(f"Invalid setting, using default: {e}")
        # Fall back to defaults for invalid values
        if "model_name" not in current or current["model_name"] not in model_config.ALLOWED_MODELS:
            combined["model_name"] = defaults["model_name"]
        if "reasoning_effort" not in current or current["reasoning_effort"] not in model_config.ALLOWED_EFFORT_LEVELS:
            combined["reasoning_effort"] = defaults["reasoning_effort"]
        if "auto_delay" not in current:
            combined["auto_delay"] = defaults["auto_delay"]
    
    vs_id = cl.user_session.get("vector_store_id")
    if vs_id:
        combined["vector_store_id"] = vs_id
        
    return combined

