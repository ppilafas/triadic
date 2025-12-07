# Modularization Plan for Triadic Codebase

## 📋 Current State Analysis

### Current Structure
```
triadic/
├── app.py                    # Streamlit app (911 lines)
├── app_chainlit.py           # Chainlit app (770 lines)
├── ai_api.py                 # AI API wrapper
├── stt.py                    # Speech-to-Text
├── tts.py                    # Text-to-Speech
├── config.py                 # Configuration
├── exceptions.py             # Custom exceptions
├── utils/
│   ├── conversation.py       # Conversation logic
│   ├── chainlit_ui.py        # Chainlit UI helpers
│   ├── logging_config.py     # Logging setup
│   └── validators.py         # Input validation
└── public/                   # Static assets
```

### Issues Identified

1. **Code Duplication**
   - Speaker info duplicated in `app.py` and `app_chainlit.py`
   - UI rendering logic duplicated
   - Turn execution logic duplicated

2. **Mixed Concerns**
   - Business logic mixed with UI code
   - Framework-specific code not separated
   - Configuration scattered

3. **Large Files**
   - `app.py`: 911 lines (too large)
   - `app_chainlit.py`: 770 lines (too large)
   - Hard to maintain and test

4. **Tight Coupling**
   - UI components directly call business logic
   - Hard to swap frameworks
   - Difficult to test in isolation

## 🎯 Proposed Structure

```
triadic/
├── core/                          # Framework-agnostic business logic
│   ├── __init__.py
│   ├── conversation.py            # Conversation state & flow
│   ├── turn_executor.py           # Turn execution logic
│   ├── message_builder.py         # Prompt building
│   └── session_manager.py        # Session state management
│
├── ui/                            # UI components (framework-agnostic)
│   ├── __init__.py
│   ├── components/                # Reusable UI components
│   │   ├── __init__.py
│   │   ├── speaker_info.py        # Speaker configuration & styling
│   │   ├── message_bubbles.py     # Message rendering
│   │   ├── status_badges.py       # Status indicators
│   │   └── metrics.py             # Metrics display
│   └── themes.py                   # Theme/styling configuration
│
├── adapters/                      # Framework-specific adapters
│   ├── __init__.py
│   ├── streamlit/                 # Streamlit-specific code
│   │   ├── __init__.py
│   │   ├── app.py                 # Main Streamlit app (thin)
│   │   ├── components.py          # Streamlit UI components
│   │   ├── sidebar.py             # Sidebar configuration
│   │   ├── chat_ui.py             # Chat interface
│   │   └── telemetry.py           # Telemetry visualization
│   └── chainlit/                  # Chainlit-specific code
│       ├── __init__.py
│       ├── app.py                 # Main Chainlit app (thin)
│       ├── components.py          # Chainlit UI components
│       ├── commands.py            # Command setup
│       └── controls.py            # Control panel
│
├── services/                      # External service integrations
│   ├── __init__.py
│   ├── ai_service.py              # AI API wrapper (from ai_api.py)
│   ├── stt_service.py             # Speech-to-Text (from stt.py)
│   └── tts_service.py             # Text-to-Speech (from tts.py)
│
├── utils/                         # Shared utilities
│   ├── __init__.py
│   ├── logging_config.py          # Logging setup
│   ├── validators.py              # Input validation
│   └── helpers.py                 # General helpers
│
├── config/                        # Configuration
│   ├── __init__.py
│   ├── settings.py                # App settings (from config.py)
│   └── constants.py               # Constants
│
├── exceptions.py                  # Custom exceptions
├── system.txt                     # System prompt
├── bootstrap.sh                   # Launcher script
└── public/                        # Static assets
    ├── avatars/
    └── custom.css
```

## 📦 Module Responsibilities

### 1. `core/` - Business Logic (Framework-Agnostic)

#### `core/conversation.py`
- **Purpose**: Conversation state management
- **Functions**:
  - `ConversationState` class (dataclass)
  - `add_message()`
  - `get_history()`
  - `reset_conversation()`
- **Dependencies**: `config/`, `utils/`

#### `core/turn_executor.py`
- **Purpose**: Execute AI turns
- **Functions**:
  - `execute_turn()` - Main turn execution
  - `prepare_turn()` - Prepare turn data
  - `process_response()` - Process AI response
- **Dependencies**: `services/`, `core/conversation.py`, `core/message_builder.py`

#### `core/message_builder.py`
- **Purpose**: Build prompts and format messages
- **Functions**:
  - `build_prompt()` - Build AI prompt
  - `format_message()` - Format message for display
  - `load_system_prompt()` - Load system prompt
