"""
Turn Executor

Core orchestrator for executing AI turns. Handles:
- Vector store management
- Tool detection
- Prompt building
- Response rendering (via turn_renderer)
- Message history management
- Summary generation
- Auto-save
"""

import time
from typing import Dict, Any
import streamlit as st
from ai_api import ensure_vector_store
from core.message_builder import build_prompt_from_messages
from core.conversation import get_next_speaker_key
from services.turn_renderer import render_turn_response
from services.conversation_summarizer import (
    generate_conversation_summary,
    should_generate_summary,
    DEFAULT_SUMMARY_INTERVAL
)
from utils.message_history import add_message_to_history, clear_irc_streaming_container
from utils.streamlit_ui import SPEAKER_INFO
from utils.streamlit_session import get_settings
from utils.streamlit_persistence import auto_save_session_state
from utils.logging_config import get_logger

logger = get_logger(__name__)


def execute_turn() -> None:
    """
    Execute one AI turn with proper error handling and logging.
    
    This is the main orchestrator that:
    1. Sets up vector store and tools
    2. Builds the prompt
    3. Renders the response (IRC or Bubble mode)
    4. Adds message to history
    5. Generates summary if needed
    6. Auto-saves state
    """
    # Check if turn is already in progress
    if st.session_state.get("turn_in_progress", False):
        logger.debug("Turn already in progress, skipping")
        return
    
    # Set turn in progress flag and record start time (for stuck flag detection)
    st.session_state.turn_in_progress = True
    st.session_state._turn_start_time = time.time()
    start_time = st.session_state._turn_start_time
    
    try:
        speaker = st.session_state.next_speaker
        speaker_meta = SPEAKER_INFO[speaker]
        settings = get_settings()
        
        logger.info(f"Executing turn for {speaker} with model {settings['model_name']}")
        
        # Ensure vector store exists (will be created if needed) - must be done before tool detection
        try:
            vs_id = ensure_vector_store(st.session_state)
        except Exception as e:
            logger.warning(f"Vector store not available: {e}")
            vs_id = None
        
        # Determine available tools for prompt enhancement
        available_tools = []
        if vs_id:
            available_tools.append("file_search")
        web_search_enabled = settings.get("web_search_enabled", False)
        logger.info(f"Web search enabled: {web_search_enabled} (from settings: {settings.get('web_search_enabled')}, session_state: {st.session_state.get('web_search_enabled', 'not set')})")
        if web_search_enabled:
            available_tools.append("web_search")
        
        prompt = build_prompt_from_messages(speaker, st.session_state.show_messages, available_tools=available_tools)
        
        # Build config dict for ai_api
        api_config = {
            "model_name": settings["model_name"],
            "reasoning_effort": settings["reasoning_effort"],
            "web_search_enabled": settings.get("web_search_enabled", False),
            "text_verbosity": settings.get("text_verbosity", "medium"),
            "reasoning_summary_enabled": settings.get("reasoning_summary_enabled", False),
            "vector_store_id": vs_id  # Include vector store ID for RAG
        }
        
        # Get view mode
        view_mode = st.session_state.get("view_mode", "irc")
        
        # Render turn response (handles both IRC and Bubble modes)
        ai_text, tts_bytes = render_turn_response(
            speaker=speaker,
            prompt=prompt,
            api_config=api_config,
            view_mode=view_mode,
            settings=settings
        )
        
        elapsed = time.time() - start_time
        st.session_state.last_latency = f"{elapsed:.2f}s"
        st.session_state.total_turns += 1
        
        # Clear streaming container in IRC mode before adding to history (prevents duplicate display)
        if view_mode == "irc":
            clear_irc_streaming_container()
        
        # Add message to history AFTER streaming completes (ensures proper ordering)
        message_added = add_message_to_history(
            speaker=speaker,
            content=ai_text,
            audio_bytes=tts_bytes
        )
        
        # Store flag indicating if message was added (for conditional rerun)
        st.session_state._last_turn_message_added = message_added
        
        # Update next speaker
        st.session_state.next_speaker = get_next_speaker_key(speaker)
        
        logger.info(f"Turn completed: {speaker} responded with {len(ai_text)} characters in {elapsed:.2f}s")
        
        # Generate conversation summary every N turns
        _generate_summary_if_needed(settings)
        
        # Auto-save session state after turn completion
        auto_save_session_state()
    
    except Exception as e:
        logger.error(f"Unexpected error in execute_turn: {e}", exc_info=True)
        st.error("**System Error:** An unexpected error occurred. Please check the logs.", icon=":material/error:")
    finally:
        # Always clear turn in progress flag and start time
        st.session_state.turn_in_progress = False
        if "_turn_start_time" in st.session_state:
            del st.session_state._turn_start_time


def _generate_summary_if_needed(settings: Dict[str, Any]) -> None:
    """
    Generate conversation summary if needed based on turn count.
    
    Args:
        settings: Settings dictionary
    """
    summary_interval = st.session_state.get("summary_interval", DEFAULT_SUMMARY_INTERVAL)
    
    if not should_generate_summary(st.session_state.total_turns, summary_interval):
        return
    
    logger.info(f"Generating conversation summary at turn {st.session_state.total_turns}")
    
    try:
        previous_summary = st.session_state.get("conversation_summary")
        summary_text = generate_conversation_summary(
            messages=st.session_state.show_messages,
            previous_summary=previous_summary,
            model_name=settings.get("model_name", "gpt-5-mini")
        )
        
        # Store latest summary (for backward compatibility with homepage)
        st.session_state.conversation_summary = summary_text
        
        # Store in summary history
        if "summary_history" not in st.session_state:
            st.session_state.summary_history = []
        
        # Calculate turn range for this summary
        summary_interval = st.session_state.get("summary_interval", DEFAULT_SUMMARY_INTERVAL)
        start_turn = max(1, st.session_state.total_turns - summary_interval + 1)
        end_turn = st.session_state.total_turns
        
        summary_entry = {
            "summary_text": summary_text,
            "turn_number": st.session_state.total_turns,
            "timestamp": time.strftime("%H:%M:%S"),
            "message_count": len(st.session_state.show_messages),
            "turn_range": (start_turn, end_turn)
        }
        
        st.session_state.summary_history.append(summary_entry)
        logger.info(f"Conversation summary updated: {len(summary_text)} characters (turn {end_turn})")
    except Exception as e:
        logger.error(f"Failed to generate conversation summary: {e}", exc_info=True)

