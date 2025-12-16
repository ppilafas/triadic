# AI Backend Reuse Guide

## 📋 Overview

This guide explains how to extract and reuse the Triadic AI backend components in other projects. The backend is designed to be **framework-agnostic** and can work with Streamlit, Chainlit, Flask, FastAPI, or any Python framework.

## 🚀 Quick Start for Streamlit

**Want to quickly create a new Streamlit project?** Use the automated kickstart script:

```bash
# From the Triadic project root
python kickstart_streamlit_project.py my_chatbot ~/projects/
```

This creates a complete Streamlit project with all backend files, a working `app.py`, and configuration files. See the main `README.md` for an overview of the generated structure.

---

## 🎯 Reusable Components

### Core Backend (Framework-Agnostic)

These components have **no framework dependencies** and can be used in any Python project:

#### 1. **`ai_api.py`** - OpenAI API Wrapper
- **Purpose**: Unified interface for OpenAI API calls
- **Features**:
  - Synchronous and streaming model calls
  - Automatic retry logic with exponential backoff
  - Vector store management (RAG)
  - File indexing for document search
  - Universal session helpers (works with any session store)
- **Dependencies**: `openai`, `config.py`, `exceptions.py`
- **Key Functions**:
  ```python
  from ai_api import call_model, stream_model_generator, ensure_vector_store, index_uploaded_files
  
  # Synchronous call
  response = call_model(prompt_text, config={"model_name": "gpt-5-mini"})
  
  # Streaming call
  for chunk in stream_model_generator(prompt_text, config):
      print(chunk, end="")
  
  # RAG setup
  vs_id = ensure_vector_store(session_store)
  index_uploaded_files(uploaded_files, session_store)
  ```

#### 2. **`core/conversation.py`** - Conversation State Management
- **Purpose**: Manages conversation history and speaker alternation
- **Features**:
  - Message history tracking
  - Speaker alternation logic
  - Turn counting
  - Framework-agnostic data structures
- **Dependencies**: `config.py` (for speaker profiles)
- **Key Classes**:
  ```python
  from core.conversation import ConversationState, get_next_speaker_key
  
  state = ConversationState()
  state.add_message("host", "Hello, welcome to the show!")
  state.add_message("gpt_a", "Thank you for having me!")
  
  next_speaker = get_next_speaker_key("gpt_a")  # Returns "gpt_b"
  ```

#### 3. **`core/message_builder.py`** - Prompt Construction
- **Purpose**: Builds prompts from conversation history
- **Features**:
  - System prompt loading
  - Conversation formatting
  - Tool availability integration
  - Persona support
- **Dependencies**: `config.py`, `core/conversation.py`
- **Key Functions**:
  ```python
  from core.message_builder import build_prompt_from_messages, load_system_prompt
  
  prompt = build_prompt_from_messages(
      next_speaker="gpt_a",
      messages=conversation_history,
      available_tools=["web_search", "file_search"]
  )
  ```

#### 4. **`config.py`** - Configuration Management
- **Purpose**: Centralized configuration
- **Features**:
  - Model configuration
  - Speaker profiles
  - Audio settings
  - Environment-based API key management
- **Dependencies**: None (pure configuration)
- **Usage**:
  ```python
  from config import model_config, speaker_config, get_openai_api_key
  
  api_key = get_openai_api_key()  # Checks env, secrets, session
  model = model_config.DEFAULT_MODEL
  ```

#### 5. **`exceptions.py`** - Custom Exceptions
- **Purpose**: Structured error handling
- **Dependencies**: None
- **Usage**:
  ```python
  from exceptions import ModelGenerationError, VectorStoreError
  
  try:
      response = call_model(prompt)
  except ModelGenerationError as e:
      print(f"Model error: {e}")
  ```

#### 6. **`stt.py`** - Speech-to-Text
- **Purpose**: Audio transcription using Whisper
- **Dependencies**: `openai` (for Whisper API)
- **Usage**:
  ```python
  from stt import transcribe_audio
  
  with open("audio.wav", "rb") as audio_file:
      text = transcribe_audio(audio_file)
  ```

#### 7. **`tts.py`** - Text-to-Speech
- **Purpose**: Generate audio from text
- **Dependencies**: `openai` (for TTS API)
- **Usage**:
  ```python
  from tts import tts_stream_to_bytes
  
  audio_bytes = tts_stream_to_bytes("Hello world", voice="alloy")
  ```

#### 8. **`services/`** - Business Services
- **`topic_generator.py`**: Generate discussion topics from documents
- **`conversation_summarizer.py`**: Summarize conversations
- **Dependencies**: `ai_api.py`, `config.py`

