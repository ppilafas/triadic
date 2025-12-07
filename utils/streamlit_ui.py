"""
Streamlit-specific UI helpers for HTML generation, styling, and settings management.

Phase 3: Full Native Alignment
- Avatar loading optimized with @st.cache_resource
- Native Streamlit patterns throughout
- Performance optimizations applied
"""

import base64
import io
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
import streamlit as st
from config import model_config, speaker_config, timing_config, audio_config
from utils.logging_config import get_logger
from utils.validators import (
    validate_model_name,
    validate_reasoning_effort,
    validate_auto_delay
)
from stt import transcribe_audio as stt_transcribe_audio
from exceptions import TranscriptionError
from tts import tts_stream_to_bytes
from utils.streamlit_styles import inject_custom_css

logger = get_logger(__name__)

@st.cache_resource
def _load_avatar_image(speaker_key: str) -> Optional[bytes]:
    """
    Load avatar image file as bytes (cached with @st.cache_resource).
    
    This is a resource that should be cached across reruns but can be cleared
    if needed. Using @st.cache_resource is appropriate for file I/O operations.
    
    Args:
        speaker_key: Speaker key (host, gpt_a, gpt_b)
    
    Returns:
        Avatar image bytes if found, None otherwise
    """
    avatar_filenames = {
        "host": ["Host.png", "host.png"],
        "gpt_a": ["gpt_a.png", "GPT-A.png"],
        "gpt_b": ["gpt_b.png", "GPT-B.png"]
    }
    
    filenames = avatar_filenames.get(speaker_key, [])
    
    # Check if custom avatar exists in public/avatars/
    for filename in filenames:
        avatar_path = Path("public/avatars") / filename
        if avatar_path.exists():
            try:
                with open(avatar_path, "rb") as img_file:
                    return img_file.read()
            except Exception as e:
                logger.warning(f"Failed to load avatar {avatar_path}: {e}")
                break
    
    return None


@st.cache_data
def _encode_avatar_data_uri(img_data: bytes) -> str:
    """
    Encode avatar image bytes as base64 data URI (cached with @st.cache_data).
    
    This caches the base64 encoding operation which is relatively expensive.
    The image bytes themselves are already cached via @st.cache_resource.
    
    Args:
        img_data: Avatar image bytes
    
    Returns:
        Base64 data URI string
    """
    img_base64 = base64.b64encode(img_data).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"


def get_avatar_path(speaker_key: str) -> str:
    """
    Get the avatar for a speaker, using custom PNG if available, otherwise Material Symbol.
    
    For Streamlit, we encode the image as base64 data URI since Streamlit doesn't
    automatically serve files from public/ directory like Chainlit does.
    
    Uses @st.cache_resource for image loading and @st.cache_data for encoding (Phase 3 optimization).
    
    Args:
        speaker_key: Speaker key (host, gpt_a, gpt_b)
    
    Returns:
        Avatar as base64 data URI string or Material Symbol string
    """
    # Try to load custom avatar (cached image bytes)
    img_data = _load_avatar_image(speaker_key)
    
    if img_data:
        try:
            # Cache the base64 encoding operation
            return _encode_avatar_data_uri(img_data)
        except Exception as e:
            logger.warning(f"Failed to encode avatar for {speaker_key}: {e}")
    
    # Fallback to Material Symbol if custom avatar not found
    fallback_map = {
        "host": ":material/person:",
        "gpt_a": ":material/smart_toy:",
        "gpt_b": ":material/sentiment_satisfied:"
    }
    logger.debug(f"Custom avatar not found for {speaker_key}, using Material Symbol fallback")
    return fallback_map.get(speaker_key, ":material/help:")

