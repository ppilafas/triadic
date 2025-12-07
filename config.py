"""
Centralized configuration for Triadic application.
All constants and configuration values should be defined here.
"""
import os
from dataclasses import dataclass
from typing import Optional, Dict, List

@dataclass
class AudioConfig:
    """Audio processing configuration"""
    SAMPLE_RATE: int = 24000
    CHANNELS: int = 1
    SAMPLE_WIDTH: int = 2  # 16-bit audio (2 bytes per sample)
    WAV_FILENAME: str = "audio.wav"

@dataclass
class ModelConfig:
    """AI model configuration"""
    DEFAULT_MODEL: str = "gpt-5-mini"
    DEFAULT_REASONING_EFFORT: str = "low"
    MAX_OUTPUT_TOKENS: int = 4096
    ALLOWED_MODELS: List[str] = None
    ALLOWED_EFFORT_LEVELS: List[str] = None
    
    def __post_init__(self):
        if self.ALLOWED_MODELS is None:
            self.ALLOWED_MODELS = ["gpt-5-mini", "gpt-5-nano", "gpt-5.1"]
        if self.ALLOWED_EFFORT_LEVELS is None:
            self.ALLOWED_EFFORT_LEVELS = ["minimal", "low", "medium", "high"]

@dataclass
class TimingConfig:
    """Timing and delay configuration"""
    DEFAULT_AUTO_DELAY: float = 4.0
    MIN_AUTO_DELAY: float = 2.0
    MAX_AUTO_DELAY: float = 15.0

@dataclass
class UIConfig:
    """UI feature flags and configuration"""
    USE_NATIVE_MESSAGE_BUBBLES: bool = True  # Native Streamlit message bubbles (Phase 3: enabled by default)

@dataclass
class FileConfig:
    """File handling configuration"""
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_MIME_TYPES: List[str] = None
    
    def __post_init__(self):
        if self.ALLOWED_MIME_TYPES is None:
            self.ALLOWED_MIME_TYPES = ["application/pdf", "text/plain", "application/msword"]

@dataclass
class SpeakerConfig:
    """Speaker profiles and voice mapping"""
    PROFILES: Dict[str, Dict[str, str]] = None
    VOICE_MAP: Dict[str, str] = None
    
    def __post_init__(self):
        if self.PROFILES is None:
            self.PROFILES = {
                "host": {"name": "Host", "avatar": "/public/Host.png"},
                "gpt_a": {"name": "GPT-A", "avatar": "/public/GPT-A.png"},
                "gpt_b": {"name": "GPT-B", "avatar": "/public/GPT-B.png"},
            }
        if self.VOICE_MAP is None:
            self.VOICE_MAP = {"gpt_a": "alloy", "gpt_b": "verse"}

# Environment-based configuration
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL: Optional[str] = os.getenv("OPENAI_MODEL")

# System prompt path
SYSTEM_PROMPT_PATH: str = os.path.join(os.path.dirname(__file__), "system.txt")

# Initialize config instances
audio_config = AudioConfig()
model_config = ModelConfig()
timing_config = TimingConfig()
file_config = FileConfig()
speaker_config = SpeakerConfig()
ui_config = UIConfig()

