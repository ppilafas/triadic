"""
Turn Response Renderer

Handles rendering of AI turn responses based on view mode (IRC vs Bubble).
This module encapsulates all view-mode-specific rendering logic.
"""

import time
from typing import Dict, Any, Optional, Tuple
import streamlit as st
from ai_api import call_model, stream_model_generator, ModelGenerationError
from tts import tts_stream_to_bytes
from utils.streamlit_ui import SPEAKER_INFO, VOICE_FOR_SPEAKER, get_avatar_path
from utils.streamlit_audio import autoplay_audio
from utils.streamlit_bubbles import (
    render_styled_bubble,
    render_streaming_bubble,
    update_streaming_bubble
)
from utils.streamlit_irc import render_irc_streaming_container
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Batch size for streaming updates
BATCH_SIZE = 8


def render_turn_response(
    speaker: str,
    prompt: str,
    api_config: Dict[str, Any],
    view_mode: str,
    settings: Dict[str, Any]
) -> Tuple[str, Optional[bytes]]:
    """
    Render turn response based on view mode.
    
    Args:
        speaker: Speaker key (host, gpt_a, gpt_b)
        prompt: Prompt to send to model
        api_config: API configuration dictionary
        view_mode: View mode ("irc" or "bubbles")
        settings: Settings dictionary
    
    Returns:
        Tuple of (response_text, audio_bytes)
    """
    is_irc_mode = view_mode == "irc"
    
    if is_irc_mode:
        return _render_irc_response(speaker, prompt, api_config, settings)
    else:
        return _render_bubble_response(speaker, prompt, api_config, settings)


def _render_irc_response(
    speaker: str,
    prompt: str,
    api_config: Dict[str, Any],
    settings: Dict[str, Any]
) -> Tuple[str, Optional[bytes]]:
    """Render response in IRC mode."""
    ai_text = ""
    tts_bytes = None
    timestamp = time.strftime("%H:%M:%S")
    
    try:
        if settings["stream_enabled"]:
            # Get or create streaming container
            streaming_container = st.session_state.get("irc_streaming_container")
            if not streaming_container:
                streaming_container = st.empty()
                st.session_state.irc_streaming_container = streaming_container
            
            # Show thinking indicator while waiting for first token
            render_irc_streaming_container(
                messages=[],
                streaming_speaker=speaker,
                streaming_content="",
                streaming_timestamp=timestamp,
                show_cursor=False,
                container=streaming_container,
                is_thinking=True
            )
            
            token_gen = stream_model_generator(prompt, config=api_config)
            
            # Batch updates for better performance
            token_buffer = []
            first_token_received = False
            
            try:
                for token in token_gen:
                    # On first token, switch from thinking indicator to actual content
                    if not first_token_received:
                        first_token_received = True
                        ai_text = token
                        # Immediately show first token to replace thinking indicator
                        render_irc_streaming_container(
                            messages=[],
                            streaming_speaker=speaker,
                            streaming_content=ai_text,
                            streaming_timestamp=timestamp,
                            show_cursor=True,
                            container=streaming_container
                        )
                        continue
                    token_buffer.append(token)
                    # Update IRC streaming display in batches
                    if len(token_buffer) >= BATCH_SIZE:
                        ai_text += ''.join(token_buffer)
                        # Render ONLY streaming line (completed messages already shown)
                        render_irc_streaming_container(
                            messages=[],
                            streaming_speaker=speaker,
                            streaming_content=ai_text,
                            streaming_timestamp=timestamp,
                            show_cursor=True,
                            container=streaming_container
                        )
                        token_buffer = []
                
                # Final update with remaining tokens
                if token_buffer:
                    ai_text += ''.join(token_buffer)
            finally:
                # Final update without cursor (last streaming display)
                if ai_text:
                    render_irc_streaming_container(
                        messages=[],
                        streaming_speaker=speaker,
                        streaming_content=ai_text,
                        streaming_timestamp=timestamp,
                        show_cursor=False,
                        container=streaming_container
                    )
        else:
            # Non-streaming: get full response
            ai_text = call_model(prompt, config=api_config)
        
        logger.info(f"Generated response: {len(ai_text)} characters")
    
    except ModelGenerationError as e:
        logger.error(f"Model generation failed: {e}", exc_info=True)
        ai_text = f"(Error: {str(e)})"
    
    # TTS generation for IRC mode (no UI rendering)
    if settings["tts_enabled"] and ai_text and "(Error" not in ai_text:
        try:
            voice = VOICE_FOR_SPEAKER.get(speaker, "alloy")
            tts_bytes = tts_stream_to_bytes(ai_text, voice=voice)
            logger.info(f"TTS generated: {len(tts_bytes)} bytes")
        except Exception as e:
            logger.error(f"TTS generation failed: {e}", exc_info=True)
    
    return ai_text, tts_bytes