# Speaker info for Streamlit UI (extends config with UI-specific fields)
# Enhanced with modern gradients and better color schemes
# Note: avatar paths are resolved at runtime via get_avatar_path()
SPEAKER_INFO = {
    "host": {
        "label": "Host",
        "full_label": "Host (Panagiotis)",
        "icon": ":material/person:",
        "avatar": None,  # Will be set dynamically
        "color": "#10b981",  # Emerald green for accent
        "bubble_bg": "linear-gradient(135deg, #10b981 0%, #059669 50%, #047857 100%)",  # Vibrant green gradient
        "bubble_bg_fallback": "#10b981",  # Fallback for browsers that don't support gradients
        "text_color": "#ffffff",
        "shadow_color": "rgba(16, 185, 129, 0.4)",
        "border_color": "#34d399",
        "glow_color": "rgba(16, 185, 129, 0.2)"
    },
    "gpt_a": {
        "label": "GPT-A",
        "full_label": "GPT-A (The Analyst)",
        "icon": ":material/psychology:",
        "avatar": None,  # Will be set dynamically
        "color": "#3b82f6",  # Bright blue for accent
        "bubble_bg": "linear-gradient(135deg, #3b82f6 0%, #2563eb 50%, #1e40af 100%)",  # Vibrant blue gradient
        "bubble_bg_fallback": "#3b82f6",
        "text_color": "#ffffff",
        "shadow_color": "rgba(59, 130, 246, 0.4)",
        "border_color": "#60a5fa",
        "glow_color": "rgba(59, 130, 246, 0.2)"
    },
    "gpt_b": {
        "label": "GPT-B",
        "full_label": "GPT-B (The Empath)",
        "icon": ":material/favorite:",
        "avatar": None,  # Will be set dynamically
        "color": "#ef4444",  # Bright red for accent
        "bubble_bg": "linear-gradient(135deg, #f87171 0%, #ef4444 50%, #dc2626 100%)",  # Vibrant red gradient
        "bubble_bg_fallback": "#f87171",
        "text_color": "#ffffff",
        "shadow_color": "rgba(239, 68, 68, 0.4)",
        "border_color": "#fca5a5",
        "glow_color": "rgba(239, 68, 68, 0.2)"
    },
}

# Use voice map from config
VOICE_FOR_SPEAKER = speaker_config.VOICE_MAP

# Note: Avatar paths are resolved lazily via get_avatar_path() which uses caching
# We don't initialize them at module load to avoid calling Streamlit functions
# at import time, which is a Streamlit best practice


# ========== CSS & STYLING ==========
# CSS injection is now handled by utils.streamlit_styles
# This import provides inject_custom_css() function


# ========== AUDIO FUNCTIONS ==========


def autoplay_audio(audio_bytes: bytes) -> None:
    """
    Autoplay audio using HTML5 audio element.
    
    Args:
        audio_bytes: Audio data as bytes
    """
    if not audio_bytes:
        return
    
    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    st.markdown(
        f'<audio autoplay="true" style="display:none;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
        unsafe_allow_html=True
    )


def transcribe_streamlit_audio(audio_file) -> Optional[str]:
    """
    Transcribe Streamlit audio_input to text.
    
    Args:
        audio_file: Streamlit audio_input file object (BytesIO-like)
    
    Returns:
        Transcribed text or None if transcription fails
    """
    try:
        # Streamlit audio_input provides file-like object with audio data
        # Get the raw bytes
        audio_bytes = audio_file.getvalue()
        
        # Create BytesIO buffer for stt.transcribe_audio
        wav_buffer = io.BytesIO(audio_bytes)
        wav_buffer.name = audio_config.WAV_FILENAME
        
        # Use the shared stt.transcribe_audio function
        text = stt_transcribe_audio(wav_buffer)
        logger.info(f"Transcription successful: {len(text)} characters")
        return text
            
    except TranscriptionError as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        st.error(f"**Transcription Error:** {str(e)}", icon=":material/error:")
        return None
    except Exception as e:
        logger.error(f"Unexpected transcription error: {e}", exc_info=True)
        st.error("**Audio Error:** Failed to transcribe audio. Please try again.", icon=":material/error:")
        return None


# ========== BANNER & STATUS ==========

def render_broadcast_banner(speaker_key: str) -> None:
    """
    Render ON AIR banner for current speaker.
    
    Args:
        speaker_key: Speaker key (gpt_a or gpt_b)
    """
    meta = SPEAKER_INFO.get(speaker_key, SPEAKER_INFO["gpt_a"])
    color = meta["color"]
    label = meta["full_label"].upper()
    
    st.markdown(
        f"""
        <div style="
            background-color: {color}15; 
            border: 1px solid {color}; 
            border-radius: 8px; 
            padding: 8px; 
            text-align: center; 
            margin-bottom: 20px;
            animation: pulse 2s infinite;">
            <span style="color: {color}; font-weight: bold; letter-spacing: 1px; font-size: 0.9em;">
                <span style="color: #ef4444;">●</span> ON AIR: {label}
            </span>
        </div>
        <style>
            @keyframes pulse {{
                0% {{ box-shadow: 0 0 0 0 {color}30; }}
                70% {{ box-shadow: 0 0 0 8px {color}00; }}
                100% {{ box-shadow: 0 0 0 0 {color}00; }}
            }}
        </style>
        """,
        unsafe_allow_html=True
    )


