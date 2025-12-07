"""
Timeline Page

Multi-page Streamlit app for viewing conversation summaries chronologically.
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from utils.streamlit_styles import inject_custom_css
from utils.streamlit_session import initialize_session_state, apply_default_settings
from utils.logging_config import get_logger

# Initialize logging
logger = get_logger(__name__)

# Page config
st.set_page_config(
    page_title="Timeline • Triadic",
    page_icon=":material/timeline:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state if needed
initialize_session_state()
apply_default_settings()

# Inject CSS
inject_custom_css()

# Auto-refresh every 5 seconds to check for new summaries
# This ensures timeline updates when summaries are generated on other pages
st_autorefresh(interval=5000, key="timeline_autorefresh")

# Page header
st.title(":material/timeline: Discussion Timeline")
st.caption("Chronological view of conversation summaries")

st.divider()

# Get summary history
summary_history = st.session_state.get("summary_history", [])

# Track last summary count to detect new summaries
if "_last_timeline_summary_count" not in st.session_state:
    st.session_state._last_timeline_summary_count = len(summary_history)

current_count = len(summary_history)
last_count = st.session_state._last_timeline_summary_count

# If new summaries were added, show a toast and update the count
if current_count > last_count:
    new_summaries = current_count - last_count
    st.toast(f"📅 {new_summaries} new summar{'y' if new_summaries == 1 else 'ies'} added!", icon=":material/timeline:")
    st.session_state._last_timeline_summary_count = current_count

if not summary_history:
    st.info("**No summaries yet.** Summaries are generated every 5 turns. Start a conversation to see the timeline.", icon=":material/info:")
else:
    # Statistics
    total_summaries = len(summary_history)
    total_turns = summary_history[-1]["turn_number"] if summary_history else 0
    first_timestamp = summary_history[0]["timestamp"] if summary_history else ""
    last_timestamp = summary_history[-1]["timestamp"] if summary_history else ""
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Summaries", total_summaries)
    with col2:
        st.metric("Total Turns", total_turns)
    with col3:
        st.metric("Duration", f"{first_timestamp} - {last_timestamp}" if first_timestamp else "N/A")
    
    st.divider()
    
    # Timeline view
    import html
    for idx, summary in enumerate(summary_history):
        turn_range = summary.get("turn_range", (0, summary["turn_number"]))
        start_turn, end_turn = turn_range
        
        # Summary card with styled container
        # Escape HTML and preserve line breaks
        summary_text_escaped = html.escape(summary["summary_text"]).replace("\n", "<br>")
        
        st.markdown(
            f"""
            <div class="timeline-summary-card">
                <div class="timeline-summary-header">
                    <h3>Turns {start_turn}-{end_turn}</h3>
                    <span class="timeline-timestamp">{html.escape(summary['timestamp'])}</span>
                </div>
                <div class="timeline-summary-content">
                    {summary_text_escaped}
                </div>
                <div class="timeline-summary-meta">
                    📊 {summary['message_count']} messages • Turn {summary['turn_number']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Divider between summaries (except last one)
        if idx < len(summary_history) - 1:
            st.divider()

