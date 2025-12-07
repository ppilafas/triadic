"""
Streamlit session state persistence utilities.

This module provides functions to save and restore session state across
browser refreshes using file-based storage (JSON).
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Set, Optional
import streamlit as st
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Storage directory for persisted state
_STORAGE_DIR = Path(".streamlit") / "persisted_state"
_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# State file path - can be per-session or shared
# Note: Currently using single shared file. Set USE_SESSION_SPECIFIC_STORAGE=True for per-user storage
USE_SESSION_SPECIFIC_STORAGE = False  # Set to True for user-specific persistence

def _get_state_file_path() -> Path:
    """
    Get the state file path for the current session.
    
    Returns:
        Path to the state file (session-specific or shared)
    """
    if USE_SESSION_SPECIFIC_STORAGE:
        # Try to get username from authentication first
        username = st.session_state.get("username")
        if username:
            # User-specific storage (when authentication is enabled)
            return _STORAGE_DIR / f"session_state_{username}.json"
        
        # Fallback: Use Streamlit's session ID for user-specific storage
        # Note: Streamlit doesn't expose session ID directly, so we use a workaround
        # We'll use a hash of the session state object ID as a proxy
        try:
            # Try to get a unique identifier for this session
            # This is a workaround since Streamlit doesn't expose session ID directly
            session_hash = hash(id(st.session_state)) % (10 ** 8)  # 8-digit hash
            return _STORAGE_DIR / f"session_state_{session_hash}.json"
        except Exception:
            # Fallback to shared storage if session ID unavailable
            logger.warning("Could not generate session-specific file, using shared storage")
            return _STORAGE_DIR / "session_state.json"
    else:
        # Shared storage (current behavior)
        return _STORAGE_DIR / "session_state.json"

# Keys that should NOT be persisted (temporary/internal state)
_EXCLUDED_KEYS: Set[str] = {
    # Internal Streamlit keys
    "_manual_next",
    "_auto_generate_topics",
    "_selected_topic",
    "pending_turn",
    "turn_in_progress",
    "show_voice_input",
    "knowledge_base_dialog_open",
    "topics_dialog_open",
    # Audio playback state (per-message, regenerated)
    "last_audio_id",
    # Widget state keys (regenerated on each run) - ALL widget keys must be excluded
    "top_auto_mode_toggle",
    "manual_next_button",
    "reboot_button",
    "auto_delay_slider",
    "sidebar_manage_docs",
    "sidebar_add_docs",
    "sidebar_open_topics",
    "model_radio_settings",
    "reasoning_select_settings",
    "verbosity_select_settings",
    "stream_enabled_settings",
    "tts_enabled_settings",
    "tts_autoplay_settings",
    "reasoning_summary_enabled_settings",
    "voice_toggle_button",
    "banner_click_button",
    # Temporary flags
    "_kb_dialog_prev_active",
    "generating_tts_*",  # Pattern - will be checked
    "play_state_*",  # Pattern - will be checked
    "audio_btn_*",  # Pattern - will be checked
}

# Widget key patterns that should be excluded (Streamlit doesn't allow restoring widget values)
_WIDGET_KEY_PATTERNS: Set[str] = {
    "*_button",
    "*_slider",
    "*_select",
    "*_radio",
    "*_toggle",
    "*_checkbox",
    "*_input",
    "*_text_area",
    "*_selectbox",
    "*_multiselect",
    "*_date_input",
    "*_time_input",
    "*_file_uploader",
    "*_color_picker",
    "*_number_input",
    "*_text_input",
    "*_chat_input",
}

# Keys that SHOULD be persisted (important state)
_PERSISTED_KEYS: Set[str] = {
    # Conversation state
    "show_messages",
    "next_speaker",
    "total_turns",
    "last_latency",
    # Settings
    "tts_enabled",
    "tts_autoplay",
    "auto_mode",
    "auto_delay",
    "stream_enabled",
    "model_name",
    "reasoning_effort",
    "text_verbosity",
    "reasoning_summary_enabled",
    "web_search_enabled",
    # Knowledge base
    "vector_store_id",
    "uploaded_file_index",
    "topic_suggestions",
}


def _should_persist_key(key: str) -> bool:
    """
    Determine if a session state key should be persisted.
    
    Args:
        key: Session state key to check
    
    Returns:
        True if key should be persisted, False otherwise
    """
    # Explicit exclusions (highest priority)
    if key in _EXCLUDED_KEYS:
        return False
    
    # Check exclusion patterns (for keys starting with pattern)
    for pattern in _EXCLUDED_KEYS:
        if "*" in pattern:
            prefix = pattern.replace("*", "")
            if key.startswith(prefix):
                return False
    
    # Check widget key patterns (for keys ending with pattern)
    # Widget keys should NEVER be persisted (Streamlit doesn't allow it)
    for pattern in _WIDGET_KEY_PATTERNS:
        pattern_suffix = pattern.replace("*", "")
        if key.endswith(pattern_suffix):
            return False
    
    # Explicit inclusions (override exclusions, but not widget keys)
    # Note: Even if a key is in _PERSISTED_KEYS, if it matches widget pattern, exclude it
    if key in _PERSISTED_KEYS:
        # Double-check it's not a widget key
        is_widget = any(key.endswith(p.replace("*", "")) for p in _WIDGET_KEY_PATTERNS)
        if not is_widget:
            return True
    
    # Exclude keys starting with underscore (internal/temporary)
    if key.startswith("_"):
        return False
    
    # Include other keys that don't match exclusion patterns
    return True


def _serialize_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Serialize session state for storage.
    
    Handles non-serializable types and converts them to JSON-compatible formats.
    
    Args:
        state: Session state dictionary
    
    Returns:
        Serialized state dictionary
    """
    serialized = {}
    for key, value in state.items():
        if not _should_persist_key(key):
            continue
        
        try:
            # Test if value is JSON serializable
            json.dumps(value)
            serialized[key] = value
        except (TypeError, ValueError) as e:
            logger.warning(f"Cannot serialize key '{key}': {e}")
            # Skip non-serializable values (e.g., function objects, file handles)
            continue
    
    return serialized


