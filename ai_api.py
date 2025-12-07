# ai_api.py
#
# Central AI API façade for the Triadic app.
# Framework-Agnostic (Works with Streamlit & Chainlit)
#
# Features:
# - Universal Session Handler (Fixes 'UserSession not iterable' error)
# - Universal File Indexing (Streamlit/Chainlit compatibility)
# - Safe defaults
# - Fixed 'tools' variable scope error
# - Proper logging and error handling
# - Type hints and validation

import io
import time
from typing import List, Optional, Generator, Dict, Any, Callable, TypeVar

# Attempt to import streamlit, but don't crash if missing
try:
    import streamlit as st
except ImportError:
    st = None

from openai import OpenAI

# Import our improved modules
from config import model_config, get_openai_api_key, get_openai_model
from exceptions import VectorStoreError, FileIndexingError, ModelGenerationError, ConfigurationError
from utils.logging_config import get_logger
from utils.validators import sanitize_filename

# Initialize logging
from utils.logging_config import setup_logging
setup_logging()

# Initialize logger
logger = get_logger(__name__)

# ---------- OpenAI client & base model ----------

# Store last used API key to detect changes
_last_api_key: Optional[str] = None
_client: Optional[OpenAI] = None

def get_client() -> OpenAI:
    """Get OpenAI client instance, creating it dynamically if needed."""
    global _client, _last_api_key
    
    # Get API key dynamically (checks session state, secrets, env)
    api_key = get_openai_api_key()
    
    if not api_key:
        raise ConfigurationError("OpenAI client not initialized; missing OPENAI_API_KEY")
    
    # Recreate client if key changed or client doesn't exist
    if _client is None or _last_api_key != api_key:
        _client = OpenAI(api_key=api_key)
        _last_api_key = api_key
    
    return _client

def get_default_model_name() -> str:
    """Get default model name dynamically."""
    model = get_openai_model()
    return model or model_config.DEFAULT_MODEL

DEFAULT_MODEL_NAME = get_default_model_name()

# ---------- Universal Session Helpers ----------

def get_session_val(store: Optional[Any], key: str, default: Any = None) -> Any:
    """
    Safely gets a value from either Streamlit session_state (dict-like)
    or Chainlit user_session (method-based).
    
    Args:
        store: Session store (Streamlit session_state or Chainlit user_session)
        key: Key to retrieve
        default: Default value if key not found
    
    Returns:
        Value from session or default
    """
    if store is None:
        return default
    
    # 1. Try .get() method (Works for both Chainlit and Dicts)
    if hasattr(store, "get"):
        return store.get(key, default)
    
    # 2. Fallback to dictionary access (Streamlit specific fallback)
    try:
        return store[key]
    except KeyError:
        return default

def set_session_val(store: Optional[Any], key: str, value: Any) -> None:
    """
    Safely sets a value in either Streamlit or Chainlit session.
    
    Args:
        store: Session store (Streamlit session_state or Chainlit user_session)
        key: Key to set
        value: Value to set
    """
    if store is None:
        return

    # 1. Chainlit UserSession uses .set()
    if hasattr(store, "set"):
        store.set(key, value)
    # 2. Streamlit/Dict uses item assignment
    else:
        store[key] = value

# ---------- Vector store / file search helpers ----------

def ensure_vector_store(session_store: Optional[Any] = None) -> Optional[str]:
    """
    Ensure a vector store exists for the session, creating one if needed.
    
    Args:
        session_store: Session store to persist vector store ID
    
    Returns:
        Vector store ID or None if creation failed
    
    Raises:
        VectorStoreError: If vector store creation fails
    """
    # Default to Streamlit state if no store provided
    if session_store is None and st is not None:
        session_store = st.session_state

    # Check for existing ID safely
    existing_id = get_session_val(session_store, "vector_store_id")
    if existing_id:
        logger.debug(f"Using existing vector store: {existing_id}")
        return existing_id
    
    try:
        logger.info("Creating new vector store")
        vs = get_client().vector_stores.create(name="triadic-session-store")
        # Save ID safely
        set_session_val(session_store, "vector_store_id", vs.id)
        logger.info(f"Created vector store: {vs.id}")
        return vs.id
    except Exception as e:
        logger.error(f"Failed to create vector store: {e}", exc_info=True)
        raise VectorStoreError(f"Could not create vector store: {e}") from e

