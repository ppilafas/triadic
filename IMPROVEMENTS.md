# Code Improvement Suggestions

## 🎯 High Priority Improvements

### 1. **Type Hints & Type Safety**
**Current Issue:** Missing type hints makes code harder to maintain and IDE support limited.

**Recommendations:**
- Add type hints to all function signatures
- Use `TypedDict` for configuration dictionaries
- Add return type annotations

**Example:**
```python
from typing import TypedDict, Optional, List, Dict

class SettingsDict(TypedDict, total=False):
    model_name: str
    reasoning_effort: str
    auto_run: bool
    tts_enabled: bool
    auto_delay: float
    vector_store_id: Optional[str]

async def build_prompt(history: List[Dict[str, str]]) -> tuple[str, str]:
    ...
```

### 2. **Centralized Configuration**
**Current Issue:** Magic numbers and strings scattered throughout code (e.g., `24000`, `"gpt-5-mini"`, `4096`).

**Recommendations:**
- Create `config.py` module with all constants
- Use environment variables for configuration
- Support configuration files (YAML/TOML)

**Example:**
```python
# config.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class AppConfig:
    # Audio
    AUDIO_SAMPLE_RATE: int = 24000
    AUDIO_CHANNELS: int = 1
    AUDIO_SAMPLE_WIDTH: int = 2
    
    # Models
    DEFAULT_MODEL: str = "gpt-5-mini"
    DEFAULT_REASONING_EFFORT: str = "low"
    MAX_OUTPUT_TOKENS: int = 4096
    
    # Timing
    DEFAULT_AUTO_DELAY: float = 4.0
    MIN_AUTO_DELAY: float = 2.0
    MAX_AUTO_DELAY: float = 15.0
    
    # API
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: Optional[str] = None
```

### 3. **Proper Logging Instead of Print**
**Current Issue:** Using `print()` statements for logging makes debugging difficult in production.

**Recommendations:**
- Use Python's `logging` module
- Configure log levels (DEBUG, INFO, WARNING, ERROR)
- Add structured logging with context

**Example:**
```python
import logging
from logging import Logger

logger = logging.getLogger(__name__)

# In ai_api.py
logger.info(f"[RAG] Indexed: {file_name}")
logger.error(f"Failed to index file '{file_name}': {e}", exc_info=True)
```

### 4. **Error Handling & Custom Exceptions**
**Current Issue:** Generic exception handling makes debugging difficult.

**Recommendations:**
- Create custom exception classes
- Add specific error handling for different failure modes
- Implement retry logic with exponential backoff for API calls

**Example:**
```python
class TriadicError(Exception):
    """Base exception for Triadic app"""
    pass

class VectorStoreError(TriadicError):
    """Error creating or accessing vector store"""
    pass

class TranscriptionError(TriadicError):
    """Error during audio transcription"""
    pass

class ModelGenerationError(TriadicError):
    """Error during model response generation"""
    pass
```

### 5. **Retry Logic for API Calls**
**Current Issue:** No retry mechanism for transient API failures.

**Recommendations:**
- Add exponential backoff retry decorator
- Handle rate limits gracefully
- Add circuit breaker pattern for repeated failures

**Example:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def call_model_with_retry(prompt_text: str, config: dict = None) -> str:
    return call_model(prompt_text, config)
```

## 🔧 Medium Priority Improvements

### 6. **Input Validation & Sanitization**
**Current Issue:** Limited validation of user inputs and configuration values.

**Recommendations:**
- Validate model names against allowed list
- Validate reasoning effort values
- Sanitize file names before indexing
- Check file sizes before processing

**Example:**
```python
ALLOWED_MODELS = ["gpt-5-mini", "gpt-5-nano", "gpt-5.1"]
ALLOWED_EFFORT_LEVELS = ["minimal", "low", "medium", "high"]
MAX_FILE_SIZE_MB = 100