# ========== SETTINGS ==========

@st.cache_data
def _validate_settings(
    model_name: str,
    reasoning_effort: str,
    auto_delay: float
) -> Dict[str, Any]:
    """
    Validate settings values (cached with @st.cache_data).
    
    This caches the validation results to avoid redundant validation operations.
    Cache invalidates when input values change.
    
    Args:
        model_name: Model name to validate
        reasoning_effort: Reasoning effort to validate
        auto_delay: Auto delay to validate
    
    Returns:
        Dictionary of validated settings
    """
    validated = {}
    try:
        validated["model_name"] = validate_model_name(model_name)
        validated["reasoning_effort"] = validate_reasoning_effort(reasoning_effort)
        validated["auto_delay"] = validate_auto_delay(auto_delay)
    except Exception as e:
        logger.warning(f"Invalid setting, using default: {e}")
        # Fall back to defaults
        validated["model_name"] = model_config.DEFAULT_MODEL
        validated["reasoning_effort"] = model_config.DEFAULT_REASONING_EFFORT
        validated["auto_delay"] = timing_config.DEFAULT_AUTO_DELAY
    
    return validated


def get_settings() -> Dict[str, Any]:
    """
    Get and validate settings from Streamlit session state.
    
    Uses @st.cache_data for validation caching (Phase 3 optimization).
    
    Returns:
        Dictionary of validated settings
    """
    defaults = {
        "model_name": model_config.DEFAULT_MODEL,
        "reasoning_effort": model_config.DEFAULT_REASONING_EFFORT,
        "auto_delay": timing_config.DEFAULT_AUTO_DELAY,
        "tts_enabled": False,
        "tts_autoplay": False,
        "auto_mode": False,
        "stream_enabled": True,
        "text_verbosity": "medium",
        "reasoning_summary_enabled": False,
        "web_search_enabled": True  # Enable web search by default
    }
    
    settings = {}
    for key, default in defaults.items():
        settings[key] = st.session_state.get(key, default)
    
    # Validate settings (cached)
    validated = _validate_settings(
        settings["model_name"],
        settings["reasoning_effort"],
        float(settings["auto_delay"])
    )
    
    # Update with validated values
    settings.update(validated)
    
    return settings


# ========== SIDEBAR COMPONENTS ==========
# Sidebar components have been moved to utils/streamlit_sidebar.py
# Import them when needed:
# from utils.streamlit_sidebar import (
#     render_sidebar_main_controls,
#     render_sidebar_settings,
#     render_sidebar_knowledge_base
# )


# ========== TOP CONTROLS CONTAINER ==========

def _get_current_topic() -> Optional[str]:
    """
    Extract the current discussion topic from message history.
    
    Looks for the most recent host message that starts with "Let's discuss:"
    and extracts the topic.
    
    Returns:
        Current topic string if found, None otherwise
    """
    messages = st.session_state.get("show_messages", [])
    if not messages:
        return None
    
    # Search backwards through messages to find the most recent topic
    for message in reversed(messages):
        if message.get("speaker") == "host":
            content = message.get("content", "")
            if content.startswith("Let's discuss:"):
                # Extract topic (remove "Let's discuss: " prefix)
                topic = content.replace("Let's discuss:", "").strip()
                return topic if topic else None
    
    return None


