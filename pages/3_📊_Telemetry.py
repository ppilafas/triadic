"""
Telemetry Page

Multi-page Streamlit app for viewing system metrics and conversation statistics.
"""

import streamlit as st
from utils.streamlit_styles import inject_custom_css
from utils.streamlit_telemetry import render_system_metrics, render_conversation_statistics
from utils.streamlit_session import initialize_session_state, apply_default_settings
from utils.logging_config import get_logger

# Initialize logging
logger = get_logger(__name__)

# Page config
st.set_page_config(
    page_title="Telemetry • Triadic",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state if needed
initialize_session_state()
apply_default_settings()

# Inject CSS
inject_custom_css()

# Page header
st.title(":material/analytics: Telemetry")
st.caption("System metrics and conversation statistics")

st.divider()

# System Metrics
with st.container():
    st.markdown('<div class="settings-section-card">', unsafe_allow_html=True)
    st.markdown("### :material/monitor: System Metrics")
    
    render_system_metrics(
        auto_mode=st.session_state.get("auto_mode", False),
        total_turns=st.session_state.get("total_turns", 0),
        latency=st.session_state.get("last_latency", "0.00s"),
        model_name=st.session_state.get("model_name", "gpt-5-mini")
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# Conversation Statistics
with st.container():
    st.markdown('<div class="settings-section-card">', unsafe_allow_html=True)
    st.markdown("### :material/chat: Conversation Statistics")
    
    render_conversation_statistics(st.session_state.get("show_messages", []))
    
    st.markdown('</div>', unsafe_allow_html=True)

