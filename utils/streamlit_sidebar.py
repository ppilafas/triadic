"""
Streamlit Sidebar Components Module

Sidebar-specific UI components for the Triadic app.
Decoupled from utils/streamlit_ui.py for better organization.

Components:
- Main Controls (On Air, Trigger, Reboot)
- Knowledge Base (Documents & Topics)
"""

import time
import streamlit as st
from config import timing_config
from utils.logging_config import get_logger
from utils.streamlit_file_helpers import format_file_size, parse_file_key

logger = get_logger(__name__)


def render_sidebar_main_controls() -> bool:
    """
    Render main controls section in sidebar (On Air, Trigger, Reboot).
    
    Returns:
        True if "Trigger Next Turn" button was clicked, False otherwise
    """
    st.markdown("### :material/play_circle: Main Controls")
    
    # Check if at least one turn has been completed
    total_turns = st.session_state.get("total_turns", 0)
    has_completed_turn = total_turns > 0
    
    # On Air Toggle (disabled if no turns completed yet)
    auto_mode_prev = st.session_state.get("auto_mode", False)
    current_auto_mode = st.session_state.get("auto_mode", False)
    widget_key = "sidebar_auto_mode_toggle"
    
    # Allow disabling even if no turns completed, but prevent enabling
    can_enable = has_completed_turn or current_auto_mode
    
    # Render toggle
    # Note: Don't interact with widget key before rendering - causes Streamlit warnings
    # The widget's internal state (stored in the key) takes precedence over the value parameter
    toggle_value = st.toggle(
        "**On Air**",
        value=current_auto_mode,  # Default value from session state
        key=widget_key,
        disabled=not can_enable,
        help="Automatically trigger turns at specified cadence. Requires at least one completed turn." if not has_completed_turn else "Automatically trigger turns at specified cadence"
    )
    
    # Always update session state with widget value
    # The widget is the source of truth - it reflects user interaction
    st.session_state.auto_mode = toggle_value
    
    # Show info message if toggle is disabled
    if not has_completed_turn and not current_auto_mode:
        st.info("Complete at least one turn before enabling auto-run.", icon=":material/info:")
    
    # Handle state changes
    if st.session_state.auto_mode and not auto_mode_prev:
        # User just enabled auto-run
        logger.info("Auto-run mode enabled")
        
        # Clear stuck flags that could prevent auto-run from working
        if st.session_state.get("turn_in_progress", False):
            logger.warning("Clearing stuck turn_in_progress flag when enabling auto-run")
            st.session_state.turn_in_progress = False
            if "_turn_start_time" in st.session_state:
                del st.session_state._turn_start_time
        
        if st.session_state.get("pending_turn", False):
            logger.debug("Clearing pending_turn flag when enabling auto-run")
            st.session_state.pending_turn = False
        
        if "_auto_run_just_executed" in st.session_state:
            logger.debug("Clearing _auto_run_just_executed flag")
            del st.session_state._auto_run_just_executed
        
        st.toast("We are LIVE! Auto-run started.", icon=":material/broadcast_on_home:")
        st.rerun()
    elif not st.session_state.auto_mode and auto_mode_prev:
        # User just disabled auto-run
        logger.info("Auto-run mode disabled")
        
        # Clear pending_turn to allow manual input
        if st.session_state.get("pending_turn", False):
            logger.debug("Clearing pending_turn flag when disabling auto-run")
            st.session_state.pending_turn = False
        
        # Clear auto-run execution flags
        if "_auto_run_just_executed" in st.session_state:
            logger.debug("Clearing _auto_run_just_executed flag when disabling auto-run")
            del st.session_state._auto_run_just_executed
        
        st.toast("Broadcast paused.", icon=":material/pause_circle:")
    
    st.space(1)
    
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
        # Clear conversation summary on reboot
        if "conversation_summary" in st.session_state:
            del st.session_state.conversation_summary
        logger.info("System rebooted")
        st.toast("System rebooted!", icon=":material/restart_alt:")
        st.rerun()
    
    return manual_next


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
                file_name, file_size = parse_file_key(key)
                # Format file size if available
                file_size_str = f" ({format_file_size(file_size)})" if file_size is not None else ""
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