- **Dependencies**: `config/`, `core/conversation.py`

#### `core/session_manager.py`
- **Purpose**: Abstract session management
- **Functions**:
  - `SessionManager` abstract base class
  - Framework-specific implementations
- **Dependencies**: None (abstract)

### 2. `ui/` - UI Components (Framework-Agnostic)

#### `ui/components/speaker_info.py`
- **Purpose**: Speaker configuration and metadata
- **Classes**:
  - `SpeakerInfo` dataclass
  - `SpeakerRegistry` class
- **Dependencies**: `config/`

#### `ui/components/message_bubbles.py`
- **Purpose**: Message rendering logic
- **Functions**:
  - `create_message_html()` - Generate HTML
  - `format_message_content()` - Format content
- **Dependencies**: `ui/components/speaker_info.py`

#### `ui/components/status_badges.py`
- **Purpose**: Status indicators
- **Functions**:
  - `create_status_badge()` - Create badge HTML
  - `create_on_air_badge()` - ON AIR badge
- **Dependencies**: `ui/components/speaker_info.py`

#### `ui/components/metrics.py`
- **Purpose**: Metrics calculation and formatting
- **Functions**:
  - `calculate_metrics()` - Calculate stats
  - `format_metrics()` - Format for display
- **Dependencies**: `core/conversation.py`

#### `ui/themes.py`
- **Purpose**: Theme configuration
- **Classes**:
  - `Theme` dataclass
  - `ThemeManager` class
- **Dependencies**: `config/`

### 3. `adapters/` - Framework-Specific Code

#### `adapters/streamlit/app.py`
- **Purpose**: Main Streamlit entry point (thin)
- **Responsibilities**:
  - Page setup
  - Route to components
  - Session initialization
- **Size**: ~100-150 lines (down from 911)

#### `adapters/streamlit/components.py`
- **Purpose**: Streamlit-specific UI components
- **Functions**:
  - `render_metrics()` - Render metrics cards
  - `render_sidebar()` - Render sidebar
  - `render_chat_message()` - Render chat message
- **Dependencies**: `ui/`, `core/`

#### `adapters/streamlit/sidebar.py`
- **Purpose**: Sidebar configuration UI
- **Functions**:
  - `render_model_config()` - Model settings
  - `render_broadcast_controls()` - Broadcast controls
  - `render_telemetry()` - Telemetry chart
- **Dependencies**: `ui/`, `config/`

#### `adapters/streamlit/chat_ui.py`
- **Purpose**: Chat interface
- **Functions**:
  - `render_chat_history()` - Render messages
  - `render_input_area()` - Input controls
  - `handle_user_input()` - Handle input
- **Dependencies**: `ui/`, `core/`

#### `adapters/chainlit/app.py`
- **Purpose**: Main Chainlit entry point (thin)
- **Responsibilities**:
  - Event handlers
  - Route to components
  - Session initialization
- **Size**: ~150-200 lines (down from 770)

#### `adapters/chainlit/components.py`
- **Purpose**: Chainlit-specific UI components
- **Functions**:
  - `render_message()` - Render Chainlit message
  - `render_controls()` - Render controls
- **Dependencies**: `ui/`, `core/`

#### `adapters/chainlit/commands.py`
- **Purpose**: Chainlit Commands setup
- **Functions**:
  - `setup_commands()` - Setup commands
  - `handle_command()` - Handle command events
- **Dependencies**: `core/`, `config/`

### 4. `services/` - External Services

#### `services/ai_service.py`
- **Purpose**: AI API integration
- **Functions**:
  - `call_model()` - Call AI model
  - `stream_model()` - Stream AI response
  - `index_files()` - Index files for RAG
- **Dependencies**: `config/`, `exceptions.py`

#### `services/stt_service.py`
- **Purpose**: Speech-to-Text service
- **Functions**:
  - `transcribe_audio()` - Transcribe audio
  - `create_wav_buffer()` - Create WAV buffer
- **Dependencies**: `config/`, `exceptions.py`

#### `services/tts_service.py`
- **Purpose**: Text-to-Speech service
- **Functions**:
  - `synthesize_speech()` - Synthesize speech
  - `stream_to_bytes()` - Stream TTS to bytes
- **Dependencies**: `config/`, `exceptions.py`

### 5. `config/` - Configuration

#### `config/settings.py`
- **Purpose**: Application settings
- **Classes**:
  - `ModelConfig`
  - `AudioConfig`
  - `TimingConfig`
  - `SpeakerConfig`
- **Dependencies**: None

#### `config/constants.py`
- **Purpose**: Constants and enums
- **Content**:
  - Model names
  - Voice names
  - Error messages