def index_uploaded_files(uploaded_files: List[Any], session_store: Optional[Any] = None) -> None:
    """
    Index uploaded files into the vector store for RAG.
    
    Args:
        uploaded_files: List of file objects (Streamlit or Chainlit format)
        session_store: Session store to track indexed files
    
    Raises:
        FileIndexingError: If file indexing fails
    """
    if not uploaded_files:
        logger.debug("No files to index")
        return

    if session_store is None and st is not None:
        session_store = st.session_state
    
    # Note: session_store can be None, Chainlit UserSession, or Streamlit session_state
    # Both are handled by get_session_val/set_session_val helpers

    try:
        vs_id = ensure_vector_store(session_store)
    except VectorStoreError as e:
        logger.error(f"Cannot index files without vector store: {e}")
        raise FileIndexingError(f"Vector store unavailable: {e}") from e

    # Initialize index tracker safely
    index_map = get_session_val(session_store, "uploaded_file_index")
    if index_map is None:
        index_map = {}
        set_session_val(session_store, "uploaded_file_index", index_map)

    for f in uploaded_files:
        # 1. Normalize file data (Streamlit vs Chainlit)
        file_bytes = None
        
        # Streamlit
        if hasattr(f, "getvalue"):
            file_bytes = f.getvalue()
        # Chainlit (In-Memory)
        elif hasattr(f, "content") and f.content:
            if callable(f.content):
                file_bytes = f.content()
            else:
                file_bytes = f.content
        # Chainlit (Temp File on Disk)
        elif hasattr(f, "path") and f.path:
            try:
                with open(f.path, "rb") as file_handle:
                    file_bytes = file_handle.read()
            except Exception as e:
                logger.error(f"Error reading file path {f.path}: {e}", exc_info=True)
                continue
        
        if not file_bytes:
            logger.warning("Skipping file with no data")
            continue

        file_name = getattr(f, "name", "unknown_file")
        # Sanitize filename
        file_name = sanitize_filename(file_name)
        file_size = getattr(f, "size", len(file_bytes))
        key = f"{file_name}:{file_size}"

        if key in index_map:
            logger.debug(f"File already indexed: {file_name}")
            continue

        try:
            # Upload to OpenAI
            file_obj = io.BytesIO(file_bytes)
            file_obj.name = file_name
            
            logger.info(f"Uploading file to OpenAI: {file_name} ({file_size} bytes)")
            uploaded = get_client().files.create(
                file=file_obj,
                purpose="assistants",
            )
            get_client().vector_stores.files.create(
                vector_store_id=vs_id,
                file_id=uploaded.id,
            )
            
            index_map[key] = uploaded.id
            logger.info(f"[RAG] Successfully indexed: {file_name} (ID: {uploaded.id})")
            
        except Exception as e:
            logger.error(f"Failed to index file '{file_name}': {e}", exc_info=True)
            raise FileIndexingError(f"Failed to index file '{file_name}': {e}") from e

# ---------- Config Helper ----------

def _get_config_value(key: str, override: Optional[Dict[str, Any]] = None, default: Any = None) -> Any:
    """
    Get configuration value from override dict or session state.
    
    Args:
        key: Configuration key
        override: Override dictionary (takes precedence)
        default: Default value if not found
    
    Returns:
        Configuration value or default
    """
    if override and key in override:
        return override[key]
    if st and hasattr(st, "session_state") and key in st.session_state:
        return st.session_state[key]
    return default

# ---------- kwargs builder ----------

