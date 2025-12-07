"""
Chat Input Module

Handles all chat input UI components including:
- Text input with chat_input widget
- Voice input toggle
- Message submission callbacks
- Auto-mode detection
"""

import streamlit as st
from typing import Callable, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)


def render_text_input(
    on_message: Callable[[str], None],
    on_voice_toggle: Callable[[], None]
) -> Optional[str]:
    """
    Render text input with voice toggle button.
    
    Args:
        on_message: Callback function called with message text when submitted
        on_voice_toggle: Callback function called when voice toggle is clicked
    
    Returns:
        Message text if submitted, None otherwise
    """
    # CRITICAL: Check auto-mode FIRST - this function should NEVER be called when auto_mode is True
    # The container check should prevent this, but we add a safeguard here
    auto_mode = st.session_state.get("auto_mode", False)
    
    if auto_mode:
        # This should never happen if render_chat_input_container() is working correctly
        # But if it does, we return immediately without rendering anything
        logger.warning("render_text_input() called while auto_mode is True - this should not happen")
        return None
    
    # Text input mode with integrated voice button
    # Use a custom layout to place mic icon next to chat input
    input_col1, input_col2 = st.columns([20, 1])
    
    with input_col1:
        # Render chat input - auto_mode check above ensures this only renders when auto_mode is False
        # Use a dynamic key that includes auto_mode state to force widget reset when state changes
        # This prevents widget persistence issues
        widget_key = f"chat_input_widget_{st.session_state.get('auto_mode', False)}"
        host_msg = st.chat_input(
            placeholder=" ",
            key=widget_key
        )
    
    with input_col2:
        st.space(2)  # Align with chat input
        if st.button(
            ":material/mic:",
            key="voice_toggle_button",
            help="Record voice message",
            width='content'
        ):
            on_voice_toggle()
            st.rerun()
    
    # Handle text message input - but only if auto_mode is still False (double-check)
    if host_msg and not st.session_state.get("auto_mode", False):
        on_message(host_msg)
        st.success("Message sent!", icon=":material/send:")
        st.toast("Message injected!", icon=":material/send:")
        logger.info(f"Text message received: {len(host_msg)} characters")
        st.rerun()
    elif host_msg:
        # Auto-mode was enabled between render and submission - ignore the message
        logger.warning("Message submitted but auto_mode is now True - ignoring message")
        st.warning("Message ignored: Auto-run is now active. Turn off auto-run to send messages.", icon=":material/warning:")
    
    return host_msg


def create_message_handler() -> Callable[[str], None]:
    """
    Create a standard message handler callback.
    
    Returns:
        Callback function that adds message to session state and sets pending_turn
    """
    import time
    
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
    
    return on_message


def create_voice_toggle_handler() -> Callable[[], None]:
    """
    Create a standard voice toggle handler callback.
    
    Returns:
        Callback function that toggles voice input mode
    """
    def on_voice_toggle() -> None:
        """Handle voice toggle."""
        st.session_state.show_voice_input = True
    
    return on_voice_toggle


def render_voice_input(
    on_transcription: Callable[[str], None],
    on_cancel: Callable[[], None]
) -> None:
    """
    Render voice input widget.
    
    Args:
        on_transcription: Callback function called with transcribed text
        on_cancel: Callback function called when cancelled
    """
    from utils.streamlit_audio import transcribe_streamlit_audio
    
    # Check if auto-mode is enabled (disable voice input when auto-run is active)
    auto_mode = st.session_state.get("auto_mode", False)
    
    if auto_mode:
        # Cancel voice input if it was active
        if st.session_state.get("show_voice_input", False):
            on_cancel()
        st.info(":material/pause_circle: Voice input disabled while On Air (Auto-Run) is active", icon=":material/info:")
        return
    
    # Voice input mode
    col1, col2 = st.columns([20, 1])
    with col1:
        audio_val = st.audio_input("Recording...", key="audio_input_widget", disabled=auto_mode)
    with col2:
        if st.button("✕", key="cancel_voice", help="Cancel recording", disabled=auto_mode):
            on_cancel()
            st.rerun()
    
    if audio_val:
        audio_hash = hash(audio_val.getvalue())
        if st.session_state.get("last_audio_id") != audio_hash:
            st.session_state.last_audio_id = audio_hash
            st.session_state.show_voice_input = False
            with st.spinner("Transcribing audio stream..."):
                text_out = transcribe_streamlit_audio(audio_val)
            if text_out:
                on_transcription(text_out)
                st.success("Voice transcribed successfully!", icon=":material/mic:")
                st.toast("Voice transcribed!", icon=":material/graphic_eq:")
                logger.info(f"Voice transcribed: {len(text_out)} characters")
                st.rerun()


