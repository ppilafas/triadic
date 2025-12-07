"""
Topics Modal Module

Streamlit-specific UI components for the Topics dialog and topic selection functionality.
"""

import streamlit as st
from typing import Callable, List
from services.topic_generator import generate_topics
from utils.logging_config import get_logger

logger = get_logger(__name__)


@st.dialog(":material/lightbulb: Discussion Topics", width="large")
def topics_dialog(on_topic_select: Callable[[str], None]):
    """
    Dialog function for Topics - opens as modal.
    
    Args:
        on_topic_select: Callback function that takes a topic string as argument
    """
    # Header section
    st.caption("Select a topic to start the discussion")
    
    st.divider()
    
    # Check if topics exist in session state
    topics = st.session_state.get("topic_suggestions", [])
    
    # Generate Topics button
    st.markdown("#### :material/auto_awesome: Generate Topics")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        has_documents = bool(st.session_state.get("uploaded_file_index", {}))
        vector_store_id = st.session_state.get("vector_store_id")
        
        if st.button(
            "Generate Topics",
            icon=":material/auto_awesome:",
            use_container_width=True,
            type="primary",
            help="Generate discussion topics based on uploaded documents (if any)",
            key="dialog_generate_topics"
        ):
            with st.spinner("Generating topic suggestions..."):
                st.session_state.topic_suggestions = generate_topics(
                    has_documents=has_documents,
                    vector_store_id=vector_store_id
                )
            st.toast("Topic suggestions generated!", icon=":material/lightbulb:")
            # Keep dialog open after generating topics
            st.session_state.topics_dialog_open = True
            st.rerun()
    
    with col2:
        if topics and st.button(
            "Clear",
            icon=":material/clear:",
            use_container_width=True,
            help="Clear current topic suggestions",
            key="dialog_clear_topics"
        ):
            st.session_state.topic_suggestions = []
            st.toast("Topics cleared!", icon=":material/clear:")
            st.rerun()
    
    st.divider()
    
    # Display topics
    if topics:
        st.markdown("#### :material/chat: Select a Topic")
        st.caption(f"{len(topics)} topic(s) available")
        
        # Display topics in a grid layout
        topic_cols = st.columns(2)
        for idx, topic in enumerate(topics):
            col_idx = idx % 2
            with topic_cols[col_idx]:
                if st.button(
                    f":material/chat: {topic}",
                    key=f"dialog_topic_btn_{idx}",
                    use_container_width=True,
                    help=f"Start discussion about: {topic}"
                ):
                    # Store selected topic in session state
                    st.session_state._selected_topic = topic
                    # Ensure dialog won't reopen on next rerun
                    st.session_state.topics_dialog_open = False
                    # Close dialog by triggering rerun
                    st.rerun()
    else:
        st.info("Click 'Generate Topics' to create discussion topics based on your documents (if any).", icon=":material/info:")
    
    st.divider()
    
    # Close button
    if st.button("Close", icon=":material/close:", use_container_width=True, type="secondary"):
        st.rerun()


def render_topics_dialog(on_topic_select: Callable[[str], None]) -> None:
    """
    Check if dialog should be opened and call the dialog function.
    
    This function should be called in the main app flow to handle
    opening the topics dialog when requested.
    
    Args:
        on_topic_select: Callback function that takes a topic string as argument
    """
    # Initialize dialog state
    if "topics_dialog_open" not in st.session_state:
        st.session_state.topics_dialog_open = False
    
    # Open dialog if requested
    if st.session_state.topics_dialog_open:
        st.session_state.topics_dialog_open = False  # Reset flag
        topics_dialog(on_topic_select)  # Call the decorated dialog function