- **Dependencies**: None

## 🔄 Migration Strategy

### Phase 1: Extract Core Business Logic (Week 1)
1. Create `core/` directory structure
2. Extract conversation logic from `utils/conversation.py` → `core/conversation.py`
3. Extract turn execution logic → `core/turn_executor.py`
4. Extract message building → `core/message_builder.py`
5. Update imports in both apps

### Phase 2: Extract UI Components (Week 1-2)
1. Create `ui/` directory structure
2. Extract speaker info → `ui/components/speaker_info.py`
3. Extract message rendering → `ui/components/message_bubbles.py`
4. Extract status badges → `ui/components/status_badges.py`
5. Create theme system → `ui/themes.py`

### Phase 3: Refactor Services (Week 2)
1. Create `services/` directory
2. Move `ai_api.py` → `services/ai_service.py`
3. Move `stt.py` → `services/stt_service.py`
4. Move `tts.py` → `services/tts_service.py`
5. Update all imports

### Phase 4: Create Framework Adapters (Week 2-3)
1. Create `adapters/streamlit/` structure
2. Refactor `app.py` → `adapters/streamlit/app.py` (thin)
3. Extract components → `adapters/streamlit/components.py`
4. Extract sidebar → `adapters/streamlit/sidebar.py`
5. Extract chat UI → `adapters/streamlit/chat_ui.py`
6. Repeat for Chainlit

### Phase 5: Reorganize Configuration (Week 3)
1. Create `config/` directory
2. Move `config.py` → `config/settings.py`
3. Extract constants → `config/constants.py`
4. Update all imports

### Phase 6: Testing & Cleanup (Week 3-4)
1. Test both apps thoroughly
2. Update documentation
3. Remove old files
4. Update `bootstrap.sh` if needed

## 📊 Benefits

### 1. **Maintainability**
- Smaller, focused files (100-200 lines each)
- Clear separation of concerns
- Easier to locate and fix bugs

### 2. **Testability**
- Business logic can be tested independently
- UI components can be tested in isolation
- Mock framework adapters for testing

### 3. **Reusability**
- UI components work across frameworks
- Business logic framework-agnostic
- Easy to add new frameworks (e.g., Gradio, FastAPI)

### 4. **Scalability**
- Easy to add new features
- Clear extension points
- Better code organization

### 5. **Developer Experience**
- Easier onboarding
- Clear file structure
- Better IDE navigation

## 🎯 Implementation Priorities

### High Priority (Do First)
1. ✅ Extract core business logic
2. ✅ Extract UI components
3. ✅ Refactor services

### Medium Priority (Do Next)
4. ⚠️ Create framework adapters
5. ⚠️ Reorganize configuration

### Low Priority (Polish)
6. ⚪ Add comprehensive tests
7. ⚪ Update documentation
8. ⚪ Performance optimizations

## 📝 Example: Before vs After

### Before (app.py - 911 lines)
```python
# app.py - Everything in one file
import streamlit as st
from tts import tts_stream_to_bytes
from ai_api import call_model
# ... 50+ lines of imports

# 50+ lines of configuration
SPEAKER_INFO = {...}

# 100+ lines of helper functions
def build_prompt(...):
    ...

def execute_turn(...):
    ...

# 700+ lines of UI code
def podcast_stage():
    ...

podcast_stage()
```

### After (Modular)
```python
# adapters/streamlit/app.py - ~100 lines
import streamlit as st
from core.turn_executor import execute_turn
from adapters.streamlit.sidebar import render_sidebar
from adapters.streamlit.chat_ui import render_chat_ui

st.set_page_config(...)

if __name__ == "__main__":
    render_sidebar()
    render_chat_ui()
```

## 🔍 Key Design Principles

1. **Separation of Concerns**: Business logic separate from UI
2. **Dependency Inversion**: Depend on abstractions, not implementations
3. **Single Responsibility**: Each module has one clear purpose
4. **Framework Agnostic**: Core logic works with any framework
5. **Composition over Inheritance**: Build complex from simple parts

## 🚀 Next Steps

1. Review and approve this plan
2. Create feature branch: `refactor/modularization`
3. Start with Phase 1 (Core Business Logic)
4. Test incrementally after each phase
5. Merge when all phases complete

## 📚 Additional Considerations

### Testing Strategy
- Unit tests for `core/` modules
- Integration tests for `services/`
- UI tests for `adapters/` (framework-specific)

### Documentation
- Update README with new structure
- Add docstrings to all modules
- Create architecture diagram

### Backward Compatibility
- Keep old imports working during migration
- Use deprecation warnings
- Gradual migration path

