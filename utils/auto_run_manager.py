"""
Auto-Run Manager

Handles auto-run state management, delay logic, and resume functionality.
This module provides a single source of truth for auto-run behavior.
"""

import time
import streamlit as st
from utils.logging_config import get_logger

logger = get_logger(__name__)


def check_and_resume_auto_run() -> None:
    """
    Check if auto-run delay has elapsed and resume if conditions are met.
    
    This function handles:
    1. User navigated away during delay and returned
    2. User switched view modes during delay
    3. Any other rerun that occurred during the delay period
    
    If delay has elapsed, clears waiting flags. The next check of should_execute_auto()
    will return True, allowing the next turn to execute.
    If delay hasn't elapsed yet, does nothing (handle_auto_run_delay will continue waiting).
    """
    if not st.session_state.get("_auto_run_waiting", False):
        return
    
    elapsed = time.time() - st.session_state._auto_run_wait_start
    delay_needed = st.session_state.get("auto_delay", 2.0)
    
    if elapsed >= delay_needed:
        # Delay completed - clear waiting flag
        del st.session_state._auto_run_waiting
        del st.session_state._auto_run_wait_start
        logger.info(f"Auto-run delay completed (elapsed: {elapsed:.2f}s, needed: {delay_needed}s) - ready to resume")
        
        # Re-check conditions before continuing (user might have disabled auto-mode)
        current_auto_mode = st.session_state.get("auto_mode", False)
        current_turn_in_progress = st.session_state.get("turn_in_progress", False)
        current_has_messages = len(st.session_state.get("show_messages", [])) > 0
        
        if current_auto_mode and not current_turn_in_progress and current_has_messages:
            # Conditions still met - trigger rerun to continue auto-run
            # This rerun will cause should_execute_auto() to return True, triggering next turn
            logger.info("Auto-run conditions met - triggering rerun to continue")
            st.rerun()
        else:
            logger.debug(f"Auto-run delay elapsed but conditions not met: auto_mode={current_auto_mode}, turn_in_progress={current_turn_in_progress}, has_messages={current_has_messages}")
    else:
        # Delay hasn't elapsed yet - handle_auto_run_delay will continue waiting
        remaining = delay_needed - elapsed
        logger.debug(f"Auto-run still waiting: {remaining:.2f}s remaining")


def handle_auto_run_delay() -> None:
    """
    Handle auto-mode delay checking and continuation.
    
    This should be called after container rendering to check if delay has elapsed.
    If delay is complete and conditions are met, triggers rerun to continue auto-run.
    
    This function continues waiting even if user navigated away and returned.
    """
    if not st.session_state.get("_auto_run_waiting", False):
        return
    
    # We're waiting for the delay to complete
    # Calculate elapsed time from when delay started (persists across page navigation)
    elapsed = time.time() - st.session_state._auto_run_wait_start
    delay_needed = st.session_state.get("auto_delay", 2.0)
    
    if elapsed >= delay_needed:
        # Delay complete - clear waiting flag and check if we should continue
        del st.session_state._auto_run_waiting
        del st.session_state._auto_run_wait_start
        
        # Re-check conditions before continuing (user might have disabled auto-mode)
        current_auto_mode = st.session_state.get("auto_mode", False)
        current_turn_in_progress = st.session_state.get("turn_in_progress", False)
        current_has_messages = len(st.session_state.get("show_messages", [])) > 0
        
        if current_auto_mode and not current_turn_in_progress and current_has_messages:
            # Conditions still met, rerun to trigger next turn
            # This rerun will cause should_execute_auto() to return True, triggering next turn
            logger.info("Auto-run delay completed - resuming auto-run")
            st.rerun()
    else:
        # Still waiting - rerun after a minimal delay to check again
        # Use a very short sleep (0.1s) to prevent excessive reruns while keeping UI responsive
        # This ensures we keep checking even if user navigated away and returned
        time.sleep(0.1)
        st.rerun()


def start_auto_run_delay() -> None:
    """
    Start the auto-run delay timer.
    
    Should be called after a turn completes in auto-mode to wait before next turn.
    """
    st.session_state._auto_run_waiting = True
    st.session_state._auto_run_wait_start = time.time()
    logger.debug(f"Started auto-run delay: {st.session_state.get('auto_delay', 2.0)}s")


def should_execute_auto() -> bool:
    """
    Check if auto-run should execute a turn.
    
    Returns:
        True if auto-mode is enabled, not in progress, has messages, and not waiting for delay
    """
    # First check if auto-mode is actually enabled
    auto_mode = st.session_state.get("auto_mode", False)
    if not auto_mode:
        # If auto-mode is disabled, clear any stuck waiting flags
        if "_auto_run_waiting" in st.session_state:
            del st.session_state._auto_run_waiting
        if "_auto_run_wait_start" in st.session_state:
            del st.session_state._auto_run_wait_start
        return False
    
    has_messages = len(st.session_state.get("show_messages", [])) > 0
    is_waiting_for_delay = st.session_state.get("_auto_run_waiting", False)
    turn_in_progress = st.session_state.get("turn_in_progress", False)
    
    # If turn_in_progress is stuck (no start time or >30s), reset it
    if turn_in_progress:
        if "_turn_start_time" not in st.session_state:
            logger.warning("Detected stuck turn_in_progress in should_execute_auto - resetting")
            st.session_state.turn_in_progress = False
            turn_in_progress = False
        else:
            elapsed = time.time() - st.session_state._turn_start_time
            if elapsed > 30:
                logger.warning(f"Detected stuck turn_in_progress in should_execute_auto (elapsed: {elapsed:.1f}s) - resetting")
                st.session_state.turn_in_progress = False
                del st.session_state._turn_start_time
                turn_in_progress = False
    
    # Debug logging to help diagnose why auto-run isn't starting
    result = (
        auto_mode and
        not turn_in_progress and
        has_messages and
        not is_waiting_for_delay
    )
    
    if auto_mode and not result:
        # Auto-mode is enabled but conditions aren't met - log why
        logger.debug(
            f"Auto-run enabled but not executing: "
            f"auto_mode={auto_mode}, turn_in_progress={turn_in_progress}, "
            f"has_messages={has_messages}, is_waiting_for_delay={is_waiting_for_delay}"
        )
    
    return result