---

## 📦 Extraction Steps

### Step 1: Create a New Project Structure

```
your_project/
├── backend/                    # Extracted backend
│   ├── __init__.py
│   ├── ai_api.py              # Copy from triadic/
│   ├── config.py              # Copy and customize
│   ├── exceptions.py          # Copy as-is
│   ├── stt.py                 # Copy as-is
│   ├── tts.py                 # Copy as-is
│   ├── core/
│   │   ├── __init__.py
│   │   ├── conversation.py
│   │   └── message_builder.py
│   └── services/
│       ├── __init__.py
│       └── topic_generator.py
├── utils/                      # Optional utilities
│   ├── logging_config.py      # Copy if needed
│   └── validators.py          # Copy if needed
└── requirements.txt
```

### Step 2: Copy Core Files

```bash
# From triadic project
cp ai_api.py your_project/backend/
cp config.py your_project/backend/
cp exceptions.py your_project/backend/
cp stt.py your_project/backend/
cp tts.py your_project/backend/
cp -r core/ your_project/backend/
cp -r services/ your_project/backend/
```

### Step 3: Update Dependencies

**`requirements.txt`**:
```txt
openai>=1.0.0
python-dotenv>=1.0.0  # For environment variables (optional)
```

### Step 4: Customize Configuration

Edit `backend/config.py` to match your project's needs:

```python
# Update model defaults
@dataclass
class ModelConfig:
    DEFAULT_MODEL: str = "gpt-4"  # Change to your default
    DEFAULT_REASONING_EFFORT: str = "medium"
    MAX_OUTPUT_TOKENS: int = 2048

# Update speaker profiles (if using multi-speaker)
@dataclass
class SpeakerConfig:
    PROFILES: Dict[str, Dict[str, str]] = {
        "assistant": {"name": "Assistant", "avatar": "/avatar.png"},
        "user": {"name": "User", "avatar": "/user.png"},
    }
```

### Step 5: Update Imports

In `ai_api.py` and other files, update imports:

```python
# Change from:
from config import model_config
from utils.logging_config import get_logger

# To:
from backend.config import model_config
from backend.utils.logging_config import get_logger  # If you copy utils
```

---

## 🚀 Usage Examples

### Example 1: Simple Chat Bot (Flask)

```python
from flask import Flask, request, jsonify
from backend.ai_api import call_model
from backend.core.conversation import ConversationState
from backend.core.message_builder import build_prompt_from_messages

app = Flask(__name__)
conversation = ConversationState()

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    
    # Add user message
    conversation.add_message("user", user_message)
    
    # Build prompt
    prompt = build_prompt_from_messages(
        next_speaker="assistant",
        messages=conversation.get_history(format="streamlit")
    )
    
    # Get AI response
    response = call_model(prompt)
    
    # Add AI response
    conversation.add_message("assistant", response)
    
    return jsonify({"response": response})

if __name__ == "__main__":
    app.run()
```

### Example 2: FastAPI with Streaming

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from backend.ai_api import stream_model_generator
from backend.core.message_builder import build_prompt_from_messages

app = FastAPI()

@app.post("/stream")
async def stream_chat(prompt: str):
    def generate():
        for chunk in stream_model_generator(prompt):
            yield f"data: {chunk}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

### Example 3: CLI Tool

```python
#!/usr/bin/env python3
"""Simple CLI chat using the backend"""

from backend.ai_api import call_model
from backend.core.conversation import ConversationState
from backend.core.message_builder import build_prompt_from_messages

def main():
    conversation = ConversationState()
    
    print("Chat CLI (type 'exit' to quit)")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            break
        
        conversation.add_message("user", user_input)
        
        prompt = build_prompt_from_messages(
            next_speaker="assistant",
            messages=conversation.get_history(format="streamlit")
        )
        
        print("Assistant: ", end="", flush=True)
        response = call_model(prompt)
        print(response)
        
        conversation.add_message("assistant", response)

if __name__ == "__main__":
    main()
```

### Example 4: Discord Bot

```python
import discord
from discord.ext import commands
from backend.ai_api import call_model
from backend.core.conversation import ConversationState
from backend.core.message_builder import build_prompt_from_messages

# Store conversations per channel
conversations = {}

bot = commands.Bot(command_prefix="!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Get or create conversation for channel
    channel_id = message.channel.id
    if channel_id not in conversations:
        conversations[channel_id] = ConversationState()
    
    conv = conversations[channel_id]
    conv.add_message("user", message.content)
    
    prompt = build_prompt_from_messages(
        next_speaker="assistant",
        messages=conv.get_history(format="streamlit")
    )
    
    response = call_model(prompt)
    conv.add_message("assistant", response)
    
    await message.channel.send(response)
    
    await bot.process_commands(message)

bot.run("YOUR_BOT_TOKEN")
```