def render_top_controls() -> None:
    """
    Render top controls container (On Air toggle and current topic).
    This container appears above the main chat area.
    """
    # Get current topic if available
    current_topic = _get_current_topic()
    
    # Create columns for On Air toggle and topic display
    if current_topic:
        col1, col2 = st.columns([1, 2])
        with col1:
            # On Air Toggle
            auto_mode_prev = st.session_state.auto_mode
            st.session_state.auto_mode = st.toggle(
                "**On Air (Auto-Run)**",
                value=st.session_state.auto_mode,
                key="top_auto_mode_toggle",
                help="Automatically trigger turns at specified cadence"
            )
            
            if st.session_state.auto_mode and not auto_mode_prev:
                st.toast("We are LIVE! Auto-run started.", icon=":material/broadcast_on_home:")
                logger.info("Auto-run mode enabled")
                # Trigger rerun to start auto-run cycle immediately
                st.rerun()
            elif not st.session_state.auto_mode and auto_mode_prev:
                st.toast("Broadcast paused.", icon=":material/pause_circle:")
                logger.info("Auto-run mode disabled")
        
        with col2:
            # Display current topic using Streamlit info component
            st.info(
                f"**Current Topic:** {current_topic}",
                icon=":material/lightbulb:"
            )
    else:
        # No topic - just show On Air toggle
        auto_mode_prev = st.session_state.auto_mode
        st.session_state.auto_mode = st.toggle(
            "**On Air (Auto-Run)**",
            value=st.session_state.auto_mode,
            key="top_auto_mode_toggle",
            help="Automatically trigger turns at specified cadence"
        )
        
        if st.session_state.auto_mode and not auto_mode_prev:
            st.toast("We are LIVE! Auto-run started.", icon=":material/broadcast_on_home:")
            logger.info("Auto-run mode enabled")
            # Trigger rerun to start auto-run cycle immediately
            st.rerun()
        elif not st.session_state.auto_mode and auto_mode_prev:
            st.toast("Broadcast paused.", icon=":material/pause_circle:")
            logger.info("Auto-run mode disabled")


# ========== MAIN AREA COMPONENTS ==========

@st.cache_resource
def _load_banner_image() -> Optional[bytes]:
    """
    Load banner image file as bytes (cached with @st.cache_resource).
    
    Args:
        None (banner path is fixed)
    
    Returns:
        Banner image bytes if found, None otherwise
    """
    banner_path = Path("public/banners/triadic-banner.png")
    if banner_path.exists():
        try:
            with open(banner_path, "rb") as img_file:
                return img_file.read()
        except Exception as e:
            logger.warning(f"Failed to load banner {banner_path}: {e}")
    return None


@st.cache_data
def _encode_banner_data_uri(img_data: bytes) -> str:
    """
    Encode banner image bytes as base64 data URI (cached with @st.cache_data).
    
    Args:
        img_data: Banner image bytes
    
    Returns:
        Base64 data URI string
    """
    img_base64 = base64.b64encode(img_data).decode("utf-8")
    return f"data:image/png;base64,{img_base64}"


def render_app_banner(clickable: bool = False, on_click: Optional[Callable] = None) -> bool:
    """
    Render the Triadic Show banner at the top of the main content area.
    
    Loads the banner image from public/banners/ and displays it as a header.
    Uses @st.cache_resource and @st.cache_data for efficient loading (Phase 3 optimization).
    
    Args:
        clickable: If True, makes the banner clickable
        on_click: Optional callback function to call when banner is clicked
    
    Returns:
        True if banner was clicked (when clickable=True), False otherwise
    """
    # Load banner image (cached)
    img_data = _load_banner_image()
    
    if img_data:
        try:
            # Encode as data URI (cached)
            banner_data_uri = _encode_banner_data_uri(img_data)
            
            if clickable:
                
                # Use HTML img tag to better control transparency
                st.markdown(f"""
                    <div class="app-banner-container clickable-banner-wrapper" style="position: relative;">
                        <img src="{banner_data_uri}" alt="Triadic Show" class="app-banner" style="background: transparent; image-rendering: -webkit-optimize-contrast;" />
                """, unsafe_allow_html=True)
                
                # Add hover overlay HTML
                st.markdown("""
                    <div class="banner-hover-overlay">
                        <div class="banner-cta-text">
                            <span>Click to Enter →</span>
                        </div>
                    </div>
                    <style>
                        .app-banner-container {
                            position: relative;
                            border-radius: var(--radius-lg);
                            overflow: hidden;
                            box-shadow: var(--shadow-md);
                            cursor: pointer;
                            transition: all var(--duration-normal) var(--ease-out);
                        }
                        .app-banner-container:hover {
                            transform: scale(1.015) translateY(-2px);
                            box-shadow: var(--shadow-xl), 0 0 30px rgba(77, 166, 255, 0.2);
                        }
                        .banner-hover-overlay {
                            position: absolute;
                            top: 0;
                            left: 0;
                            right: 0;
                            bottom: 0;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            background: rgba(0, 0, 0, 0.4);
                            backdrop-filter: blur(8px);
                            opacity: 0;
                            transition: opacity var(--duration-normal) var(--ease-out);
                            border-radius: var(--radius-lg);
                            pointer-events: none;
                            z-index: 5;
                        }
                        .clickable-banner-wrapper:hover .banner-hover-overlay {
                            opacity: 1;
                        }
                        .banner-cta-text {
                            background: rgba(0, 0, 0, 0.7);
                            backdrop-filter: blur(12px);
                            padding: 14px 28px;
                            border-radius: 12px;
                            border: 1px solid rgba(255, 255, 255, 0.2);
                        }
                        .banner-cta-text span {
                            color: white;
                            font-weight: 600;
                            font-size: 0.95rem;
                            letter-spacing: 0.5px;
                        }
                    </style>
                    </div>
                """, unsafe_allow_html=True)
                
                # Create clickable button overlay using columns
                click_col1, click_col2, click_col3 = st.columns([1, 8, 1])
                with click_col2:
                    clicked = st.button("", key="banner_click_button", use_container_width=True, help="Click to enter the app")
                    if clicked:
                        if on_click:
                            on_click()
                        return True
                return False
            else:
                # Render banner with proper styling (non-clickable)
                # Use HTML img tag to better control transparency
                banner_html = f"""
                <div class="app-banner-container">
                    <img src="{banner_data_uri}" alt="Triadic Show" class="app-banner" style="background: transparent; image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;" />
                </div>
                """
                st.markdown(banner_html, unsafe_allow_html=True)
                return False
        except Exception as e:
            logger.warning(f"Failed to process banner: {e}")
            return False
    else:
        logger.warning("Banner not found at public/banners/triadic-banner.png")
        return False


