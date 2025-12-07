# app.py
#
# Triadic • GPT-5.1 Self-Dialogue Monolith
# "WhatsApp Style" Edition (Streamlit 1.51+)
#
# Features:
# - UI: Color-coded Chat Bubbles (Host=Green, A=Blue, B=Red)
# - CORE: Real Whisper, Live Altair, Reactive Trigger
# - SAFE: Reasoning Summary disabled by default
# - NATIVE: Phase 3 - Full native Streamlit alignment enabled
#
# Run via: ./bootstrap.sh

import time
from typing import List, Dict, Optional, Any
import streamlit as st

# Import internal modules
from tts import tts_stream_to_bytes
from ai_api import call_model, stream_model, ModelGenerationError, index_uploaded_files, ensure_vector_store
from exceptions import TranscriptionError, FileIndexingError

# Import centralized configuration
from config import (
    model_config,
    timing_config,
    OPENAI_API_KEY
)
from utils.logging_config import get_logger, setup_logging
from core.message_builder import build_prompt_from_messages
from core.conversation import get_next_speaker_key
from utils.streamlit_ui import (
    SPEAKER_INFO,
    VOICE_FOR_SPEAKER,
    inject_custom_css,
    autoplay_audio,
    transcribe_streamlit_audio,
    render_styled_bubble,
    render_streaming_bubble,
    update_streaming_bubble,
    get_settings,
    render_top_controls,
    render_message_history,
    render_text_input,
    render_voice_input,
    render_app_banner
)
from utils.streamlit_sidebar import (
    render_sidebar_main_controls,
    render_sidebar_knowledge_base
)
from utils.streamlit_knowledge_base import render_knowledge_base_dialog
from utils.streamlit_topics import render_topics_dialog
from utils.streamlit_session import initialize_session_state, apply_default_settings
from services.topic_generator import generate_topics

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# ---------- Streamlit Page Setup ----------

