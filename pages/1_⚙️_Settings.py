"""
Settings Page

Multi-page Streamlit app for managing application settings.
"""

import streamlit as st
from utils.streamlit_styles import inject_custom_css
from utils.streamlit_session import get_settings
from utils.streamlit_session import initialize_session_state, apply_default_settings
from utils.streamlit_persistence import auto_save_session_state
from config import model_config
from utils.logging_config import get_logger

# Initialize logging
logger = get_logger(__name__)

# Page config
st.set_page_config(
    page_title="Settings • Triadic",
    page_icon=":material/settings:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state if needed
initialize_session_state()
apply_default_settings()

# Inject CSS
inject_custom_css()

# Page header
st.title(":material/settings: Settings")
st.caption("Configure model, audio, and advanced features")

st.divider()

# Model Configuration
with st.container():
    st.markdown('<div class="settings-section-card">', unsafe_allow_html=True)
    st.markdown("### :material/psychology: Model Configuration")
    
    model_index = model_config.ALLOWED_MODELS.index(st.session_state.model_name) if st.session_state.model_name in model_config.ALLOWED_MODELS else 1
    st.session_state.model_name = st.radio(
        "**Base Model**",
        model_config.ALLOWED_MODELS,
        index=model_index,
        horizontal=True,
        key="model_radio_settings",
        help="Select the GPT model variant to use"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        effort_index = model_config.ALLOWED_EFFORT_LEVELS.index(st.session_state.reasoning_effort) if st.session_state.reasoning_effort in model_config.ALLOWED_EFFORT_LEVELS else 1
        st.session_state.reasoning_effort = st.selectbox(
            "**Reasoning Effort**",
            model_config.ALLOWED_EFFORT_LEVELS,
            index=effort_index,
            key="reasoning_select_settings",
            help="Higher effort = more thorough reasoning"
        )
    with col2:
        verbosity_options = ["low", "medium", "high"]
        verbosity_index = verbosity_options.index(st.session_state.text_verbosity) if st.session_state.text_verbosity in verbosity_options else 1
        st.session_state.text_verbosity = st.selectbox(
            "**Text Verbosity**",
            verbosity_options,
            index=verbosity_index,
            key="verbosity_select_settings",
            help="Control response length and detail"
        )
    
    st.toggle(
        "**Stream Output**",
        value=st.session_state.get("stream_enabled", True),
        key="stream_enabled_settings",
        help="Enable real-time token streaming"
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# API Configuration
with st.container():
    st.markdown('<div class="settings-section-card">', unsafe_allow_html=True)
    st.markdown("### :material/key: API Configuration")
    
    # Check if key is already set (from secrets/env)
    from config import OPENAI_API_KEY
    has_key_from_env = bool(OPENAI_API_KEY and not st.session_state.get("openai_api_key"))
    
    if has_key_from_env:
        st.info("✅ API key is configured via environment/secrets. You can override it below if needed.", icon=":material/info:")
    else:
        st.warning("⚠️ No API key found. Please enter your OpenAI API key below.", icon=":material/warning:")
    
    # API Key input (password type for security)
    current_key = st.session_state.get("openai_api_key", "")
    # Show masked value if key exists
    display_value = "••••••••" + current_key[-4:] if current_key and len(current_key) > 4 else ""
    
    api_key_value = st.text_input(
        "**OpenAI API Key**",
        value="" if has_key_from_env and not current_key else current_key,
        type="password",
        key="openai_api_key_input",
        help="Enter your OpenAI API key. Get one at https://platform.openai.com/api-keys. This key is stored in session state and takes precedence over environment variables.",
        placeholder="sk-..." if not current_key else None
    )
    
    # Store in session state if provided
    if api_key_value and api_key_value.strip():
        new_key = api_key_value.strip()
        if new_key != current_key:
            st.session_state["openai_api_key"] = new_key
            st.success("✅ API key saved! The app will use this key.", icon=":material/check_circle:")
            st.rerun()  # Reload to pick up the new key
    elif api_key_value == "" and "openai_api_key" in st.session_state and not has_key_from_env:
        # Clear if user deleted the key and no env key exists
        del st.session_state["openai_api_key"]
        st.info("API key cleared. Using environment/secrets key if available.", icon=":material/info:")
    
    st.caption("💡 Your key is stored securely in session state and never committed to git.")
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# Audio Settings
with st.container():
    st.markdown('<div class="settings-section-card">', unsafe_allow_html=True)
    st.markdown("### :material/volume_up: Audio Settings")
    
    st.checkbox(
        "**Synthesize Voice**",
        value=st.session_state.get("tts_enabled", False),
        key="tts_enabled_settings",
        help="Generate speech from AI responses"
    )
    
    st.checkbox(
        "**Autoplay Audio**",
        value=st.session_state.get("tts_autoplay", False),
        key="tts_autoplay_settings",
        help="Automatically play generated audio"
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# IRC View Settings
with st.container():
    st.markdown('<div class="settings-section-card">', unsafe_allow_html=True)
    st.markdown("### :material/code: IRC View Settings")
    
    # Available cyberpunk/terminal fonts
    irc_fonts = {
        "Hack": "Hack",
        "Fira Code": "Fira Code",
        "JetBrains Mono": "JetBrains Mono",
        "Source Code Pro": "Source Code Pro",
        "IBM Plex Mono": "IBM Plex Mono",
        "Operator Mono": "Operator Mono",
        "Space Mono": "Space Mono",
        "Anonymous Pro": "Anonymous Pro",
        "Courier Prime Code": "Courier Prime Code",
        "Courier New": "Courier New"  # Fallback
    }
    
    current_font = st.session_state.get("irc_font", "Hack")
    font_index = list(irc_fonts.keys()).index(current_font) if current_font in irc_fonts else 0
    
    st.session_state.irc_font = st.selectbox(
        "**IRC Font**",
        options=list(irc_fonts.keys()),
        index=font_index,
        key="irc_font_settings",
        help="Select font for IRC text view mode. Cyberpunk-style fonts recommended!"
    )
    
    st.caption("💡 Fonts like Hack, Fira Code, and JetBrains Mono give a cyberpunk terminal aesthetic.")
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# Advanced Features
with st.container():
    st.markdown('<div class="settings-section-card">', unsafe_allow_html=True)
    st.markdown("### :material/science: Advanced Features")
    
    st.checkbox(
        "**Web Search**",
        value=st.session_state.get("web_search_enabled", False),
        key="web_search_enabled_settings",
        help="Enable web search tool - allows the model to search the internet for current information"
    )
    
    st.slider(
        "**Summary Interval** (turns)",
        min_value=3,
        max_value=20,
        value=st.session_state.get("summary_interval", 5),
        step=1,
        key="summary_interval_settings",
        help="Generate conversation summary every N turns (default: 5)"
    )
    
    with st.expander(":material/tune: **Advanced**", expanded=False):
        st.caption("Experimental and advanced API features")
        st.checkbox(
            "**API Introspection** (Verified Orgs)",
            value=st.session_state.get("reasoning_summary_enabled", False),
            key="reasoning_summary_enabled_settings",
            help="Enables 'summary: auto' for reasoning transparency"
        )
        st.info("These features require verified OpenAI organizations", icon=":material/lightbulb:")
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# Current Settings Summary
with st.container():
    st.markdown('<div class="settings-section-card">', unsafe_allow_html=True)
    st.markdown("### :material/info: Current Settings Summary")
    
    settings = get_settings()
    settings_cols = st.columns(3)
    
    with settings_cols[0]:
        st.metric("Model", settings["model_name"])
    with settings_cols[1]:
        st.metric("Reasoning Effort", settings["reasoning_effort"])
    with settings_cols[2]:
        st.metric("Text Verbosity", settings.get("text_verbosity", "medium"))
    
    st.markdown("---")
    
    features_status = []
    if settings.get("tts_enabled", False):
        features_status.append(":material/check_circle: TTS")
    if settings.get("stream_enabled", False):
        features_status.append(":material/check_circle: Streaming")
    if settings.get("web_search_enabled", False):
        features_status.append(":material/check_circle: Web Search")
    if settings.get("reasoning_summary_enabled", False):
        features_status.append(":material/check_circle: API Introspection")
    
    if features_status:
        st.caption(f"Active features: {' '.join(features_status)}")
    else:
        st.caption("No advanced features enabled")
    st.markdown('</div>', unsafe_allow_html=True)

# Sync widget values to actual setting keys
# Streamlit widgets store values in st.session_state[key], but we need them in the setting keys
if "web_search_enabled_settings" in st.session_state:
    st.session_state["web_search_enabled"] = st.session_state["web_search_enabled_settings"]
if "tts_enabled_settings" in st.session_state:
    st.session_state["tts_enabled"] = st.session_state["tts_enabled_settings"]
if "tts_autoplay_settings" in st.session_state:
    st.session_state["tts_autoplay"] = st.session_state["tts_autoplay_settings"]
if "stream_enabled_settings" in st.session_state:
    st.session_state["stream_enabled"] = st.session_state["stream_enabled_settings"]
if "reasoning_summary_enabled_settings" in st.session_state:
    st.session_state["reasoning_summary_enabled"] = st.session_state["reasoning_summary_enabled_settings"]
if "summary_interval_settings" in st.session_state:
    st.session_state["summary_interval"] = st.session_state["summary_interval_settings"]
if "irc_font_settings" in st.session_state:
    st.session_state["irc_font"] = st.session_state["irc_font_settings"]

# Auto-save settings when page is viewed (settings are updated via widgets)
auto_save_session_state()

