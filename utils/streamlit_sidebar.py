"""
Streamlit Sidebar Components Module

Sidebar-specific UI components for the Triadic app.
Decoupled from utils/streamlit_ui.py for better organization.

Components:
- Main Controls (On Air, Trigger, Reboot)
- Settings Link
- Knowledge Base (Documents & Topics)
"""

import streamlit as st
from config import timing_config
from utils.logging_config import get_logger

logger = get_logger(__name__)


def render_sidebar_main_controls() -> bool:
    """
    Render main controls section in sidebar (On Air, Trigger, Reboot).
    
    Returns:
        True if "Trigger Next Turn" button was clicked, False otherwise
    """
    st.markdown("### :material/play_circle: Main Controls")
    
    # Cadence slider (only show when On Air is active)
    if st.session_state.auto_mode:
        st.slider(
            "**Cadence** (seconds)",
            min_value=float(timing_config.MIN_AUTO_DELAY),
            max_value=float(timing_config.MAX_AUTO_DELAY),
            value=float(st.session_state.auto_delay),
            step=0.5,
            key="auto_delay_slider",
            help="Delay between automatic turns"
        )
    
    st.space(1)
    
    # Manual Controls
    manual_next = st.button(
        "Trigger Next Turn",
        icon=":material/play_arrow:",
        width='stretch',
        disabled=st.session_state.auto_mode,
        key="manual_next_button",
        help="Manually trigger the next AI turn (disabled when auto-run is on)"
    )
    
    if st.button(
        "Reboot System",
        icon=":material/restart_alt:",
        width='stretch',
        key="reboot_button",
        help="Reset conversation to initial state"
    ):
        st.session_state.show_messages = [st.session_state.show_messages[0]]
        st.session_state.next_speaker = "gpt_a"
        st.session_state.turn_in_progress = False
        st.session_state.total_turns = 0
        logger.info("System rebooted")
        st.toast("System rebooted!", icon=":material/restart_alt:")
        st.rerun()
    
    return manual_next


def render_sidebar_settings() -> None:
    """Render settings link in sidebar."""
    with st.expander(":material/settings: **Settings**", expanded=False):
        st.caption("Configure model, audio, and advanced features")
        if st.button("Open Settings", icon=":material/settings:", width='stretch', use_container_width=True):
            st.switch_page("pages/1_⚙️_Settings.py")


def render_sidebar_knowledge_base() -> None:
    """Render attached documents in the sidebar."""
    index_map = st.session_state.get("uploaded_file_index", {})
    
    if index_map:
        st.markdown("### :material/library_books: Attached Documents")
        indexed_count = len(index_map)
        
        # Show count badge
        st.caption(f"{indexed_count} document{'s' if indexed_count != 1 else ''} attached")
        
        # Display file list in expander
        with st.expander("View Documents", expanded=False):
            for key in list(index_map.keys()):
                file_name = key.split(":")[0] if ":" in key else key
                # Extract file size if available
                file_size_str = ""
                if ":" in key:
                    try:
                        file_size = int(key.split(":")[1])
                        if file_size > 1024 * 1024:
                            file_size_str = f" ({file_size / (1024 * 1024):.1f} MB)"
                        elif file_size > 1024:
                            file_size_str = f" ({file_size / 1024:.1f} KB)"
                        else:
                            file_size_str = f" ({file_size} B)"
                    except (ValueError, IndexError):
                        pass
                
                st.caption(f":material/description: {file_name}{file_size_str}")
        
        # Quick action to open Knowledge Base
        if st.button("Manage Documents", icon=":material/settings:", use_container_width=True, key="sidebar_manage_docs"):
            st.session_state.knowledge_base_dialog_open = True
            st.rerun()
    else:
        st.markdown("### :material/library_books: Documents")
        st.caption("No documents attached")
        if st.button("Add Documents", icon=":material/add:", use_container_width=True, key="sidebar_add_docs"):
            st.session_state.knowledge_base_dialog_open = True
            st.rerun()
    
    # Topics section (always shown under Documents)
    st.divider()
    st.markdown("### :material/lightbulb: Discussion Topics")
    
    topics = st.session_state.get("topic_suggestions", [])
    if topics:
        st.caption(f"{len(topics)} topic(s) available")
    else:
        st.caption("No topics generated yet")
    
    # Button to open topics dialog
    if st.button("Open Topics", icon=":material/lightbulb:", use_container_width=True, key="sidebar_open_topics"):
        st.session_state.topics_dialog_open = True
        st.rerun()

