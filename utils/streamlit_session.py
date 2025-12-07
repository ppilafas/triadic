"""
Streamlit session state management utilities.

This module provides functions for initializing and managing Streamlit
session state variables.
"""

import time
from typing import Dict, Any
import streamlit as st
from config import model_config, timing_config
from utils.logging_config import get_logger
from utils.streamlit_persistence import restore_session_state, save_session_state
from utils.validators import (
    validate_model_name,
    validate_reasoning_effort,
    validate_auto_delay
)

logger = get_logger(__name__)


def initialize_session_state() -> None:
    """
    Initialize all required session state variables.
    
    Sets up the initial conversation state, speaker rotation, and metrics.
    Should be called once at app startup.
    
    Attempts to restore persisted state from previous session before
    initializing defaults.
    """
    # Try to restore persisted state first
    restore_session_state(merge=True)
    
    # Initialize defaults only if keys don't exist (restore may have set them)
    if "show_messages" not in st.session_state:
        # Start with empty message history - welcome message will be shown as suggestion
        st.session_state.show_messages = []
        st.session_state.next_speaker = "gpt_a"
        st.session_state.total_turns = 0
        st.session_state.last_latency = "0.00s"
        logger.info("Session initialized with defaults")
    else:
        logger.info("Session restored from persisted state")
    
    # Always initialize temporary flags (not persisted, must be reset on each session)
    if "turn_in_progress" not in st.session_state:
        st.session_state.turn_in_progress = False
    if "last_audio_id" not in st.session_state:
        st.session_state.last_audio_id = None
    if "view_mode" not in st.session_state:
        st.session_state.view_mode = "bubbles"  # Default to bubbles view
        st.session_state.summary_history = []  # Initialize summary history


def get_default_settings() -> Dict[str, Any]:
    """
    Get default settings dictionary.
    
    Returns:
        Dictionary of default setting values
    """
    return {
        "tts_enabled": False,
        "tts_autoplay": False,
        "auto_mode": False,
        "auto_delay": timing_config.DEFAULT_AUTO_DELAY,
        "stream_enabled": True,
        "model_name": model_config.DEFAULT_MODEL,
        "reasoning_effort": model_config.DEFAULT_REASONING_EFFORT,
        "text_verbosity": "medium",
        "reasoning_summary_enabled": False,
        "web_search_enabled": True,  # Enable web search tool for the model by default
        "summary_interval": 5,  # Generate conversation summary every N turns
        "irc_font": "Hack"  # Default font for IRC mode
    }


def apply_default_settings() -> None:
    """
    Apply default settings to session state.
    
    Only sets values that don't already exist in session state,
    preserving any user customizations.
    """
    defaults = get_default_settings()
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


@st.cache_data
def _validate_settings(
    model_name: str,
    reasoning_effort: str,
    auto_delay: float
) -> Dict[str, Any]:
    """
    Validate settings values (cached with @st.cache_data).
    
    This caches the validation results to avoid redundant validation operations.
    Cache invalidates when input values change.
    
    Args:
        model_name: Model name to validate
        reasoning_effort: Reasoning effort to validate
        auto_delay: Auto delay to validate
    
    Returns:
        Dictionary of validated settings
    """
    validated = {}
    try:
        validated["model_name"] = validate_model_name(model_name)
        validated["reasoning_effort"] = validate_reasoning_effort(reasoning_effort)
        validated["auto_delay"] = validate_auto_delay(auto_delay)
    except Exception as e:
        logger.warning(f"Invalid setting, using default: {e}")
        # Fall back to defaults
        validated["model_name"] = model_config.DEFAULT_MODEL
        validated["reasoning_effort"] = model_config.DEFAULT_REASONING_EFFORT
        validated["auto_delay"] = timing_config.DEFAULT_AUTO_DELAY
    
    return validated


def get_settings() -> Dict[str, Any]:
    """
    Get and validate settings from Streamlit session state.
    
    Uses @st.cache_data for validation caching (Phase 3 optimization).
    
    Returns:
        Dictionary of validated settings
    """
    defaults = {
        "model_name": model_config.DEFAULT_MODEL,
        "reasoning_effort": model_config.DEFAULT_REASONING_EFFORT,
        "auto_delay": timing_config.DEFAULT_AUTO_DELAY,
        "tts_enabled": False,
        "tts_autoplay": False,
        "auto_mode": False,
        "stream_enabled": True,
        "text_verbosity": "medium",
        "reasoning_summary_enabled": False,
        "web_search_enabled": True  # Enable web search by default
    }
    
    settings = {}
    for key, default in defaults.items():
        settings[key] = st.session_state.get(key, default)
    
    # Validate settings (cached)
    validated = _validate_settings(
        settings["model_name"],
        settings["reasoning_effort"],
        float(settings["auto_delay"])
    )
    
    # Update with validated values
    settings.update(validated)
    
    return settings

