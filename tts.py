# tts.py
# Text-to-Speech Module (OpenAI TTS Wrapper)
from __future__ import annotations
from typing import Optional

from openai import OpenAI

# Import our improved modules
from exceptions import TriadicError
from utils.logging_config import get_logger

# Initialize logging
from utils.logging_config import setup_logging
setup_logging()

# Initialize logger
logger = get_logger(__name__)

__all__ = [
    "tts_synthesize",
    "tts_stream_to_file",
    "tts_stream_to_bytes",
]

def tts_synthesize(
    text: str,
    *,
    voice: str = "alloy",
    speed: float = 1.0,
    fmt: str = "mp3",
    model: str = "gpt-4o-mini-tts",
) -> bytes:
    """
    Synthesize speech from text using OpenAI Audio Speech API.

    Parameters
    ----------
    text : str
        The text to read aloud.
    voice : str
        Supported voices: alloy, ash, ballad, coral, echo, fable, onyx, nova, sage, shimmer, verse.
    speed : float
        Playback speed [0.25, 4.0].
    fmt : str
        Output format: mp3 | wav | flac | opus | aac | pcm.
    model : str
        TTS-capable model (default: gpt-4o-mini-tts).

    Returns
    -------
    bytes
        Audio bytes in the specified format.
    """
    if not text or not text.strip():
        logger.error("Empty text provided for TTS")
        raise ValueError("Empty text for TTS")

    try:
        client = OpenAI()
        kwargs = {"model": model, "voice": voice, "input": text, "speed": speed}
        logger.debug(f"Generating TTS: voice={voice}, model={model}, length={len(text)}")
        try:
            # Some SDK versions accept 'format'; others do not.
            resp = client.audio.speech.create(**kwargs, format=fmt)
        except TypeError:
            # Retry without format if unsupported
            logger.debug("Retrying TTS without format parameter")
            resp = client.audio.speech.create(**kwargs)

        try:
            audio_bytes = resp.read()
            logger.info(f"TTS generation successful: {len(audio_bytes)} bytes")
            return audio_bytes
        except AttributeError:
            audio_bytes = getattr(resp, "content", b"")
            logger.info(f"TTS generation successful (alternative method): {len(audio_bytes)} bytes")
            return audio_bytes
    except Exception as e:
        logger.error(f"TTS generation failed: {e}", exc_info=True)
        raise TriadicError(f"Failed to generate TTS: {e}") from e


def tts_stream_to_file(
    text: str,
    path: str,
    *,
    voice: str = "alloy",
    speed: float = 1.0,
    model: str = "gpt-4o-mini-tts",
) -> None:
    """
    Stream TTS audio directly to a file. Useful for long texts or when you want progressive writes.
    
    Args:
        text: Text to synthesize
        path: Output file path
        voice: Voice to use
        speed: Playback speed
        model: TTS model to use
    
    Raises:
        ValueError: If text is empty
        TriadicError: If TTS generation fails
    """
    if not text or not text.strip():
        logger.error("Empty text provided for TTS file streaming")
        raise ValueError("Empty text for TTS")

    try:
        logger.info(f"Streaming TTS to file: {path}")
        client = OpenAI()
        with client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=text,
            speed=speed,
        ) as response:
            response.stream_to_file(path)
            logger.info(f"TTS file streaming complete: {path}")
    except Exception as e:
        logger.error(f"TTS file streaming failed: {e}", exc_info=True)
        raise TriadicError(f"Failed to stream TTS to file: {e}") from e

def tts_stream_to_bytes(
    text: str,
    *,
    voice: str = "alloy",
    speed: float = 1.0,
    model: str = "gpt-4o-mini-tts",
) -> bytes:
    """
    Stream TTS audio progressively and return as bytes.
    Useful when you want to render the sound in-app after generation.

    Note: Streamlit's st.audio requires full bytes before playback, so this
    still buffers locally — but audio is downloaded progressively.
    
    Args:
        text: Text to synthesize
        voice: Voice to use
        speed: Playback speed
        model: TTS model to use
    
    Returns:
        Audio bytes in the specified format
    
    Raises:
        ValueError: If text is empty
        TriadicError: If TTS generation fails
    """
    if not text or not text.strip():
        logger.error("Empty text provided for TTS byte streaming")
        raise ValueError("Empty text for TTS")

    try:
        logger.debug(f"Streaming TTS to bytes: voice={voice}, model={model}, length={len(text)}")
        client = OpenAI()
        data = bytearray()
        with client.audio.speech.with_streaming_response.create(
            model=model,
            voice=voice,
            input=text,
            speed=speed,
        ) as response:
            for chunk in response.iter_bytes():
                data.extend(chunk)
            audio_bytes = bytes(data)
            logger.info(f"TTS byte streaming complete: {len(audio_bytes)} bytes")
            return audio_bytes
    except Exception as e:
        logger.error(f"TTS byte streaming failed: {e}", exc_info=True)
        raise TriadicError(f"Failed to stream TTS to bytes: {e}") from e