st.set_page_config(
    page_title="Triadic • GPT-5.1",
    page_icon=":material/podcasts:",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.logo("https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/ChatGPT_logo.svg/1024px-ChatGPT_logo.svg.png", icon_image=None)

# Inject CSS on app load
inject_custom_css()

# ---------- Authentication (before initialization) ----------
from utils.streamlit_auth import require_auth, get_current_user

# Check if authentication is enabled (via environment variable or config)
import os
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
st.session_state["auth_enabled"] = AUTH_ENABLED

# Require authentication (with guest option)
if not require_auth(allow_guest=True):
    st.stop()

# ---------- Initialization (before navigation) ----------

if not OPENAI_API_KEY:
    st.error("**OPENAI_API_KEY** is missing.", icon=":material/error:")
    logger.error("OpenAI API key not found in environment")
    st.stop()

# Initialize session state (only once, before navigation)
# Note: Guest users won't have state restored (no persistence)
initialize_session_state()
apply_default_settings()

# Import persistence for auto-save
from utils.streamlit_persistence import auto_save_session_state

# ---------- Navigation Setup ----------


def home_page():
    """Main podcast stage page."""
    # Render sidebar controls only on home page
    with st.sidebar:
        st.title(":material/tune: Control Deck")
        
        # Show user info if authenticated (not guest)
        user = get_current_user()
        is_guest = st.session_state.get("is_guest", False)
        if user and not is_guest:
            st.caption(f"**User:** {user.get('name', user.get('username', 'Unknown'))}")
        elif is_guest:
            st.caption(":material/person_off: **Guest Mode** (no persistence)")
        
        st.divider()
        
        # Main Controls
        manual_next = render_sidebar_main_controls()
        
        st.divider()
        
        # Knowledge Base
        render_sidebar_knowledge_base()
    
    # Store manual_next in session state for use in podcast_stage
    st.session_state._manual_next = manual_next
    
    # Run the podcast stage
    podcast_stage()

# Define pages with Material Symbols (using :material/icon_name: format)
pages = [
    st.Page(home_page, title="Home", icon=":material/podcasts:", default=True),
    st.Page("pages/1_⚙️_Settings.py", title="Settings", icon=":material/settings:"),
    st.Page("pages/2_🗄️_Vector_Stores.py", title="Vector Stores", icon=":material/storage:"),
    st.Page("pages/3_📊_Telemetry.py", title="Telemetry", icon=":material/analytics:"),
]

# Create navigation (landing page is accessible via st.switch_page but not shown in sidebar)
current_page = st.navigation(pages, position="sidebar", expanded=True)

def execute_turn() -> None:
    """Execute one AI turn with proper error handling and logging."""
    if st.session_state.get("turn_in_progress", False):
        return

    st.session_state.turn_in_progress = True
    start_time = time.time()
    
    try:
        speaker = st.session_state.next_speaker
        speaker_meta = SPEAKER_INFO[speaker]
        settings = get_settings()
        
        logger.info(f"Executing turn for {speaker} with model {settings['model_name']}")
        
        # Ensure vector store exists (will be created if needed) - must be done before tool detection
        try:
            vs_id = ensure_vector_store(st.session_state)
        except Exception as e:
            logger.warning(f"Vector store not available: {e}")
            vs_id = None
        
        # Determine available tools for prompt enhancement
        available_tools = []
        if vs_id:
            available_tools.append("file_search")
        web_search_enabled = settings.get("web_search_enabled", False)
        logger.info(f"Web search enabled: {web_search_enabled} (from settings: {settings.get('web_search_enabled')}, session_state: {st.session_state.get('web_search_enabled', 'not set')})")
        if web_search_enabled:
            available_tools.append("web_search")
        
        prompt = build_prompt_from_messages(speaker, st.session_state.show_messages, available_tools=available_tools)
        
        # Build config dict for ai_api
        api_config = {
            "model_name": settings["model_name"],
            "reasoning_effort": settings["reasoning_effort"],
            "web_search_enabled": settings.get("web_search_enabled", False),
            "text_verbosity": settings.get("text_verbosity", "medium"),
            "reasoning_summary_enabled": settings.get("reasoning_summary_enabled", False),
            "vector_store_id": vs_id  # Include vector store ID for RAG
        }
        
        # Get avatar path (supports both custom PNG and Material Symbols)
        # Use get_avatar_path to ensure proper avatar resolution
        from utils.streamlit_ui import get_avatar_path
        avatar = get_avatar_path(speaker)
        role = "user" if speaker == "host" else "assistant"
        
        with st.chat_message(role, avatar=avatar):
            # Show speaker label immediately (before streaming starts)
            header_cols = st.columns([3, 1])
            with header_cols[0]:
                speaker_label = speaker_meta.get("full_label", speaker)
                st.caption(f"**{speaker_label}**")
            with header_cols[1]:
                timestamp = time.strftime("%H:%M:%S")
                st.caption(f"`{timestamp}`")
            
            ai_text = ""
            tts_bytes = None

            try:
                if settings["stream_enabled"]:
                    # Create streaming bubble container for real-time updates
                    bubble_container = render_streaming_bubble(speaker)
                    
                    # Stream tokens with batched updates for better performance
                    from ai_api import stream_model_generator
                    token_gen = stream_model_generator(prompt, config=api_config)
                
                    # Batch updates for smoother performance (update every 5 tokens)
                    token_buffer = []
                    BATCH_SIZE = 5
                    
                    try:
                        for token in token_gen:
                            token_buffer.append(token)
                            # Update bubble in batches for better performance
                            if len(token_buffer) >= BATCH_SIZE:
                                ai_text += ''.join(token_buffer)
                                update_streaming_bubble(bubble_container, ai_text, speaker, show_cursor=True)
                                token_buffer = []
                        
                        # Final update with any remaining tokens
                        if token_buffer:
                            ai_text += ''.join(token_buffer)
                    finally:
                        # After streaming completes, update bubble one final time without cursor
                        if ai_text:
                            update_streaming_bubble(bubble_container, ai_text, speaker, show_cursor=False)
                        # Don't clear the bubble container - leave it as-is to avoid unnecessary rerun
                        # The streaming bubble already shows the final content, so no need to rerun immediately
                        # It will be replaced by render_message_history on the next natural rerun (user interaction, etc.)
                else:
                    ai_text = call_model(prompt, config=api_config)
                    # For non-streaming, render the bubble immediately
                    render_styled_bubble(ai_text, speaker)
                
                logger.info(f"Generated response: {len(ai_text)} characters")

            except ModelGenerationError as e:
                logger.error(f"Model generation failed: {e}", exc_info=True)
                # Show error directly in styled bubble
                render_styled_bubble(f"**Error:** {str(e)}\n\nPlease try again or adjust your settings.", speaker)
                ai_text = f"(Error: {str(e)})"
            
            # TTS generation (silent, no progress indicators)
            if settings["tts_enabled"] and ai_text and "(Error" not in ai_text:
                try:
                    voice = VOICE_FOR_SPEAKER.get(speaker, "alloy")
                    tts_bytes = tts_stream_to_bytes(ai_text, voice=voice)
                    logger.info(f"TTS generated: {len(tts_bytes)} bytes")
                except Exception as e:
                    logger.error(f"TTS generation failed: {e}", exc_info=True)

            if tts_bytes:
                st.audio(tts_bytes, format="audio/mp3")
                if settings["tts_autoplay"]:
                    autoplay_audio(tts_bytes)

        elapsed = time.time() - start_time
        st.session_state.last_latency = f"{elapsed:.2f}s"
        st.session_state.total_turns += 1
        
        # Add message to history AFTER streaming completes (ensures proper ordering)
        # Only add if not already in history (prevents duplicates on rerun)
        if ai_text and not ai_text.startswith("(Error"):
            # Check if this message is already in history (by content and speaker)
            message_already_exists = any(
                m.get("speaker") == speaker and m.get("content") == ai_text
                for m in st.session_state.show_messages
            )
            if not message_already_exists:
                st.session_state.show_messages.append({
                    "speaker": speaker,
                    "content": ai_text,
                    "audio_bytes": tts_bytes,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "chars": len(ai_text)
                })
        
        st.session_state.next_speaker = get_next_speaker_key(speaker)

        logger.info(f"Turn completed: {speaker} responded with {len(ai_text)} characters in {elapsed:.2f}s")
        
        # Auto-save session state after turn completion
        auto_save_session_state()

    except Exception as e:
        logger.error(f"Unexpected error in execute_turn: {e}", exc_info=True)
        st.error("**System Error:** An unexpected error occurred. Please check the logs.", icon=":material/error:")
    finally:
        st.session_state.turn_in_progress = False

@st.fragment
def podcast_stage():
    """Main podcast stage UI using Streamlit 1.51+ fragment for performance."""
    # Render dialogs if open
    render_knowledge_base_dialog()
    
    # Initialize topic suggestions in session state
    if "topic_suggestions" not in st.session_state:
        st.session_state.topic_suggestions = []
    
    # Handle auto topic generation after file indexing
    if st.session_state.get("_auto_generate_topics", False):
        logger.info("Auto-generate topics flag detected - generating topic suggestions...")
        st.session_state._auto_generate_topics = False
        with st.spinner("Updating topic suggestions based on new documents..."):
            has_documents = bool(st.session_state.get("uploaded_file_index", {}))
            vector_store_id = st.session_state.get("vector_store_id")
            logger.info(f"Generating topics: has_documents={has_documents}, vector_store_id={vector_store_id}")
            st.session_state.topic_suggestions = generate_topics(
                has_documents=has_documents,
                vector_store_id=vector_store_id
            )
        st.toast("Topic suggestions updated! Opening topics dialog...", icon=":material/lightbulb:")
        logger.info(f"Auto-generated {len(st.session_state.topic_suggestions)} topic suggestions after file indexing")
        # Auto-save after topic generation
        auto_save_session_state()
        # Auto-open topics dialog after generation
        st.session_state.topics_dialog_open = True
        st.rerun()
    
    # Topic selection handler
    def on_topic_select(topic: str) -> None:
        """Handle topic selection."""
        st.session_state.show_messages.append({
            "speaker": "host",
            "content": f"Let's discuss: {topic}",
            "audio_bytes": None,
            "timestamp": time.strftime("%H:%M:%S"),
            "chars": len(f"Let's discuss: {topic}")
        })
        st.toast(f"Topic injected: {topic}", icon=":material/send:")
        logger.info(f"Topic injected: {topic}")
        st.session_state.pending_turn = True
        # Don't execute turn in the same cycle - rerun first to render the host message
        st.rerun()
    
    # Render topics dialog if requested (check BEFORE processing selection)
    # This ensures dialog closes before we process the topic
    render_topics_dialog(on_topic_select)
    
    # Handle topic selection from dialog (AFTER dialog render check)
    # This ensures dialog is closed before we process the selection
    if st.session_state.get("_selected_topic"):
        selected_topic = st.session_state._selected_topic
        del st.session_state._selected_topic  # Clear the flag immediately
        # Process topic selection (this will trigger rerun)
        on_topic_select(selected_topic)
        # Auto-save after topic selection
        auto_save_session_state()
    
    # Check for pending turns BEFORE entering containers
    pending_turn = st.session_state.get("pending_turn", False) and not st.session_state.turn_in_progress
    manual_next = st.session_state.get("_manual_next", False)
    # Auto-run requires: auto_mode enabled, not in progress, and has messages to continue
    has_messages = len(st.session_state.get("show_messages", [])) > 0
    should_execute_auto = st.session_state.auto_mode and not st.session_state.turn_in_progress and has_messages
    
    # ========== TOP CONTROLS CONTAINER ==========
    # Container for On Air toggle above the chat area
    with st.container():
        render_top_controls()
    
    # ========== SCROLLABLE CHAT AREA ==========
    # Use native Streamlit container with height parameter for independent scrolling
    # Height set to fill most of viewport (700px works well for most screens)
    # This container is ONLY for chat bubbles
    with st.container(height=700):
        # Render message history FIRST to establish proper DOM order
        # This ensures all historical messages (including newly added host message) are rendered
        # before any new streaming bubbles from execute_turn()
        render_message_history(st.session_state.show_messages)
        
        # Execute turn INSIDE container so streaming messages appear in scrollable area
        # This ensures all new messages (including streaming) are within the scrollable container
        
        if pending_turn:
            # Verify that the host message was actually added (safety check)
            if st.session_state.show_messages and st.session_state.show_messages[-1].get("speaker") == "host":
                # Clear the flag BEFORE executing to prevent re-execution on rerun
                st.session_state.pending_turn = False
                # Execute turn - this will create streaming bubble inside the container
                execute_turn()
            else:
                # Host message not found, clear flag and log warning
                logger.warning("Pending turn but host message not found in show_messages")
                st.session_state.pending_turn = False
        
        if manual_next and not st.session_state.turn_in_progress:
            execute_turn()
            # Clear the flag so it doesn't trigger again
            st.session_state._manual_next = False

        if should_execute_auto:
            # Execute turn inside container for auto-mode
            execute_turn()
    
    # Handle auto-mode rerun OUTSIDE container (after container is rendered)
    # This is the original working approach: simple time.sleep + st.rerun
    if should_execute_auto and not st.session_state.turn_in_progress:
        # Only rerun if turn completed (not still streaming)
        # Use the original blocking approach - it works in Streamlit
        time.sleep(st.session_state.auto_delay)
        # Re-check auto_mode after delay (user might have disabled it)
        if st.session_state.auto_mode:
            st.rerun()

    # ========== INPUT CONTAINER ==========
    # Native Streamlit way: Only render chat input when not in auto-mode
    # When auto-mode is enabled, chat input is completely hidden (not rendered)
    if not st.session_state.auto_mode:
        # Use native Streamlit container with CSS class for styling
        # This is more native than raw HTML divs
        chat_input_container = st.container()
        
        # Apply CSS class via markdown (still needed for fixed positioning)
        # But we use st.container() for better structure
        with chat_input_container:
            chat_input_container.markdown(
                '<div class="fixed-chat-input-container">',
                unsafe_allow_html=True
            )
            
            st.divider()
            
            # Check if we should show voice input or text input
            show_voice = st.session_state.get("show_voice_input", False)
            
            if show_voice:
                def on_transcription(text: str) -> None:
                    """Handle voice transcription."""
                    st.session_state.show_messages.append({
                        "speaker": "host",
                        "content": text,
                        "audio_bytes": None,
                        "timestamp": time.strftime("%H:%M:%S"),
                        "chars": len(text)
                    })
                    # Set pending_turn flag instead of calling execute_turn() directly
                    # This ensures message history is rendered first, then execute_turn() runs
                    st.session_state.pending_turn = True
                
                def on_voice_cancel() -> None:
                    """Handle voice input cancellation."""
                    st.session_state.show_voice_input = False
                
                render_voice_input(
                    on_transcription=on_transcription,
                    on_cancel=on_voice_cancel
                )
            else:
                def on_message(text: str) -> None:
                    """Handle text message."""
                    st.session_state.show_messages.append({
                        "speaker": "host",
                        "content": text,
                        "audio_bytes": None,
                        "timestamp": time.strftime("%H:%M:%S"),
                        "chars": len(text)
                    })
                    # Set pending_turn flag instead of calling execute_turn() directly
                    # This ensures message history is rendered first, then execute_turn() runs
                    st.session_state.pending_turn = True
                
                def on_voice_toggle() -> None:
                    """Handle voice toggle."""
                    st.session_state.show_voice_input = True
                
                render_text_input(
                    on_message=on_message,
                    on_voice_toggle=on_voice_toggle
                )
            
            chat_input_container.markdown('</div>', unsafe_allow_html=True)

# ---------- Run Current Page ----------

# Run the selected page
current_page.run()
