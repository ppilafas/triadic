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

import os
import time
import streamlit as st

# Import centralized configuration
from config import get_openai_api_key

# Import logging
from utils.logging_config import get_logger, setup_logging

# Import UI components
from utils.streamlit_styles import inject_custom_css
from utils.streamlit_messages import render_message_history
from utils.streamlit_irc import render_irc_style_history
from utils.streamlit_chat_input import render_chat_input_container
from utils.streamlit_sidebar import (
    render_sidebar_main_controls,
    render_sidebar_knowledge_base,
    render_sidebar_view_mode
)
from utils.streamlit_knowledge_base import render_knowledge_base_dialog

# Import session management
from utils.streamlit_session import initialize_session_state, apply_default_settings
from utils.streamlit_persistence import auto_save_session_state

# Import authentication
from utils.streamlit_auth import require_auth, get_current_user

# Import business logic
from services.turn_executor import execute_turn
from utils.topic_handler import handle_auto_topic_generation, handle_topic_dialog
from utils.auto_run_manager import (
    check_and_resume_auto_run,
    handle_auto_run_delay,
    should_execute_auto,
    start_auto_run_delay
)

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

# Check if authentication is enabled (via environment variable or config)
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
st.session_state["auth_enabled"] = AUTH_ENABLED

# Require authentication (with guest option)
if not require_auth(allow_guest=True):
    st.stop()

# ---------- Initialization (before navigation) ----------

# Check for API key - dynamically check (allows Settings page to set it)
OPENAI_API_KEY = get_openai_api_key()

if not OPENAI_API_KEY:
    st.warning("**⚠️ OPENAI_API_KEY is missing.**", icon=":material/warning:")
    st.info("💡 You can add your API key in **Settings** page (click Settings in the sidebar).", icon=":material/info:")
    st.info("Alternatively, set it via Streamlit Cloud secrets or environment variables.", icon=":material/info:")
    logger.warning("OpenAI API key not found - user can set it in Settings")
    # Don't stop - allow user to navigate to Settings to add key

# Initialize session state (only once, before navigation)
# Note: Guest users won't have state restored (no persistence)
initialize_session_state()
apply_default_settings()

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
        
        # View mode toggle (Bubbles vs IRC-style)
        render_sidebar_view_mode()
        st.divider()
        
        # Main Controls
        manual_next = render_sidebar_main_controls()
        
        st.divider()
        
        # Knowledge Base
        render_sidebar_knowledge_base()
    
    # Store manual_next in session state for use in podcast_stage
    st.session_state._manual_next = manual_next
    
    # Run the podcast stage
    # NOTE: Chat input is rendered AFTER podcast_stage() to ensure it sees
    # the latest auto_mode state after all sidebar widgets have updated session state
    podcast_stage()
    
    # ========== INPUT CONTAINER (OUTSIDE FRAGMENT) ==========
    # CRITICAL: Render chat input OUTSIDE the fragment to ensure it always sees
    # the latest auto_mode state. Fragments can execute before widget state updates,
    # so checking auto_mode inside the fragment can see stale values on initial load.
    # By rendering outside the fragment, we ensure the check happens after all
    # sidebar widgets have updated session state.
    # 
    # Note: We've already read final_auto_mode above, but render_chat_input_container()
    # will also check internally for robustness.
    show_voice = st.session_state.get("show_voice_input", False)
    
    if show_voice:
        def on_transcription(text: str) -> None:
            """Handle voice transcription."""
            from utils.message_history import add_message_to_history
            add_message_to_history(
                speaker="host",
                content=text
            )
            # Set pending_turn flag instead of calling execute_turn() directly
            # This ensures message history is rendered first, then execute_turn() runs
            st.session_state.pending_turn = True
        
        def on_voice_cancel() -> None:
            """Handle voice input cancellation."""
            st.session_state.show_voice_input = False
        
        render_chat_input_container(
            show_voice_input=True,
            on_transcription=on_transcription,
            on_voice_cancel=on_voice_cancel
        )
    else:
        # Always call render_chat_input_container - it will check auto_mode internally
        # and show disabled message if needed
        render_chat_input_container(show_voice_input=False)

# Define pages with Material Symbols (using :material/icon_name: format)
pages = [
    st.Page(home_page, title="Home", icon=":material/podcasts:", default=True),
    st.Page("pages/1_⚙️_Settings.py", title="Settings", icon=":material/settings:"),
    st.Page("pages/2_🗄️_Vector_Stores.py", title="Vector Stores", icon=":material/storage:"),
    st.Page("pages/3_📊_Telemetry.py", title="Telemetry", icon=":material/analytics:"),
    st.Page("pages/4_📅_Timeline.py", title="Timeline", icon=":material/timeline:"),
]

# Create navigation (landing page is accessible via st.switch_page but not shown in sidebar)
current_page = st.navigation(pages, position="sidebar", expanded=True)


