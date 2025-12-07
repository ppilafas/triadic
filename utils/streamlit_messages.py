"""
Streamlit Message History Orchestration Module

Orchestrates message history rendering with audio controls and state management.
Bubble rendering logic is decoupled to utils.streamlit_bubbles for better modularity.

This module focuses on:
- Message history orchestration
- Audio controls and TTS generation
- State initialization and management
- Coordination between bubbles, audio, and UI controls
"""

from typing import Dict, Any, List
import streamlit as st
from tts import tts_stream_to_bytes
from utils.streamlit_ui import SPEAKER_INFO, VOICE_FOR_SPEAKER, get_avatar_path
from utils.streamlit_bubbles import (
    render_styled_bubble,
    render_streaming_bubble,
    update_streaming_bubble
)
from utils.logging_config import get_logger

logger = get_logger(__name__)


def _initialize_message_state_keys(messages: List[Dict[str, Any]]) -> None:
    """
    Pre-initialize all message state keys before rendering to prevent flicker.
    
    This ensures state keys exist before render, avoiding conditional initialization
    that can cause visual flicker.
    
    Args:
        messages: List of message dictionaries
    """
    for idx in range(len(messages)):
        message_id = f"msg_{idx}"
        play_state_key = f"play_state_{message_id}"
        generating_key = f"generating_tts_{message_id}"
        
        # Initialize keys if they don't exist (prevents flicker from conditional init)
        if play_state_key not in st.session_state:
            st.session_state[play_state_key] = False
        if generating_key not in st.session_state:
            st.session_state[generating_key] = False


def render_message_history(messages: List[Dict[str, Any]]) -> None:
    """
    Render message history with styled bubbles and audio controls.
    Optimized for performance with cached lookups and fragment isolation.
    
    This function handles bubble mode rendering only.
    For IRC mode, use render_irc_style_history() from utils.streamlit_irc.
    
    Uses @st.fragment to prevent full page reruns, reducing flicker.
    
    Args:
        messages: List of message dictionaries with 'speaker', 'content', etc.
    """
    # Show empty state if no messages
    if not messages:
        st.info("**Start the conversation** by typing a message or selecting a topic.", icon=":material/chat:")
        return
    
    # Pre-initialize all state keys before rendering (prevents flicker)
    _initialize_message_state_keys(messages)
    
    # Pre-compute speaker metadata and avatars (batch lookup optimization)
    speaker_meta_cache: Dict[str, Dict[str, Any]] = {}
    avatar_cache: Dict[str, str] = {}
    for speaker_key in ["host", "gpt_a", "gpt_b"]:
        speaker_meta_cache[speaker_key] = SPEAKER_INFO.get(speaker_key, SPEAKER_INFO["gpt_a"])
        # Batch avatar lookup (cached, but we pre-fetch all at once)
        avatar_cache[speaker_key] = get_avatar_path(speaker_key)
    
    for idx, m in enumerate(messages):
        speaker_key = m["speaker"]
        speaker_meta = speaker_meta_cache.get(speaker_key, speaker_meta_cache["gpt_a"])
        
        role = "user" if speaker_key == "host" else "assistant"
        # Use pre-fetched avatar from cache (optimization: no function call overhead)
        avatar = avatar_cache.get(speaker_key, get_avatar_path(speaker_key))
        
        with st.chat_message(role, avatar=avatar):
            # Pre-compute message-specific keys (optimization: compute once)
            message_id = f"msg_{idx}"
            button_key = f"audio_btn_{message_id}"
            play_state_key = f"play_state_{message_id}"
            generating_key = f"generating_tts_{message_id}"
            
            # Header with speaker label and timestamp
            header_cols = st.columns([3, 1])
            with header_cols[0]:
                st.caption(f"**{speaker_meta['full_label']}**")
            with header_cols[1]:
                timestamp = m.get("timestamp")
                if timestamp:
                    st.caption(f"`{timestamp}`")
            
            # Render message bubble (optimized: single call)
            render_styled_bubble(m["content"], speaker_key)
            
            # Action controls: audio button and character count - render immediately after bubble
            action_cols = st.columns([1, 1, 8])
            with action_cols[0]:
                # Audio button - always render for immediate visibility
                # Use stable key to prevent flicker
                button_clicked = st.button(
                    ":material/volume_up:",
                    key=button_key,
                    help="Generate and play audio"
                )
                if button_clicked:
                    # Check if audio already exists
                    if not m.get("audio_bytes"):
                        # Set flag to generate TTS on next rerun (so we can show spinner)
                        # Don't rerun immediately - let fragment handle it
                        st.session_state[generating_key] = True
                        logger.info(f"TTS generation requested for message {idx}")
                        # Fragment will handle rerun automatically
                    else:
                        # Audio already exists, just mark for playback
                        st.session_state[play_state_key] = True
                        # No rerun needed - fragment will update
            
            with action_cols[1]:
                # Character count
                chars = m.get("chars", 0)
                if chars > 0:
                    st.caption(f":material/analytics: {chars:,}")
            
            # Generate TTS with spinner if flag is set and audio doesn't exist
            # Use fragment-aware rendering to prevent flicker
            is_generating = st.session_state.get(generating_key, False)
            has_audio = bool(m.get("audio_bytes"))
            
            if is_generating and not has_audio:
                # Show spinner in a stable container to prevent flicker
                spinner_container = st.empty()
                with spinner_container.container():
                    with st.spinner("Generating audio..."):
                        try:
                            voice = VOICE_FOR_SPEAKER.get(speaker_key, "alloy")
                            audio_bytes = tts_stream_to_bytes(m["content"], voice=voice)
                            # Store in message for future use
                            st.session_state.show_messages[idx]["audio_bytes"] = audio_bytes
                            logger.info(f"Generated TTS on demand for message {idx}")
                            st.toast("Audio generated!", icon=":material/volume_up:")
                            # Clear generating flag and mark for playback
                            st.session_state[generating_key] = False
                            st.session_state[play_state_key] = True
                            # Clear spinner container
                            spinner_container.empty()
                        except Exception as e:
                            logger.error(f"TTS generation failed: {e}", exc_info=True)
                            st.error(f"Failed to generate audio: {str(e)}", icon=":material/error:")
                            # Clear generating flag on error
                            st.session_state[generating_key] = False
                            spinner_container.empty()
            
            # Show audio player if audio is available and should be played
            # Use stable container to prevent flicker when toggling
            audio_bytes = m.get("audio_bytes")
            should_play = st.session_state.get(play_state_key, False)
            
            # Always render audio container (stable key) to prevent flicker
            audio_container = st.empty()
            if audio_bytes and should_play:
                # Render audio player in stable container
                with audio_container.container():
                    st.markdown('<div class="audio-player-container">', unsafe_allow_html=True)
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                # Reset play flag after rendering (prevents re-triggering)
                st.session_state[play_state_key] = False
            elif audio_bytes:
                # Audio exists but not playing - keep container empty to maintain layout stability
                audio_container.empty()
            else:
                # No audio - keep container empty
                audio_container.empty()

