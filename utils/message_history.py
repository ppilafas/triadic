"""
Message History Management

Handles adding messages to conversation history with duplicate detection
and proper metadata management.
"""

import time
from typing import Dict, Any, Optional, List
import streamlit as st
from utils.logging_config import get_logger

logger = get_logger(__name__)


def add_message_to_history(
    speaker: str,
    content: str,
    audio_bytes: Optional[bytes] = None,
    timestamp: Optional[str] = None
) -> bool:
    """
    Add message to history, returning True if added (not duplicate).
    
    Args:
        speaker: Speaker key (host, gpt_a, gpt_b)
        content: Message content
        audio_bytes: Optional audio data
        timestamp: Optional timestamp (defaults to current time)
    
    Returns:
        True if message was added, False if it was a duplicate
    """
    if not content or content.startswith("(Error"):
        return False
    
    # Check if this message is already in history (by content and speaker)
    message_already_exists = any(
        m.get("speaker") == speaker and m.get("content") == content
        for m in st.session_state.get("show_messages", [])
    )
    
    if message_already_exists:
        logger.debug(f"Duplicate message detected for {speaker}, skipping")
        return False
    
    # Use provided timestamp or generate one
    if timestamp is None:
        timestamp = time.strftime("%H:%M:%S")
    
    # Add message to history
    message = {
        "speaker": speaker,
        "content": content,
        "audio_bytes": audio_bytes,
        "timestamp": timestamp,
        "chars": len(content)
    }
    
    if "show_messages" not in st.session_state:
        st.session_state.show_messages = []
    
    st.session_state.show_messages.append(message)
    logger.debug(f"Added message to history: {speaker} ({len(content)} chars)")
    
    return True


def clear_irc_streaming_container() -> None:
    """
    Clear IRC streaming container to prevent duplicate display.
    
    Should be called after streaming completes and before adding message to history.
    """
    if "irc_streaming_container" in st.session_state:
        streaming_container = st.session_state.get("irc_streaming_container")
        if streaming_container:
            streaming_container.empty()  # Clear streaming display
        del st.session_state.irc_streaming_container
        logger.debug("Cleared IRC streaming container")

