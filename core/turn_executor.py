"""
Turn execution logic - Framework-agnostic.

Handles the execution of a single AI turn, including prompt building,
AI generation, and response processing.
"""

import time
from typing import Dict, Any, Optional, Callable, Protocol
from utils.logging_config import get_logger
from core.message_builder import build_prompt_from_messages, build_prompt
from core.conversation import get_next_speaker_key
from config import speaker_config
from exceptions import ModelGenerationError

logger = get_logger(__name__)

# Speaker profiles from config
SPEAKER_PROFILES = speaker_config.PROFILES
VOICE_MAP = speaker_config.VOICE_MAP


class TurnResult:
    """Result of a turn execution."""
    
    def __init__(
        self,
        speaker_key: str,
        content: str,
        audio_bytes: Optional[bytes] = None,
        elapsed_time: float = 0.0,
        error: Optional[Exception] = None
    ):
        self.speaker_key = speaker_key
        self.content = content
        self.audio_bytes = audio_bytes
        self.elapsed_time = elapsed_time
        self.error = error
        self.success = error is None


class TurnExecutor:
    """
    Framework-agnostic turn executor.
    
    Handles turn execution logic that can work with any UI framework
    by using dependency injection for framework-specific operations.
    """
    
    def __init__(
        self,
        call_model_fn: Callable[[str, Dict[str, Any]], str],
        stream_model_fn: Optional[Callable[[str, Dict[str, Any]], str]] = None,
        tts_fn: Optional[Callable[[str, str], bytes]] = None,
    ):
        """
        Initialize turn executor.
        
        Args:
            call_model_fn: Function to call AI model (non-streaming)
            stream_model_fn: Optional function to stream AI model (streaming)
            tts_fn: Optional function to generate TTS audio
        """
        self.call_model = call_model_fn
        self.stream_model = stream_model_fn
        self.tts = tts_fn
    
    def execute_turn(
        self,
        next_speaker: str,
        messages: list,
        settings: Dict[str, Any],
        message_format: str = "streamlit"
    ) -> TurnResult:
        """
        Execute one AI turn.
        
        Args:
            next_speaker: Next speaker key (gpt_a or gpt_b)
            messages: List of message dictionaries
            settings: Settings dictionary with model config, TTS settings, etc.
            message_format: Format of messages ("streamlit" or "chainlit")
        
        Returns:
            TurnResult with turn outcome
        """
        start_time = time.time()
        
        try:
            # Build prompt based on message format
            if message_format == "streamlit":
                prompt = build_prompt_from_messages(next_speaker, messages)
            else:  # chainlit format
                prompt, _ = build_prompt(messages)
            
            speaker_info = SPEAKER_PROFILES.get(next_speaker, SPEAKER_PROFILES["gpt_a"])
            
            logger.info(f"Executing turn for {speaker_info['name']} with model {settings.get('model_name', 'gpt-5-mini')}")
            
            # Generate AI response
            api_config = {
                "model_name": settings.get("model_name", "gpt-5-mini"),
                "reasoning_effort": settings.get("reasoning_effort", "low"),
                "text_verbosity": settings.get("text_verbosity", "medium"),
                "reasoning_summary_enabled": settings.get("reasoning_summary_enabled", False)
            }
            
            if settings.get("stream_enabled", True) and self.stream_model:
                ai_text = self.stream_model(prompt, config=api_config)
            else:
                ai_text = self.call_model(prompt, config=api_config)
            
            logger.info(f"Generated response: {len(ai_text)} characters")
            
            # Generate TTS if enabled
            tts_bytes = None
            if settings.get("tts_enabled", False) and ai_text and self.tts and "(Error" not in ai_text:
                try:
                    voice = VOICE_MAP.get(next_speaker, "alloy")
                    tts_bytes = self.tts(ai_text, voice=voice)
                    logger.info(f"TTS generated: {len(tts_bytes)} bytes")
                except Exception as e:
                    logger.warning(f"TTS generation failed: {e}", exc_info=True)
                    # Continue without audio - don't fail the whole turn
            
            elapsed = time.time() - start_time
            
            return TurnResult(
                speaker_key=next_speaker,
                content=ai_text,
                audio_bytes=tts_bytes,
                elapsed_time=elapsed
            )
            
        except ModelGenerationError as e:
            logger.error(f"Model generation failed: {e}", exc_info=True)
            elapsed = time.time() - start_time
            return TurnResult(
                speaker_key=next_speaker,
                content=f"(Error: {str(e)})",
                elapsed_time=elapsed,
                error=e
            )
        except Exception as e:
            logger.error(f"Unexpected error in turn execution: {e}", exc_info=True)
            elapsed = time.time() - start_time
            return TurnResult(
                speaker_key=next_speaker,
                content="(System Error)",
                elapsed_time=elapsed,
                error=e
            )

