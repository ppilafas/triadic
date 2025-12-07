"""
Streamlit Audio Module

Handles audio-related functionality for Streamlit UI:
- Audio autoplay
- Audio transcription from Streamlit audio_input
"""

import base64
import io
from typing import Optional
import streamlit as st
from stt import transcribe_audio as stt_transcribe_audio
from exceptions import TranscriptionError
from config import audio_config
from utils.logging_config import get_logger

logger = get_logger(__name__)


def autoplay_audio(audio_bytes: bytes) -> None:
    """
    Autoplay audio using HTML5 audio element.
    
    Args:
        audio_bytes: Audio data as bytes
    """
    if not audio_bytes:
        return
    
    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    st.markdown(
        f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
        unsafe_allow_html=True
    )


def transcribe_streamlit_audio(audio_file) -> Optional[str]:
    """
    Transcribe Streamlit audio_input to text.
    
    Args:
        audio_file: Streamlit audio_input file object (BytesIO-like)
    
    Returns:
        Transcribed text or None if transcription fails
    """
    try:
        # Streamlit audio_input provides file-like object with audio data
        # Get the raw bytes
        audio_bytes = audio_file.getvalue()
        
        # Create BytesIO buffer for stt.transcribe_audio
        wav_buffer = io.BytesIO(audio_bytes)
        wav_buffer.name = audio_config.WAV_FILENAME
        
        # Use the shared stt.transcribe_audio function
        text = stt_transcribe_audio(wav_buffer)
        logger.info(f"Transcription successful: {len(text)} characters")
        return text
            
    except TranscriptionError as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        st.error(f"**Transcription Error:** {str(e)}", icon=":material/error:")
        return None
    except Exception as e:
        logger.error(f"Unexpected transcription error: {e}", exc_info=True)
        st.error("**Audio Error:** Failed to transcribe audio. Please try again.", icon=":material/error:")
        return None

