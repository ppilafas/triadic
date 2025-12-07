# stt.py
# Speech-to-Text Module (Whisper Wrapper)
# Uses 'wave' to construct a chemically pure WAV file from raw chunks.

import io
import wave
from typing import List, Optional
import numpy as np
from openai import OpenAI

# Import our improved modules
from config import audio_config, OPENAI_API_KEY
from exceptions import TranscriptionError
from utils.logging_config import get_logger

# Initialize logging
from utils.logging_config import setup_logging
setup_logging()

# Initialize logger
logger = get_logger(__name__)

# Initialize client once
_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def create_wav_buffer(audio_chunks: List[np.ndarray], sample_rate: Optional[int] = None) -> Optional[io.BytesIO]:
    """
    Constructs a valid WAV file in memory from raw PCM chunks.
    
    Args:
        audio_chunks: List of numpy arrays containing audio data
        sample_rate: Sample rate in Hz (defaults to config value)
    
    Returns:
        BytesIO buffer containing WAV file, or None if no chunks provided
    """
    if not audio_chunks:
        logger.warning("No audio chunks provided")
        return None

    if sample_rate is None:
        sample_rate = audio_config.SAMPLE_RATE

    try:
        # Concatenate all raw chunks
        concatenated = np.concatenate(list(audio_chunks))
        
        # Create in-memory bytes buffer
        wav_buffer = io.BytesIO()
        
        # Write standard WAV headers
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(audio_config.CHANNELS)
            wav_file.setsampwidth(audio_config.SAMPLE_WIDTH)
            wav_file.setframerate(sample_rate) 
            wav_file.writeframes(concatenated.tobytes())
        
        # Reset pointer to start so it can be read
        wav_buffer.seek(0)
        wav_buffer.name = audio_config.WAV_FILENAME
        logger.debug(f"Created WAV buffer: {len(concatenated)} samples at {sample_rate}Hz")
        return wav_buffer
    except Exception as e:
        logger.error(f"Failed to create WAV buffer: {e}", exc_info=True)
        raise TranscriptionError(f"Failed to create WAV buffer: {e}") from e

def transcribe_audio(audio_buffer: io.BytesIO) -> Optional[str]:
    """
    Transcribes a WAV buffer using OpenAI Whisper.
    
    Args:
        audio_buffer: BytesIO buffer containing WAV audio data
    
    Returns:
        Transcribed text or None if transcription fails
    
    Raises:
        TranscriptionError: If transcription fails
    """
    if not _client:
        logger.error("OpenAI client not initialized for transcription")
        raise TranscriptionError("OpenAI client not initialized; missing OPENAI_API_KEY")

    if audio_buffer is None:
        logger.error("No audio buffer provided for transcription")
        raise TranscriptionError("No audio buffer provided")

    try:
        logger.info("Starting audio transcription with Whisper")
        # Send the valid WAV buffer to OpenAI
        transcript = _client.audio.transcriptions.create(
            model="whisper-1",
            file=(audio_config.WAV_FILENAME, audio_buffer, "audio/wav")
        )
        text = transcript.text
        logger.info(f"Transcription successful: {len(text)} characters")
        return text

    except Exception as e:
        logger.error(f"Transcription failed: {e}", exc_info=True)
        raise TranscriptionError(f"Failed to transcribe audio: {e}") from e