def _build_responses_kwargs(prompt_text: str, config: Optional[Dict[str, Any]], stream: bool) -> Dict[str, Any]:
    """
    Build the kwargs dict for client.responses.create(...)
    
    Args:
        prompt_text: Input prompt text
        config: Configuration dictionary
        stream: Whether to stream the response
    
    Returns:
        Dictionary of kwargs for OpenAI API call
    """
    # [FIX] 'tools' is defined here so it is available in the entire scope
    tools = []
    
    # Add file_search tool if vector store is available
    vs_id = _get_config_value("vector_store_id", config)
    # Only add file_search if vs_id is truthy and not an empty string
    if vs_id and vs_id != "":
        tools.append({"type": "file_search", "vector_store_ids": [vs_id]})
    
    # Add web_search tool if enabled
    web_search_enabled = _get_config_value("web_search_enabled", config, False)
    logger.info(f"Web search check - config value: {web_search_enabled}, config dict: {config.get('web_search_enabled') if config else 'no config'}")
    if web_search_enabled:
        tools.append({"type": "web_search"})
        logger.info("Web search tool enabled and added to tools list")

    effort = _get_config_value("reasoning_effort", config, model_config.DEFAULT_REASONING_EFFORT)
    verbosity = _get_config_value("text_verbosity", config, "medium")
    model_name = _get_config_value("model_name", config, DEFAULT_MODEL_NAME)
    use_summary = _get_config_value("reasoning_summary_enabled", config, False)

    if model_name == "gpt-5-mini" and effort == "none":
        effort = "minimal"

    reasoning_config = {"effort": effort}
    if use_summary:
        reasoning_config["summary"] = "auto"

    kwargs = dict(
        model=model_name,
        input=prompt_text,
        reasoning=reasoning_config,
        text={"verbosity": verbosity},
        max_output_tokens=model_config.MAX_OUTPUT_TOKENS,
        stream=stream,
    )

    if model_name.startswith("gpt-5.1") and effort == "none":
        kwargs["temperature"] = 0.4

    if tools:
        kwargs["tools"] = tools
        logger.info(f"Enabled tools: {[t.get('type', 'unknown') for t in tools]}")

    return kwargs

# ---------- Retry Logic ----------

T = TypeVar('T')

def _retry_api_call(func: Callable[[], T], max_retries: int = 3, base_delay: float = 1.0) -> T:
    """
    Retry an API call with exponential backoff.
    
    Args:
        func: Function to call
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
    
    Returns:
        Result of function call
    
    Raises:
        ModelGenerationError: If all retries fail
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"API call failed (attempt {attempt + 1}/{max_retries}), retrying in {delay}s: {e}")
                time.sleep(delay)
            else:
                logger.error(f"API call failed after {max_retries} attempts: {e}", exc_info=True)
    
    raise ModelGenerationError(f"API call failed after {max_retries} retries: {last_exception}") from last_exception

# ---------- Public LLM façade ----------

def call_model(prompt_text: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Call the model synchronously and return the full response.
    
    Args:
        prompt_text: Input prompt text
        config: Configuration dictionary
    
    Returns:
        Full model response text
    
    Raises:
        ModelGenerationError: If model call fails
    """
    try:
        kwargs = _build_responses_kwargs(prompt_text, config or {}, stream=False)
        # Remove stream parameter for non-streaming call
        kwargs.pop("stream", None)
        
        def _call():
            return get_client().responses.create(**kwargs)
        
        response = _retry_api_call(_call)
        output_text = getattr(response, "output_text", None)
        if output_text is None:
            raise ModelGenerationError("Model response missing output_text")
        return output_text
    except Exception as e:
        logger.error(f"Model call failed: {e}", exc_info=True)
        raise ModelGenerationError(f"Failed to generate model response: {e}") from e

def stream_model_generator(prompt_text: str, config: Optional[Dict[str, Any]] = None) -> Generator[str, None, None]:
    """
    Stream model responses as a generator.
    
    Args:
        prompt_text: Input prompt text
        config: Configuration dictionary
    
    Yields:
        Text deltas from the model
    
    Raises:
        ModelGenerationError: If streaming fails
    """
    try:
        kwargs = _build_responses_kwargs(prompt_text, config or {}, stream=True)
        
        def _create_stream():
            return get_client().responses.create(**kwargs)
        
        # Use retry logic for stream creation (initial connection)
        stream = _retry_api_call(_create_stream)
        
        for event in stream:
            if getattr(event, "type", "") == "response.output_text.delta":
                delta = getattr(event, "delta", "")
                if delta:
                    yield delta
    except ModelGenerationError:
        # Re-raise ModelGenerationError as-is
        raise
    except Exception as e:
        logger.error(f"Model streaming failed: {e}", exc_info=True)
        raise ModelGenerationError(f"Failed to stream model response: {e}") from e


def stream_model(prompt_text: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Compatibility helper used by the Streamlit UI.

    Uses stream_model_generator internally.
    If Streamlit is available and has write_stream, it streams the response
    via st.write_stream and returns the full text. Otherwise it concatenates
    the chunks and returns them.
    
    Args:
        prompt_text: Input prompt text
        config: Configuration dictionary
    
    Returns:
        Full model response text
    """
    gen = stream_model_generator(prompt_text, config)

    if st is not None and hasattr(st, "write_stream"):
        return st.write_stream(gen)

    return "".join(gen)