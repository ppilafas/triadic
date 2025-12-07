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
# Priority: session_state > Streamlit secrets > environment variable
def _get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from session state, Streamlit secrets, or environment variable."""
    try:
        import streamlit as st
        from streamlit.errors import StreamlitSecretNotFoundError
        
        # Priority 1: Check session state (user-entered in Settings)
        try:
            if hasattr(st, "session_state") and "openai_api_key" in st.session_state:
                key = st.session_state.get("openai_api_key")
                if key and key.strip():
                    return key.strip()
        except (RuntimeError, AttributeError):
            # Streamlit not in proper context yet
            pass
        
        # Priority 2: Try Streamlit secrets (for Streamlit Cloud)
        try:
            if hasattr(st, "secrets") and st.secrets is not None:
                if "OPENAI_API_KEY" in st.secrets:
                    return st.secrets["OPENAI_API_KEY"]
        except (StreamlitSecretNotFoundError, RuntimeError, AttributeError, KeyError):
            # No secrets file or not in Streamlit context - this is fine
            pass
    except ImportError:
        # Streamlit not available
        pass
    except Exception:
        # Any other error accessing Streamlit - fall through to env var
        pass
    
    # Priority 3: Fallback to environment variable (for local development)
    return os.getenv("OPENAI_API_KEY")

def _get_openai_model() -> Optional[str]:
    """Get OpenAI model from Streamlit secrets or environment variable."""
    try:
        import streamlit as st
        from streamlit.errors import StreamlitSecretNotFoundError
        
        # Try Streamlit secrets first (for Streamlit Cloud)
        try:
            if hasattr(st, "secrets") and st.secrets is not None:
                if "OPENAI_MODEL" in st.secrets:
                    return st.secrets["OPENAI_MODEL"]
        except (StreamlitSecretNotFoundError, RuntimeError, AttributeError, KeyError):
            # No secrets file or not in Streamlit context - this is fine
            pass
    except ImportError:
        # Streamlit not available
        pass
    except Exception:
        # Any other error - fall through to env var
        pass
    
    # Fallback to environment variable (for local development)
    return os.getenv("OPENAI_MODEL")

# Use functions instead of variables to allow dynamic lookup
# This allows session state to override at runtime
def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key dynamically (checks session state, secrets, env)."""
    return _get_openai_api_key()

def get_openai_model() -> Optional[str]:
    """Get OpenAI model dynamically (checks session state, secrets, env)."""
    return _get_openai_model()

# For backward compatibility, create variables that call the functions
# But these will be evaluated at import time, so we'll use the functions directly
OPENAI_API_KEY: Optional[str] = _get_openai_api_key()
OPENAI_MODEL: Optional[str] = _get_openai_model()

# System prompt path
SYSTEM_PROMPT_PATH: str = os.path.join(os.path.dirname(__file__), "system.txt")

# Initialize config instances
audio_config = AudioConfig()
model_config = ModelConfig()
timing_config = TimingConfig()
file_config = FileConfig()
speaker_config = SpeakerConfig()
ui_config = UIConfig()

