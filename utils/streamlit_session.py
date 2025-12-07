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
        "web_search_enabled": True  # Enable web search tool for the model by default
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

