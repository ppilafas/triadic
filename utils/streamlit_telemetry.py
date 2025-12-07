"""
Streamlit telemetry and analytics components.

This module provides functions for rendering system metrics, conversation
statistics, and charts in the Streamlit UI.
"""

from typing import List, Dict, Any
import pandas as pd
import altair as alt
import streamlit as st


def render_system_metrics(
    auto_mode: bool,
    total_turns: int,
    latency: str,
    model_name: str
) -> None:
    """
    Render system metrics (Status, Turn Count, Latency, Model).
    
    Args:
        auto_mode: Whether auto-run mode is active
        total_turns: Total number of turns executed
        latency: Last turn latency as string (e.g., "2.34s")
        model_name: Current model name
    """
    st.markdown("#### :material/dashboard: System Metrics")
    c1, c2, c3, c4 = st.columns(4)
    
    # Status metric with native components
    status_value = "Live" if auto_mode else "Standby"
    c1.metric(
        "Status",
        status_value,
        delta=None,
        border=True
    )
    with c1:
        try:
            if auto_mode:
                st.badge("● LIVE")
            else:
                st.badge("○ STANDBY")
        except AttributeError:
            pass  # Fallback if st.badge not available
    
    # Turn count with trend
    turn_delta = f"+{total_turns}" if total_turns > 0 else None
    c2.metric(
        "Turn Count",
        total_turns,
        delta=turn_delta,
        delta_color="normal",
        border=True
    )
    
    # Latency metric
    c3.metric(
        "Latency",
        latency,
        border=True
    )
    
    # Model metric
    model_display = model_name.replace("gpt-", "").upper()
    c4.metric(
        "Model",
        model_display,
        border=True
    )


def render_conversation_statistics(messages: List[Dict[str, Any]]) -> None:
    """
    Render conversation statistics and charts.
    
    Args:
        messages: List of message dictionaries with 'chars' and 'speaker' keys
    """
    if len(messages) <= 1:
        st.info("Telemetry data will appear here after the first turn.", icon=":material/trending_up:")
        return
    
    st.markdown("#### :material/bar_chart: Conversation Statistics")
    df = pd.DataFrame(messages).reset_index()
    
    # Summary statistics with native badges
    col1, col2, col3 = st.columns(3)
    total_chars = df['chars'].sum()
    avg_chars = df['chars'].mean()
    max_chars = df['chars'].max()
    
    with col1:
        st.metric("Total Characters", f"{int(total_chars):,}", border=True)
        try:
            st.badge(f"{len(df)} messages")
        except AttributeError:
            st.caption(f"{len(df)} messages")
    with col2:
        st.metric("Avg per Turn", f"{int(avg_chars):,}", border=True)
        try:
            st.badge(f"{int(avg_chars)} avg")
        except AttributeError:
            st.caption(f"{int(avg_chars)} avg")
    with col3:
        st.metric("Max Turn", f"{int(max_chars):,}", border=True)
        try:
            st.badge("Peak")
        except AttributeError:
            st.caption("Peak")
    
    st.space(1)
    
    # Enhanced chart with better styling
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X('index:O', title='Turn Number', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('chars:Q', title='Characters', axis=alt.Axis(grid=True)),
            color=alt.Color(
                'speaker:N',
                scale=alt.Scale(
                    domain=['host', 'gpt_a', 'gpt_b'],
                    range=['#808080', '#4da6ff', '#ff6b6b']
                ),
                legend=alt.Legend(title="Speaker", orient="top")
            ),
            tooltip=[
                alt.Tooltip('index:O', title='Turn'),
                alt.Tooltip('speaker:N', title='Speaker'),
                alt.Tooltip('chars:Q', title='Characters', format=',.0f'),
                alt.Tooltip('timestamp:N', title='Time')
            ]
        )
        .properties(
            height=200,
            title="Character Count by Turn"
        )
        .configure_title(fontSize=14, fontWeight=600)
        .configure_axis(labelFontSize=10, titleFontSize=12)
        .configure_legend(labelFontSize=10, titleFontSize=11)
    )
    st.altair_chart(chart, width='stretch')

