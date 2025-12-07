"""
Knowledge Base Modal Module

Streamlit-specific UI components for the Knowledge Base dialog and file upload functionality.
"""

import streamlit as st
from typing import Optional
from ai_api import index_uploaded_files
from exceptions import FileIndexingError
from utils.logging_config import get_logger

logger = get_logger(__name__)


def _render_file_upload_tab() -> None:
    """Render file upload tab content."""
    # Track last processed files to avoid reprocessing
    if "last_processed_files" not in st.session_state:
        st.session_state.last_processed_files = set()
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Upload Documents",
        type=["pdf", "txt", "doc", "docx"],
        accept_multiple_files=True,
        help="Upload PDF, TXT, or DOC files to index in the vector store",
        key="knowledge_base_uploader"
    )
    
    # Handle file uploads (only process new files)
    if uploaded_files:
        # Check which files are new
        current_file_keys = {f"{f.name}:{f.size}" for f in uploaded_files}
        new_files = [
            f for f in uploaded_files 
            if f"{f.name}:{f.size}" not in st.session_state.last_processed_files
        ]
        
        if new_files:
            try:
                with st.spinner(f"Indexing {len(new_files)} file(s)..."):
                    index_uploaded_files(new_files, session_store=st.session_state)
                
                # Mark files as processed
                st.session_state.last_processed_files.update(current_file_keys)
                
                # Show success message
                file_names = [f.name for f in new_files]
                st.success(
                    f":material/check_circle: Indexed {len(new_files)} file(s): {', '.join(file_names[:3])}{'...' if len(file_names) > 3 else ''}", 
                    icon=":material/check_circle:"
                )
                st.toast(f"Successfully indexed {len(new_files)} document(s)!", icon=":material/library_books:")
                logger.info(f"Successfully indexed {len(new_files)} files: {file_names}")
                
                # Auto-generate topic suggestions based on newly indexed files
                vector_store_id = st.session_state.get("vector_store_id")
                if vector_store_id:
                    st.session_state._auto_generate_topics = True
                    logger.info(f"Flag set for auto-generating topic suggestions (vector_store_id: {vector_store_id})")
                else:
                    logger.warning("Cannot auto-generate topics: vector_store_id not found in session state")
                
                # Note: Dialog stays open after indexing so user can see success message
                # User can close it manually with the Close button
                
            except FileIndexingError as e:
                st.error(f":material/error: Failed to index files: {str(e)}", icon=":material/error:")
                logger.error(f"File indexing error: {e}", exc_info=True)
            except Exception as e:
                st.error(f":material/error: Unexpected error: {str(e)}", icon=":material/error:")
                logger.error(f"Unexpected error during file indexing: {e}", exc_info=True)
    
    # Show indexed files
    index_map = st.session_state.get("uploaded_file_index", {})
    if index_map:
        st.divider()
        st.markdown("#### :material/folder: Indexed Files")
        indexed_count = len(index_map)
        st.caption(f"{indexed_count} file(s) in knowledge base")
        
        # Display file list (show filename from key)
        for key in list(index_map.keys())[:10]:  # Show first 10
            file_name = key.split(":")[0] if ":" in key else key
            st.caption(f":material/description: {file_name}")
        
        if indexed_count > 10:
            st.caption(f"... and {indexed_count - 10} more")
        
        # Clear vector store button
        if st.button("Clear Knowledge Base", icon=":material/delete:", width='stretch'):
            st.session_state.uploaded_file_index = {}
            st.session_state.vector_store_id = None
            st.session_state.last_processed_files = set()
            st.toast("Knowledge base cleared!", icon=":material/delete:")
            logger.info("Knowledge base cleared by user")
            st.rerun()


@st.dialog(":material/library_books: Knowledge Base", width="large")
def knowledge_base_dialog():
    """Dialog function for Knowledge Base - opens as modal."""
    # Header section with professional styling
    st.caption("Upload documents to enhance AI responses with RAG")
    
    st.divider()
    
    # File upload section
    st.markdown("#### :material/upload: Upload Documents")
    _render_file_upload_tab()
    
    # Link to vector store management page
    st.divider()
    st.markdown("#### :material/storage: Vector Stores")
    st.caption("Manage vector stores in a dedicated page")
    st.info("Use the Vector Stores page to manage your vector stores. Close this dialog using the X button in the top-right corner.", icon=":material/info:")


def render_knowledge_base_dialog() -> None:
    """
    Check if dialog should be opened and call the dialog function.
    
    This function should be called in the main app flow to handle
    opening the knowledge base dialog when requested.
    
    Also detects when the dialog is closed via the native X button
    and triggers a rerun to refresh the UI.
    """
    # Initialize dialog state
    if "knowledge_base_dialog_open" not in st.session_state:
        st.session_state.knowledge_base_dialog_open = False
    
    # Track if dialog was active in previous render cycle
    prev_active_key = "_kb_dialog_prev_active"
    if prev_active_key not in st.session_state:
        st.session_state[prev_active_key] = False
    
    # Check if dialog was active before but is not being opened now
    # This indicates it was closed via the native X button
    was_active = st.session_state[prev_active_key]
    is_requested = st.session_state.knowledge_base_dialog_open
    
    # If dialog was active but is not requested now, it was closed
    if was_active and not is_requested:
        # Dialog was closed - trigger rerun to refresh UI
        # This rerun will also trigger topic generation if _auto_generate_topics flag is set
        logger.info("Knowledge base dialog closed - triggering rerun (may trigger topic generation)")
        st.session_state[prev_active_key] = False
        st.rerun()
        return
    
    # Update tracking state
    st.session_state[prev_active_key] = is_requested
    
    # Open dialog if requested
    if st.session_state.knowledge_base_dialog_open:
        st.session_state.knowledge_base_dialog_open = False  # Reset flag
        knowledge_base_dialog()  # Call the decorated dialog function

