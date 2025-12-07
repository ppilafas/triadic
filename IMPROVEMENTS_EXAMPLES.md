# Implementation Examples

This document shows how to apply the improvements to your existing code.

## Example 1: Using the Config Module

**Before (app_chainlit.py):**
```python
VOICE_MAP = {"gpt_a": "alloy", "gpt_b": "verse"}
# ... later in code ...
wav_buffer = await cl.make_async(create_wav_buffer)(chunks, sample_rate=24000)
```

**After:**
```python
from config import speaker_config, audio_config

# Use centralized config
voice = speaker_config.VOICE_MAP.get(next_speaker_key, "alloy")
wav_buffer = await cl.make_async(create_wav_buffer)(
    chunks, 
    sample_rate=audio_config.SAMPLE_RATE
)
```

## Example 2: Using Logging Instead of Print

**Before (ai_api.py):**
```python
print(f"[RAG] Indexed: {file_name}")
print(f"Failed to index file '{file_name}': {e}")
```

**After:**
```python
from utils.logging_config import get_logger

logger = get_logger(__name__)

# In your function
logger.info(f"[RAG] Indexed: {file_name}")
logger.error(f"Failed to index file '{file_name}': {e}", exc_info=True)
```

## Example 3: Using Custom Exceptions

**Before (ai_api.py):**
```python
except Exception as e:
    print(f"Failed to create vector store: {e}")
    return None
```

**After:**
```python
from exceptions import VectorStoreError

try:
    vs = get_client().vector_stores.create(name="triadic-session-store")
    set_session_val(session_store, "vector_store_id", vs.id)
    return vs.id
except Exception as e:
    logger.error("Failed to create vector store", exc_info=True)
    raise VectorStoreError(f"Could not create vector store: {e}") from e
```

## Example 4: Adding Input Validation

**Before (app_chainlit.py):**
```python
def get_settings():
    defaults = {
        "model_name": "gpt-5-mini", 
        "reasoning_effort": "low",
        # ...
    }
    # No validation
```

**After:**
```python
from utils.validators import validate_model_name, validate_reasoning_effort, validate_auto_delay
from exceptions import ValidationError

def get_settings():
    defaults = {
        "model_name": "gpt-5-mini", 
        "reasoning_effort": "low",
        "auto_delay": 4
    }
    current = cl.user_session.get("settings", {})
    combined = {**defaults, **current}
    
    # Validate settings
    try:
        combined["model_name"] = validate_model_name(combined["model_name"])
        combined["reasoning_effort"] = validate_reasoning_effort(combined["reasoning_effort"])
        combined["auto_delay"] = validate_auto_delay(float(combined.get("auto_delay", 4)))
    except ValidationError as e:
        logger.warning(f"Invalid setting, using default: {e}")
        # Fall back to defaults
    
    return combined
```

## Example 5: Improved Error Handling in execute_turn

**Before:**
```python
except Exception as e:
    import traceback
    error_details = traceback.format_exc()
    await cl.Message(content=f"⚠️ **System Error:** {str(e)}", author="System").send()
    print(f"[ERROR] execute_turn failed: {error_details}")
```

**After:**
```python
from exceptions import ModelGenerationError, TranscriptionError

try:
    # ... existing code ...
except ModelGenerationError as e:
    logger.error("Model generation failed", exc_info=True)
    await cl.Message(
        content=f"⚠️ **AI Generation Error:** {str(e)}\n\nPlease try again or adjust your settings.",
        author="System"
    ).send()
except TranscriptionError as e:
    logger.error("Transcription failed", exc_info=True)
    await cl.Message(
        content=f"⚠️ **Audio Error:** Could not transcribe your voice input. Please try again.",
        author="System"
    ).send()
except Exception as e:
    logger.error("Unexpected error in execute_turn", exc_info=True)
    await cl.Message(
        content=f"⚠️ **System Error:** An unexpected error occurred. Please check the logs.",
        author="System"
    ).send()
finally:
    settings["auto_run"] = False
    cl.user_session.set("settings", settings)
    await refresh_controls()
```

## Example 6: Using System Prompt in Chainlit

**Before (app_chainlit.py):**
```python
async def build_prompt(history):
    script = "You are in a podcast. Transcript so far:\n\n"
    # Hardcoded prompt
```

**After:**
```python
from config import SYSTEM_PROMPT_PATH

def load_system_prompt() -> str:
    """Load system prompt from file."""
    try:
        with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"System prompt not found at {SYSTEM_PROMPT_PATH}, using default")
        return "Participate in a talk show. Be concise."

async def build_prompt(history):
    system_prompt = load_system_prompt()
    script = f"{system_prompt}\n\nTranscript so far:\n\n"
    # ... rest of prompt building
```

## Example 7: Better Type Hints

**Before:**
```python
def get_settings():
    defaults = {
        "model_name": "gpt-5-mini", 
        # ...
    }
    return combined
```

**After:**
```python
from typing import TypedDict, Optional

class SettingsDict(TypedDict, total=False):
    model_name: str
    reasoning_effort: str
    auto_run: bool
    tts_enabled: bool
    auto_delay: float
    vector_store_id: Optional[str]

def get_settings() -> SettingsDict:
    defaults: SettingsDict = {
        "model_name": "gpt-5-mini",
        "reasoning_effort": "low",
        "auto_run": False,
        "tts_enabled": False,
        "auto_delay": 4.0
    }
    # ... rest of function
    return combined
```

## Migration Checklist

- [ ] Replace all `print()` statements with logger calls
- [ ] Extract magic numbers to `config.py`
- [ ] Add type hints to function signatures
- [ ] Replace generic exceptions with custom exceptions
- [ ] Add input validation using validators
- [ ] Use system.txt in Chainlit app
- [ ] Update imports to use new modules
- [ ] Test all functionality after migration

## Next Steps

1. Start with logging (easiest, high impact)
2. Move constants to config.py
3. Add type hints incrementally
4. Replace exceptions gradually
5. Add validation where it matters most