def validate_model_name(model: str) -> str:
    if model not in ALLOWED_MODELS:
        raise ValueError(f"Invalid model: {model}. Must be one of {ALLOWED_MODELS}")
    return model
```

### 7. **Code Organization & Separation of Concerns**
**Current Issue:** Some functions do multiple things (e.g., `execute_turn` handles UI, API calls, and state management).

**Recommendations:**
- Separate business logic from UI logic
- Create service classes for different domains (AudioService, ModelService, etc.)
- Use dependency injection for better testability

**Example Structure:**
```
triadic/
├── config.py          # Configuration
├── exceptions.py       # Custom exceptions
├── services/
│   ├── audio_service.py
│   ├── model_service.py
│   └── vector_store_service.py
├── ui/
│   ├── chainlit_app.py
│   └── streamlit_app.py
└── utils/
    ├── logging_config.py
    └── validators.py
```

### 8. **Async/Await Improvements**
**Current Issue:** Some blocking operations in async context (partially fixed, but can be improved).

**Recommendations:**
- Make `index_uploaded_files` truly async
- Use async file I/O where possible
- Consider using `aiofiles` for async file operations

**Example:**
```python
import aiofiles
from asyncio import to_thread

async def index_uploaded_files_async(uploaded_files: List, session_store: dict = None) -> None:
    # Run blocking I/O in thread pool
    await to_thread(index_uploaded_files, uploaded_files, session_store)
```

### 9. **Session State Management**
**Current Issue:** Session state access scattered throughout code.

**Recommendations:**
- Create a SessionManager class to encapsulate state operations
- Add state validation
- Implement state persistence/backup

**Example:**
```python
class SessionManager:
    def __init__(self, session_store):
        self.store = session_store
    
    def get_history(self) -> List[Dict]:
        return self.store.get("history", [])
    
    def add_message(self, author: str, author_key: str, content: str):
        history = self.get_history()
        history.append({"author": author, "author_key": author_key, "content": content})
        self.store.set("history", history)
```

### 10. **Prompt Engineering Improvements**
**Current Issue:** Prompt construction is basic and doesn't use system.txt effectively.

**Recommendations:**
- Load and use system.txt in Chainlit app (currently only in Streamlit)
- Add prompt templates with better structure
- Support dynamic prompt customization

**Example:**
```python
def load_system_prompt() -> str:
    system_path = os.path.join(os.path.dirname(__file__), "system.txt")
    try:
        with open(system_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Participate in a talk show. Be concise."

async def build_prompt(history: List[Dict]) -> tuple[str, str]:
    system_prompt = load_system_prompt()
    # ... rest of prompt building
```

## 🎨 Low Priority / Nice-to-Have

### 11. **Testing Infrastructure**
- Add unit tests for core functions
- Add integration tests for API interactions
- Mock OpenAI API for testing

### 12. **Performance Monitoring**
- Add timing/metrics collection
- Track API call latencies
- Monitor token usage

### 13. **Documentation**
- Add comprehensive docstrings
- Create API documentation
- Add usage examples

### 14. **Security Enhancements**
- Validate file types more strictly
- Add rate limiting
- Sanitize user inputs before sending to API

### 15. **Feature Enhancements**
- Add conversation export functionality
- Support multiple vector stores
- Add conversation history search
- Implement conversation templates/presets

## 📊 Code Quality Metrics to Track

1. **Cyclomatic Complexity:** Keep functions simple (< 10)
2. **Test Coverage:** Aim for > 80%
3. **Type Coverage:** 100% type hints
4. **Documentation Coverage:** All public functions documented

## 🚀 Quick Wins (Easy to Implement)

1. ✅ Replace all `print()` with `logger` calls
2. ✅ Extract magic numbers to constants
3. ✅ Add type hints to function signatures
4. ✅ Add docstrings to all functions
5. ✅ Use `system.txt` in Chainlit app
6. ✅ Add input validation for settings
7. ✅ Improve error messages with context