# Removed render_sticky_controls() - no longer needed
# Knowledge Base is accessible via sidebar "Add Documents" button


def render_generate_topics_button() -> None:
    """
    Render Generate Topics button (inside chat container).
    """
    if st.button(
        "Generate Topics",
        icon=":material/auto_awesome:",
        width='stretch',
        help="Generate discussion topics based on uploaded documents (if any)",
        key="chat_generate_topics"
    ):
        st.session_state._generate_topics_requested = True
        st.rerun()


def render_topic_suggestions(
    topics: List[str],
    on_topic_select: Callable[[str], None]
) -> None:
    """
    Render topic suggestions UI with Clear button.
    
    Args:
        topics: List of topic strings
        on_topic_select: Callback function that takes a topic string as argument
    """
    if not topics:
        return
    
    # Header with Clear button
    header_cols = st.columns([3, 1])
    with header_cols[0]:
        st.markdown("### :material/lightbulb: Discussion Topics")
        st.caption("Click a topic to start the discussion:")
    
    with header_cols[1]:
        if st.button(
            "Clear",
            icon=":material/clear:",
            width='stretch',
            help="Clear current topic suggestions",
            key="clear_topics"
        ):
            st.session_state.topic_suggestions = []
            st.rerun()
    
    # Display topics in a grid layout
    topic_cols = st.columns(2)
    for idx, topic in enumerate(topics):
        col_idx = idx % 2
        with topic_cols[col_idx]:
            if st.button(
                f":material/chat: {topic}",
                key=f"topic_btn_{idx}",
                width='stretch',
                help=f"Start discussion about: {topic}"
            ):
                on_topic_select(topic)


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
    # Check if auto-mode is enabled (hide input completely when auto-run is active)
    auto_mode = st.session_state.get("auto_mode", False)
    
    # Native Streamlit way: don't render chat input at all when auto-mode is enabled
    if auto_mode:
        return None
    
    # Text input mode with integrated voice button
    # Use a custom layout to place mic icon next to chat input
    input_col1, input_col2 = st.columns([20, 1])
    
    with input_col1:
        # Chat input (only rendered when not in auto-mode)
        host_msg = st.chat_input(
            placeholder=" ",
            key="chat_input_widget"
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
    
    # Handle text message input
    if host_msg:
        on_message(host_msg)
        st.success("Message sent!", icon=":material/send:")
        st.toast("Message injected!", icon=":material/send:")
        logger.info(f"Text message received: {len(host_msg)} characters")
        st.rerun()
    
    return host_msg


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


# ========== MESSAGE RENDERING (DECOUPLED) ==========
# Message rendering functions are now in utils.streamlit_messages
# Import them at the end to avoid circular imports (after SPEAKER_INFO is defined)
from utils.streamlit_messages import (
    render_styled_bubble,
    render_streaming_bubble,
    update_streaming_bubble,
    render_message_history
)

