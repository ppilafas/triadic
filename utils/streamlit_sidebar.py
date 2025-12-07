"""
Streamlit Sidebar Components Module

Sidebar-specific UI components for the Triadic app.
Decoupled from utils/streamlit_ui.py for better organization.

Components:
- Main Controls (On Air, Trigger, Reboot)
- Settings Link
- Knowledge Base (Documents & Topics)
"""

import time
import random
import streamlit as st
from config import timing_config
from services.topic_generator import generate_topics
from utils.logging_config import get_logger
from utils.streamlit_persistence import auto_save_session_state

logger = get_logger(__name__)


def render_sidebar_view_mode() -> None:
    """
    Render view mode toggle in sidebar (Bubbles vs IRC-style text).
    """
    st.markdown("### :material/view_module: View Mode")
    
    view_modes = {
        "bubbles": ":material/chat_bubble: Bubbles",
        "irc": ":material/code: IRC Text"
    }
    
    current_mode = st.session_state.get("view_mode", "bubbles")
    
    selected_mode = st.radio(
        "Display Style",
        options=list(view_modes.keys()),
        format_func=lambda x: view_modes[x],
        index=list(view_modes.keys()).index(current_mode) if current_mode in view_modes else 0,
        key="view_mode_radio",
        help="Choose between styled bubbles or IRC-style plain text view"
    )
    
    if selected_mode != current_mode:
        st.session_state.view_mode = selected_mode
        # Preserve auto-run waiting state when switching view modes
        # The delay logic will resume after rerun if conditions are met
        # No need to clear _auto_run_waiting - it will be handled in podcast_stage()
        logger.info(f"View mode switched from {current_mode} to {selected_mode}")
        st.rerun()


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
    
    # CRITICAL: Streamlit widgets with keys store their state in st.session_state[key]
    # We need to ensure the widget's key state is synced with auto_mode before rendering.
    # If auto_mode was restored from persistence, we must sync the widget key to match.
    widget_key = "sidebar_auto_mode_toggle"
    
    # Sync widget key state with auto_mode if they're out of sync
    # This ensures restored state (auto_mode=True) is reflected in the widget
    if widget_key in st.session_state:
        widget_state = st.session_state[widget_key]
        if widget_state != current_auto_mode:
            # Widget state is out of sync - update it to match session state
            # This happens when auto_mode was restored from persistence but widget key wasn't
            st.session_state[widget_key] = current_auto_mode
            logger.debug(f"Synced widget key {widget_key} to match auto_mode: {current_auto_mode}")
    
    # Allow disabling even if no turns completed, but prevent enabling
    can_enable = has_completed_turn or current_auto_mode
    
    # Render toggle - value parameter ensures it shows the correct state
    # The widget will update both its own key state and auto_mode
    toggle_value = st.toggle(
        "**On Air**",
        value=current_auto_mode,  # Explicitly set from session state (ensures restored state is shown)
        key=widget_key,
        disabled=not can_enable,
        help="Automatically trigger turns at specified cadence. Requires at least one completed turn." if not has_completed_turn else "Automatically trigger turns at specified cadence"
    )
    
    # Update session state with widget value (ensures they stay in sync)
    st.session_state.auto_mode = toggle_value
    
    # Show info message if toggle is disabled
    if not has_completed_turn and not current_auto_mode:
        st.info("Complete at least one turn before enabling auto-run.", icon=":material/info:")
    
    # Handle state changes
    if st.session_state.auto_mode and not auto_mode_prev:
        if has_completed_turn:
            # Clear any stuck waiting flags when enabling auto-run
            if "_auto_run_waiting" in st.session_state:
                del st.session_state._auto_run_waiting
            if "_auto_run_wait_start" in st.session_state:
                del st.session_state._auto_run_wait_start
            # Ensure turn_in_progress is not stuck
            if st.session_state.get("turn_in_progress", False):
                logger.warning("Clearing stuck turn_in_progress flag when enabling auto-run")
                st.session_state.turn_in_progress = False
                if "_turn_start_time" in st.session_state:
                    del st.session_state._turn_start_time
            # Clear pending_turn if stuck
            if st.session_state.get("pending_turn", False):
                logger.debug("Clearing pending_turn flag when enabling auto-run")
                st.session_state.pending_turn = False
            st.toast("We are LIVE! Auto-run started.", icon=":material/broadcast_on_home:")
            logger.info("Auto-run mode enabled - cleared all stuck flags")
            st.rerun()
        else:
            # Shouldn't happen due to disabled state, but handle gracefully
            st.session_state.auto_mode = False
            st.warning("Cannot enable auto-run: No turns completed yet.")
            logger.warning("Attempted to enable auto-run without completed turns")
    elif not st.session_state.auto_mode and auto_mode_prev:
        # Clear ALL waiting flags when disabling auto-run
        if "_auto_run_waiting" in st.session_state:
            del st.session_state._auto_run_waiting
        if "_auto_run_wait_start" in st.session_state:
            del st.session_state._auto_run_wait_start
        # Also clear pending_turn to allow manual input
        if st.session_state.get("pending_turn", False):
            st.session_state.pending_turn = False
        st.toast("Broadcast paused.", icon=":material/pause_circle:")
        logger.info("Auto-run mode disabled - cleared all waiting flags")
    
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
    
    # Start with Random Topic button
    if st.button(
        "Random Topic",
        icon=":material/casino:",
        use_container_width=True,
        key="sidebar_random_topic",
        help="Generate or select a random topic and start the discussion"
    ):
        # Check if we have existing topics
        if not topics:
            # Generate topics first
            with st.spinner("Generating topics..."):
                has_documents = bool(st.session_state.get("uploaded_file_index", {}))
                vector_store_id = st.session_state.get("vector_store_id")
                topics = generate_topics(
                    has_documents=has_documents,
                    vector_store_id=vector_store_id
                )
                st.session_state.topic_suggestions = topics
        
        # Select a random topic
        if topics:
            random_topic = random.choice(topics)
            
            # Inject the topic as a host message
            if "show_messages" not in st.session_state:
                st.session_state.show_messages = []
            
            st.session_state.show_messages.append({
                "speaker": "host",
                "content": f"Let's discuss: {random_topic}",
                "audio_bytes": None,
                "timestamp": time.strftime("%H:%M:%S"),
                "chars": len(f"Let's discuss: {random_topic}")
            })
            
            # Set pending turn to start the discussion
            st.session_state.pending_turn = True
            
            st.toast(f"Random topic injected: {random_topic}", icon=":material/casino:")
            logger.info(f"Random topic injected: {random_topic}")
            
            # Auto-save after topic injection
            auto_save_session_state()
            
            st.rerun()
        else:
            st.error("Failed to generate topics. Please try again.", icon=":material/error:")
    
    # Button to open topics dialog
    if st.button("Open Topics", icon=":material/lightbulb:", use_container_width=True, key="sidebar_open_topics"):
        st.session_state.topics_dialog_open = True
        st.rerun()