### Example 5: RAG-Enabled API

```python
from flask import Flask, request, jsonify
from backend.ai_api import call_model, ensure_vector_store, index_uploaded_files
from backend.core.message_builder import build_prompt_from_messages

app = Flask(__name__)
session_store = {}  # Simple dict-based session

@app.post("/upload")
def upload_files():
    files = request.files.getlist("files")
    
    # Index files for RAG
    index_uploaded_files(files, session_store)
    
    return jsonify({"status": "files indexed"})

@app.post("/query")
def query():
    question = request.json.get("question")
    config = {
        "vector_store_id": ensure_vector_store(session_store),
        "model_name": "gpt-5-mini"
    }
    
    # Model will automatically use file_search tool
    response = call_model(question, config=config)
    
    return jsonify({"response": response})
```

---

## 🔧 Customization Points

### 1. **System Prompt**

Edit `system.txt` or modify `load_system_prompt()` in `core/message_builder.py`:

```python
def load_system_prompt() -> str:
    return "You are a helpful assistant. Be concise and friendly."
```

### 2. **Speaker Profiles**

Modify `config.py`:

```python
@dataclass
class SpeakerConfig:
    PROFILES: Dict[str, Dict[str, str]] = {
        "assistant": {"name": "AI Assistant"},
        "user": {"name": "User"},
    }
```

### 3. **Model Configuration**

```python
@dataclass
class ModelConfig:
    DEFAULT_MODEL: str = "gpt-4"
    DEFAULT_REASONING_EFFORT: str = "medium"
    MAX_OUTPUT_TOKENS: int = 2048
```

### 4. **Error Handling**

Customize exception handling in your application:

```python
from backend.exceptions import ModelGenerationError, VectorStoreError

try:
    response = call_model(prompt)
except ModelGenerationError as e:
    # Your custom error handling
    logger.error(f"Model error: {e}")
    return {"error": "Failed to generate response"}
```

---

## 📋 Dependencies

### Required
- `openai>=1.0.0` - OpenAI Python SDK

### Optional
- `python-dotenv` - Environment variable management
- `pydantic` - Data validation (if you want to add it)
- `tenacity` - Advanced retry logic (if you want to replace built-in retry)

---

## 🎨 Framework Integration

### Streamlit
Already integrated in Triadic. See `app.py` for reference.

### Chainlit
Already integrated in Triadic. See `app_chainlit.py` for reference.

### Flask/FastAPI
See examples above.

### Django
```python
from django.http import JsonResponse
from backend.ai_api import call_model

def chat_view(request):
    prompt = request.POST.get("message")
    response = call_model(prompt)
    return JsonResponse({"response": response})
```

---

## 🔐 Environment Setup

### Option 1: Environment Variables
```bash
export OPENAI_API_KEY="sk-..."
```

### Option 2: `.env` File
```env
OPENAI_API_KEY=sk-...
```

### Option 3: Application Secrets
For Streamlit Cloud, use `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "sk-..."
```

---

## 🧪 Testing

Create a simple test:

```python
# test_backend.py
from backend.ai_api import call_model
from backend.core.conversation import ConversationState

def test_basic_call():
    response = call_model("Say hello")
    assert "hello" in response.lower()

def test_conversation():
    conv = ConversationState()
    conv.add_message("user", "Hi")
    assert len(conv.messages) == 1
    assert conv.messages[0]["content"] == "Hi"
```

---

## 📝 Notes

1. **Session Management**: The backend uses universal session helpers that work with any dict-like object or object with `.get()`/`.set()` methods.

2. **Streaming**: Use `stream_model_generator()` for streaming responses. It yields text chunks as they arrive.

3. **RAG**: Vector stores are automatically created and managed. Files are indexed per session.

4. **Error Handling**: All functions raise custom exceptions from `exceptions.py` for better error handling.

5. **Configuration**: The `config.py` module is designed to be easily customizable without modifying core logic.

---

## 🚀 Next Steps

1. **Extract** the backend files to your project
2. **Customize** `config.py` for your use case
3. **Update** imports in your application
4. **Test** with a simple example
5. **Integrate** with your chosen framework
6. **Deploy** and enjoy!

---

## 📚 Additional Resources

- **OpenAI API Docs**: https://platform.openai.com/docs
- **Triadic Project**: See `app.py` and `app_chainlit.py` for full integration examples
- **Core Modules**: See `core/` directory for business logic examples

---

**Questions?** Check the Triadic codebase for working examples of all these patterns!

