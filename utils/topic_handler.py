"""
Topic Handler

Handles topic generation, selection, and dialog management.
"""

import time
import streamlit as st
from services.topic_generator import generate_topics
from utils.streamlit_topics import render_topics_dialog
from utils.streamlit_persistence import auto_save_session_state
from utils.logging_config import get_logger

logger = get_logger(__name__)


def handle_auto_topic_generation() -> None:
    """
    Handle auto topic generation after file indexing.
    
    Should be called in podcast_stage() to check for auto-generate flag.
    """
    if not st.session_state.get("_auto_generate_topics", False):
        return
    
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


def create_topic_selection_handler() -> callable:
    """
    Create a topic selection handler callback.
    
    Returns:
        Callback function that handles topic selection
    """
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
    
    return on_topic_select


def handle_topic_dialog() -> None:
    """
    Render topics dialog and handle topic selection.
    
    Should be called in podcast_stage() to manage topic dialog.
    """
    # Initialize topic suggestions if needed
    if "topic_suggestions" not in st.session_state:
        st.session_state.topic_suggestions = []
    
    # Create topic selection handler
    on_topic_select = create_topic_selection_handler()
    
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