def _render_bubble_response(
    speaker: str,
    prompt: str,
    api_config: Dict[str, Any],
    settings: Dict[str, Any]
) -> Tuple[str, Optional[bytes]]:
    """Render response in bubble mode."""
    speaker_meta = SPEAKER_INFO[speaker]
    avatar = get_avatar_path(speaker)
    role = "user" if speaker == "host" else "assistant"
    
    with st.chat_message(role, avatar=avatar):
        # Show speaker label immediately (before streaming starts)
        header_cols = st.columns([3, 1])
        with header_cols[0]:
            speaker_label = speaker_meta.get("full_label", speaker)
            st.caption(f"**{speaker_label}**")
        with header_cols[1]:
            timestamp = time.strftime("%H:%M:%S")
            st.caption(f"`{timestamp}`")
        
        ai_text = ""
        tts_bytes = None
        
        try:
            if settings["stream_enabled"]:
                # Create streaming bubble container for real-time updates
                bubble_container = render_streaming_bubble(speaker)
                
                # Stream tokens with batched updates for better performance
                token_gen = stream_model_generator(prompt, config=api_config)
                
                # Batch updates for smoother performance
                token_buffer = []
                
                try:
                    for token in token_gen:
                        token_buffer.append(token)
                        # Update bubble in batches for better performance and less flicker
                        if len(token_buffer) >= BATCH_SIZE:
                            ai_text += ''.join(token_buffer)
                            update_streaming_bubble(bubble_container, ai_text, speaker, show_cursor=True)
                            token_buffer = []
                    
                    # Final update with any remaining tokens
                    if token_buffer:
                        ai_text += ''.join(token_buffer)
                finally:
                    # After streaming completes, update bubble one final time without cursor
                    if ai_text:
                        update_streaming_bubble(bubble_container, ai_text, speaker, show_cursor=False)
            else:
                ai_text = call_model(prompt, config=api_config)
                # For non-streaming, render the bubble immediately
                render_styled_bubble(ai_text, speaker)
            
            logger.info(f"Generated response: {len(ai_text)} characters")
        
        except ModelGenerationError as e:
            logger.error(f"Model generation failed: {e}", exc_info=True)
            # Show error directly in styled bubble
            render_styled_bubble(f"**Error:** {str(e)}\n\nPlease try again or adjust your settings.", speaker)
            ai_text = f"(Error: {str(e)})"
        
        # TTS generation (silent, no progress indicators)
        if settings["tts_enabled"] and ai_text and "(Error" not in ai_text:
            try:
                voice = VOICE_FOR_SPEAKER.get(speaker, "alloy")
                tts_bytes = tts_stream_to_bytes(ai_text, voice=voice)
                logger.info(f"TTS generated: {len(tts_bytes)} bytes")
            except Exception as e:
                logger.error(f"TTS generation failed: {e}", exc_info=True)
        
        if tts_bytes:
            st.audio(tts_bytes, format="audio/mp3")
            if settings["tts_autoplay"]:
                autoplay_audio(tts_bytes)
    
    return ai_text, tts_bytes