@st.fragment
def podcast_stage():
    """
    Main podcast stage UI using Streamlit 1.51+ fragment for performance.
    
    Note: This function is only called from home_page(), so when user navigates
    to Settings or other pages, this function stops running and auto-run pauses.
    When user returns to home page, this function resumes and auto-run continues.
    """
    # Render dialogs if open
    render_knowledge_base_dialog()
    
    # Clean up stuck state flags (safety check)
    # If turn_in_progress is stuck True but no actual turn is happening, reset it
    if st.session_state.get("turn_in_progress", False):
        # Check if this is a stuck flag (no actual turn happening)
        # This can happen if an error occurred or navigation interrupted a turn
        # We'll give it a grace period - if it's been stuck for more than 30 seconds, reset it
        if "_turn_start_time" not in st.session_state:
            # No start time recorded, likely stuck - reset it
            logger.warning("Detected stuck turn_in_progress flag (no start time) - resetting")
            st.session_state.turn_in_progress = False
        else:
            elapsed = time.time() - st.session_state._turn_start_time
            if elapsed > 30:  # More than 30 seconds is definitely stuck
                logger.warning(f"Detected stuck turn_in_progress flag (elapsed: {elapsed:.1f}s) - resetting")
                st.session_state.turn_in_progress = False
                if "_turn_start_time" in st.session_state:
                    del st.session_state._turn_start_time
    
    # Clean up auto-run state if auto-mode is disabled but flags are still set
    # This can happen if user toggled off auto-run but flags weren't cleared
    auto_mode = st.session_state.get("auto_mode", False)
    if not auto_mode:
        if "_auto_run_waiting" in st.session_state:
            del st.session_state._auto_run_waiting
        if "_auto_run_wait_start" in st.session_state:
            del st.session_state._auto_run_wait_start
    
    # Resume auto-run if we were waiting and delay has elapsed
    check_and_resume_auto_run()
    
    # Page header with dynamic summary
    st.header(":material/podcasts: Triadic • GPT-5.1 Podcast", divider="rainbow")
    
    # Show conversation summary if available
    conversation_summary = st.session_state.get("conversation_summary")
    if conversation_summary:
        st.info(f":material/summarize: **Discussion Progress:** {conversation_summary}", icon=":material/info:")
    else:
        st.caption("AI-to-AI Self-Dialogue • Powered by OpenAI GPT-5")
    
    # Handle auto topic generation and dialog
    handle_auto_topic_generation()
    handle_topic_dialog()
    
    # Check for pending turns BEFORE entering containers
    pending_turn = st.session_state.get("pending_turn", False) and not st.session_state.turn_in_progress
    manual_next = st.session_state.get("_manual_next", False)
    should_execute_auto_flag = should_execute_auto()
    
    # ========== SCROLLABLE CHAT AREA ==========
    # Use native Streamlit container with height parameter for independent scrolling
    # Height set to fill most of viewport (700px works well for most screens)
    # This container is ONLY for chat bubbles
    with st.container(height=700):
        # Render message history FIRST to establish proper DOM order
        # This ensures all historical messages (including newly added host message) are rendered
        # before any new streaming bubbles from execute_turn()
        # Route to appropriate renderer based on view mode (decoupled)
        view_mode = st.session_state.get("view_mode", "bubbles")
        if view_mode == "irc":
            render_irc_style_history(st.session_state.show_messages)
            # Create streaming container for IRC mode (will be updated during execute_turn)
            streaming_container = st.empty()
            st.session_state.irc_streaming_container = streaming_container
        else:
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
                # Only rerun if a message was actually added (prevents unnecessary reruns)
                if st.session_state.get("_last_turn_message_added", False):
                    st.rerun()
                    st.session_state._last_turn_message_added = False
            else:
                # Host message not found, clear flag and log warning
                logger.warning("Pending turn but host message not found in show_messages")
                st.session_state.pending_turn = False
        
        if manual_next and not st.session_state.turn_in_progress:
            execute_turn()
            # Clear the flag so it doesn't trigger again
            st.session_state._manual_next = False
            # Only rerun if a message was actually added (prevents unnecessary reruns)
            if st.session_state.get("_last_turn_message_added", False):
                st.rerun()
                st.session_state._last_turn_message_added = False

        if should_execute_auto_flag:
            # Execute turn inside container for auto-mode
            execute_turn()
            # Rerun immediately to show the turn execution (streaming, etc.)
            if st.session_state.get("_last_turn_message_added", False):
                # Mark that we need to wait for delay before next auto-run
                start_auto_run_delay()
                st.session_state._last_turn_message_added = False
                st.rerun()
    
    # Handle auto-mode delay OUTSIDE container (after container is rendered)
    # Note: This logic only runs when podcast_stage() is called, which only happens on home page
    # When user navigates to Settings or other pages, this code doesn't run, so auto-run pauses
    # When user returns to home page, check_and_resume_auto_run() handles resuming if delay elapsed
    # This function continues waiting if delay hasn't elapsed yet
    handle_auto_run_delay()
    
    # NOTE: Chat input rendering has been moved OUTSIDE the fragment to home_page()
    # This ensures it always sees the latest auto_mode state after sidebar widgets update

# ---------- Run Current Page ----------

# Run the selected page
current_page.run()