def render_chat_input_container(
    show_voice_input: bool = False,
    on_transcription: Optional[Callable[[str], None]] = None,
    on_voice_cancel: Optional[Callable[[], None]] = None
) -> None:
    """
    Render the complete chat input container with text/voice input switching.
    
    Uses a minimal CSS wrapper to keep the chat input fixed at the bottom of the viewport,
    ensuring it remains visible even when scrolling the page.
    
    This is the main entry point for rendering chat input. It handles:
    - Auto-mode detection (disables/hides input when auto-mode is active)
    - Switching between text and voice input modes
    - Fixed positioning to keep input visible while scrolling
    
    Args:
        show_voice_input: Whether to show voice input instead of text input
        on_transcription: Callback for voice transcription (required if show_voice_input=True)
        on_voice_cancel: Callback for voice input cancellation (required if show_voice_input=True)
    """
    # CRITICAL: Check auto-mode FIRST and ALWAYS disable input when auto-mode is enabled
    # This check must happen before any input widgets are rendered
    # We use explicit boolean check to ensure robustness
    auto_mode = st.session_state.get("auto_mode", False)
    
    # Explicit boolean check - disable if auto_mode is True
    # This must be checked EVERY TIME this function is called, even on initial load
    if auto_mode is True:
        # Clear any chat input widget state to prevent it from persisting
        # This ensures the widget doesn't show up from a previous render
        # Streamlit widgets can persist across reruns, so we need to clear them aggressively
        widget_keys_to_clear = ["chat_input_widget", "voice_toggle_button", "audio_input_widget", "cancel_voice"]
        for key in widget_keys_to_clear:
            if key in st.session_state:
                try:
                    del st.session_state[key]
                except (KeyError, AttributeError, RuntimeError):
                    pass  # Widget state might not be deletable, that's okay
        
        # Also clear voice input state
        if st.session_state.get("show_voice_input", False):
            st.session_state.show_voice_input = False
        
        # Show a message explaining why input is disabled
        # Use a container to maintain layout consistency
        chat_input_container = st.container()
        with chat_input_container:
            chat_input_container.markdown(
                '<div class="fixed-chat-input-container">',
                unsafe_allow_html=True
            )
            st.divider()
            st.info(
                ":material/pause_circle: Chat input is disabled while **On Air** (Auto-Run) is active. "
                "Turn off auto-run in the sidebar to enable chat input.",
                icon=":material/info:"
            )
            chat_input_container.markdown('</div>', unsafe_allow_html=True)
        
        # CRITICAL: Return immediately - do NOT render any input widgets
        # This ensures st.chat_input() is never called when auto_mode is True
        logger.debug("Chat input disabled: auto_mode is True")
        return
    
    # Use container with CSS class for fixed positioning
    # This ensures the chat input stays visible when scrolling
    chat_input_container = st.container()
    
    with chat_input_container:
        # Apply minimal CSS wrapper for fixed positioning
        # This is necessary to keep the input visible while scrolling
        chat_input_container.markdown(
            '<div class="fixed-chat-input-container">',
            unsafe_allow_html=True
        )
        
        st.divider()
        
        if show_voice_input:
            if on_transcription is None or on_voice_cancel is None:
                raise ValueError("on_transcription and on_voice_cancel are required when show_voice_input=True")
            
            render_voice_input(
                on_transcription=on_transcription,
                on_cancel=on_voice_cancel
            )
        else:
            # Use standard handlers if not provided
            on_message = create_message_handler()
            on_voice_toggle = create_voice_toggle_handler()
            
            render_text_input(
                on_message=on_message,
                on_voice_toggle=on_voice_toggle
            )
        
        chat_input_container.markdown('</div>', unsafe_allow_html=True)

