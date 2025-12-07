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
    
    current_mode = st.session_state.get("view_mode", "irc")
    
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
    # DEBUG: Print to ensure function is called
    # Use both print and logger, and also write to stderr to ensure visibility
    import sys
    import os
    
    # Force flush to ensure output appears immediately
    print("=" * 80, file=sys.stderr, flush=True)
    print("[AUTO-RUN TOGGLE] render_sidebar_main_controls() CALLED", file=sys.stderr, flush=True)
    print("=" * 80, file=sys.stderr, flush=True)
    print("=" * 80, flush=True)
    print("[AUTO-RUN TOGGLE] render_sidebar_main_controls() CALLED", flush=True)
    print("=" * 80, flush=True)
    
    # Also write directly to a file as a backup
    try:
        with open("/tmp/triadic_auto_run.log", "a") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] render_sidebar_main_controls() CALLED\n")
            f.flush()
    except Exception:
        pass
    
    logger.info("=" * 80)
    logger.info("[AUTO-RUN TOGGLE] render_sidebar_main_controls() CALLED")
    logger.info("=" * 80)
    
    st.markdown("### :material/play_circle: Main Controls")
    
    # Check if at least one turn has been completed
    total_turns = st.session_state.get("total_turns", 0)
    has_completed_turn = total_turns > 0
    
    # On Air Toggle (disabled if no turns completed yet)
    auto_mode_prev = st.session_state.get("auto_mode", False)
    current_auto_mode = st.session_state.get("auto_mode", False)
    widget_key = "sidebar_auto_mode_toggle"
    
    import sys
    print(f"[AUTO-RUN TOGGLE] Initial state: auto_mode_prev={auto_mode_prev}, current_auto_mode={current_auto_mode}", file=sys.stderr, flush=True)
    print(f"[AUTO-RUN TOGGLE] Widget key state: {widget_key}={st.session_state.get(widget_key, 'NOT SET')}", file=sys.stderr, flush=True)
    print(f"[AUTO-RUN TOGGLE] Has completed turn: {has_completed_turn}", file=sys.stderr, flush=True)
    logger.info(f"[AUTO-RUN TOGGLE] Initial state: auto_mode_prev={auto_mode_prev}, current_auto_mode={current_auto_mode}")
    logger.info(f"[AUTO-RUN TOGGLE] Widget key state: {widget_key}={st.session_state.get(widget_key, 'NOT SET')}")
    logger.info(f"[AUTO-RUN TOGGLE] Has completed turn: {has_completed_turn}")
    
    # CRITICAL: Streamlit widgets with keys store their state in st.session_state[key]
    # The widget's internal state (stored in the key) takes precedence over the value parameter.
    # 
    # Problem: If the widget key exists with a conflicting value, it can prevent the toggle
    # from working even when the user tries to change it.
    #
    # Solution: 
    # 1. If auto_mode is True (from restoration), ensure widget key matches (sync it)
    # 2. If auto_mode is False and widget key exists but conflicts, clear it to let value parameter work
    # 3. This ensures the widget can be toggled normally by user interaction
    
    # Allow disabling even if no turns completed, but prevent enabling
    can_enable = has_completed_turn or current_auto_mode
    import sys
    print(f"[AUTO-RUN TOGGLE] Can enable: {can_enable} (has_completed_turn={has_completed_turn}, current_auto_mode={current_auto_mode})", file=sys.stderr, flush=True)
    logger.info(f"[AUTO-RUN TOGGLE] Can enable: {can_enable} (has_completed_turn={has_completed_turn}, current_auto_mode={current_auto_mode})")
    
    # Render toggle
    # CRITICAL: Don't interact with widget key before rendering - causes Streamlit warnings
    # Just render with value parameter and let Streamlit manage the widget key automatically
    # If widget key exists, it will take precedence; if not, value parameter is used
    print(f"[AUTO-RUN TOGGLE] Rendering toggle with value={current_auto_mode}, disabled={not can_enable}", file=sys.stderr, flush=True)
    logger.info(f"[AUTO-RUN TOGGLE] Rendering toggle with value={current_auto_mode}, disabled={not can_enable}")
    toggle_value = st.toggle(
        "**On Air**",
        value=current_auto_mode,  # Default value from session state
        key=widget_key,
        disabled=not can_enable,
        help="Automatically trigger turns at specified cadence. Requires at least one completed turn." if not has_completed_turn else "Automatically trigger turns at specified cadence"
    )
    
    print(f"[AUTO-RUN TOGGLE] Toggle rendered, returned value: {toggle_value}", file=sys.stderr, flush=True)
    print(f"[AUTO-RUN TOGGLE] Widget key after render: {widget_key}={st.session_state.get(widget_key, 'NOT SET')}", file=sys.stderr, flush=True)
    logger.info(f"[AUTO-RUN TOGGLE] Toggle rendered, returned value: {toggle_value}")
    logger.info(f"[AUTO-RUN TOGGLE] Widget key after render: {widget_key}={st.session_state.get(widget_key, 'NOT SET')}")
    
    # CRITICAL: Always update session state with widget value
    # The widget is the source of truth - it reflects user interaction
    auto_mode_before_update = st.session_state.get("auto_mode", False)
    st.session_state.auto_mode = toggle_value
    auto_mode_after_update = st.session_state.auto_mode
    
    print(f"[AUTO-RUN TOGGLE] State update: {auto_mode_before_update} -> {auto_mode_after_update} (toggle_value={toggle_value})", file=sys.stderr, flush=True)
    logger.info(f"[AUTO-RUN TOGGLE] Updated session state: auto_mode={auto_mode_after_update} (was {auto_mode_before_update})")
    
    # Check if toggle value changed from what we expected
    if toggle_value != current_auto_mode:
        print(f"[AUTO-RUN TOGGLE] ⚠️ TOGGLE VALUE CHANGED: {current_auto_mode} -> {toggle_value}", file=sys.stderr, flush=True)
        logger.info(f"[AUTO-RUN TOGGLE] Toggle value changed: {current_auto_mode} -> {toggle_value}")
    
    # Show info message if toggle is disabled
    if not has_completed_turn and not current_auto_mode:
        st.info("Complete at least one turn before enabling auto-run.", icon=":material/info:")
    
    # Handle state changes
    import sys
    print(f"[AUTO-RUN TOGGLE] Checking state change: auto_mode={st.session_state.auto_mode}, auto_mode_prev={auto_mode_prev}", file=sys.stderr, flush=True)
    logger.info(f"[AUTO-RUN TOGGLE] Checking state change: auto_mode={st.session_state.auto_mode}, auto_mode_prev={auto_mode_prev}")
    
    if st.session_state.auto_mode and not auto_mode_prev:
        # User just enabled auto-run
        import sys
        print("=" * 80, file=sys.stderr, flush=True)
        print("[AUTO-RUN TOGGLE] *** USER ENABLED AUTO-RUN ***", file=sys.stderr, flush=True)
        print("=" * 80, file=sys.stderr, flush=True)
        print("=" * 80, flush=True)
        print("[AUTO-RUN TOGGLE] *** USER ENABLED AUTO-RUN ***", flush=True)
        print("=" * 80, flush=True)
        logger.info("=" * 60)
        logger.info("[AUTO-RUN TOGGLE] *** USER ENABLED AUTO-RUN ***")
        logger.info("=" * 60)
        
        # Write to file
        try:
            with open("/tmp/triadic_auto_run.log", "a") as f:
                f.write(f"[{time.strftime('%H:%M:%S')}] *** USER ENABLED AUTO-RUN ***\n")
                f.flush()
        except Exception:
            pass
        
        # CRITICAL: The safeguard logic must match the can_enable logic
        # can_enable = has_completed_turn or current_auto_mode
        # If the toggle was enabled (not disabled), it means can_enable was True
        # Since the toggle is the source of truth and was enabled, we should trust it
        # 
        # However, we still validate: if has_completed_turn is False, we need to ensure
        # that current_auto_mode was True (which allowed the toggle to be enabled)
        # But since auto_mode is now True (user just enabled it), the condition is met
        
        # Validate: The toggle should only be enabled if can_enable was True
        # can_enable = has_completed_turn or current_auto_mode
        # Since auto_mode is now True, can_enable would be True regardless
        # But to be safe, we still check has_completed_turn for the initial requirement
        # However, if the toggle was enabled, we trust it (the disabled attribute prevented invalid clicks)
        
        # Ensure turn_in_progress is not stuck (simple cleanup)
        if st.session_state.get("turn_in_progress", False):
            logger.warning("[AUTO-RUN TOGGLE] Clearing stuck turn_in_progress flag when enabling auto-run")
            st.session_state.turn_in_progress = False
            if "_turn_start_time" in st.session_state:
                del st.session_state._turn_start_time
        
        # Clear pending_turn if stuck
        if st.session_state.get("pending_turn", False):
            logger.info("[AUTO-RUN TOGGLE] Clearing pending_turn flag when enabling auto-run")
            st.session_state.pending_turn = False
        
        # Clear auto-run execution flags if they exist
        if "_auto_run_just_executed" in st.session_state:
            logger.info("[AUTO-RUN TOGGLE] Clearing _auto_run_just_executed flag")
            del st.session_state._auto_run_just_executed
        
        # Only show warning if has_completed_turn is False (but still allow it)
        # This handles the case where auto_mode was True from restoration, allowing toggle to be enabled
        if not has_completed_turn:
            logger.info("[AUTO-RUN TOGGLE] Auto-run enabled without completed turns (likely from restored state)")
        
        # Log current state for debugging
        has_messages = len(st.session_state.get("show_messages", [])) > 0
        turn_in_progress = st.session_state.get("turn_in_progress", False)
        just_executed = st.session_state.get("_auto_run_just_executed", False)
        
        import sys
        print(f"[AUTO-RUN TOGGLE] Current state: has_messages={has_messages}, turn_in_progress={turn_in_progress}, just_executed={just_executed}", file=sys.stderr, flush=True)
        print(f"[AUTO-RUN TOGGLE] Total turns: {st.session_state.get('total_turns', 0)}", file=sys.stderr, flush=True)
        logger.info(f"[AUTO-RUN TOGGLE] Current state: has_messages={has_messages}, turn_in_progress={turn_in_progress}, just_executed={just_executed}")
        logger.info(f"[AUTO-RUN TOGGLE] Total turns: {st.session_state.get('total_turns', 0)}")
        
        # Calculate what should_execute_auto would be
        should_execute = (
            st.session_state.auto_mode and 
            not turn_in_progress and 
            has_messages and
            not just_executed
        )
        print(f"[AUTO-RUN TOGGLE] Should execute auto-run: {should_execute}", file=sys.stderr, flush=True)
        logger.info(f"[AUTO-RUN TOGGLE] Should execute auto-run: {should_execute}")
        
        st.toast("We are LIVE! Auto-run started.", icon=":material/broadcast_on_home:")
        logger.info("[AUTO-RUN TOGGLE] Auto-run mode enabled - cleared all stuck flags - triggering rerun")
        st.rerun()
    elif not st.session_state.auto_mode and auto_mode_prev:
        # User just disabled auto-run
        logger.info("=" * 60)
        logger.info("[AUTO-RUN TOGGLE] *** USER DISABLED AUTO-RUN ***")
        logger.info("=" * 60)
        
        # Clear pending_turn to allow manual input
        if st.session_state.get("pending_turn", False):
            logger.info("[AUTO-RUN TOGGLE] Clearing pending_turn flag when disabling auto-run")
            st.session_state.pending_turn = False
        
        # Clear auto-run execution flags
        if "_auto_run_just_executed" in st.session_state:
            logger.info("[AUTO-RUN TOGGLE] Clearing _auto_run_just_executed flag when disabling auto-run")
            del st.session_state._auto_run_just_executed
        
        st.toast("Broadcast paused.", icon=":material/pause_circle:")
        logger.info("[AUTO-RUN TOGGLE] Auto-run mode disabled")
    else:
        logger.debug(f"[AUTO-RUN TOGGLE] No state change detected (auto_mode={st.session_state.auto_mode}, prev={auto_mode_prev})")
    
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