def _deserialize_state(serialized: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deserialize state from storage.
    
    Args:
        serialized: Serialized state dictionary
    
    Returns:
        Deserialized state dictionary
    """
    # JSON is already deserialized when loaded from file
    return serialized


def save_session_state() -> None:
    """
    Save current session state to persistent storage.
    
    Only saves keys that should be persisted, excluding temporary/internal state.
    Skips saving for guest users (no persistence for guests).
    """
    # Skip persistence for guest users
    if st.session_state.get("is_guest", False):
        logger.debug("Skipping persistence for guest user")
        return
    
    try:
        # Get state file path (session-specific or shared)
        state_file = _get_state_file_path()
        
        # Get all session state
        state_dict = dict(st.session_state)
        
        # Serialize state
        serialized = _serialize_state(state_dict)
        
        # Save to file
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Saved {len(serialized)} session state keys to {state_file}")
    except Exception as e:
        logger.error(f"Failed to save session state: {e}", exc_info=True)


def load_session_state() -> Optional[Dict[str, Any]]:
    """
    Load session state from persistent storage.
    
    Returns:
        Dictionary of restored state, or None if no saved state exists
    """
    try:
        # Get state file path (session-specific or shared)
        state_file = _get_state_file_path()
        
        if not state_file.exists():
            logger.debug(f"No persisted state file found at {state_file}")
            return None
        
        # Load from file
        with open(state_file, "r", encoding="utf-8") as f:
            serialized = json.load(f)
        
        # Deserialize state
        restored = _deserialize_state(serialized)
        
        logger.info(f"Loaded {len(restored)} session state keys from {state_file}")
        return restored
    except Exception as e:
        logger.error(f"Failed to load session state: {e}", exc_info=True)
        return None


def restore_session_state(merge: bool = True) -> None:
    """
    Restore session state from persistent storage.
    
    Args:
        merge: If True, merge with existing state (only restore missing keys).
               If False, overwrite existing state.
    
    Note: Skips restoration for guest users (no persistence for guests).
    """
    # Skip restoration for guest users
    if st.session_state.get("is_guest", False):
        logger.debug("Skipping restoration for guest user")
        return
    
    restored = load_session_state()
    if not restored:
        return
    
    if merge:
        # Only restore keys that don't already exist
        for key, value in restored.items():
            if key not in st.session_state:
                st.session_state[key] = value
                logger.debug(f"Restored session state key: {key}")
    else:
        # Overwrite existing state
        for key, value in restored.items():
            st.session_state[key] = value
            logger.debug(f"Restored session state key: {key}")
    
    logger.info(f"Restored {len(restored)} session state keys")


def clear_persisted_state(clear_all: bool = False) -> None:
    """
    Clear persisted session state from storage.
    
    Args:
        clear_all: If True, clear all session files. If False, clear only current session.
    """
    try:
        if clear_all:
            # Clear all session files
            for state_file in _STORAGE_DIR.glob("session_state*.json"):
                state_file.unlink()
            logger.info("Cleared all persisted session state files")
        else:
            # Clear only current session file
            state_file = _get_state_file_path()
            if state_file.exists():
                state_file.unlink()
                logger.info(f"Cleared persisted session state from {state_file}")
    except Exception as e:
        logger.error(f"Failed to clear persisted state: {e}", exc_info=True)


def auto_save_session_state() -> None:
    """
    Automatically save session state when important keys change.
    
    This should be called periodically or after important state changes.
    """
    # Check if we should auto-save (only if state has changed)
    if "_last_saved_state_hash" not in st.session_state:
        st.session_state._last_saved_state_hash = None
    
    # Create a hash of current state (simple approach)
    current_state = {k: v for k, v in st.session_state.items() if _should_persist_key(k)}
    current_hash = hash(str(sorted(current_state.items())))
    
    # Only save if state has changed
    if st.session_state._last_saved_state_hash != current_hash:
        save_session_state()
        st.session_state._last_saved_state_hash = current_hash

