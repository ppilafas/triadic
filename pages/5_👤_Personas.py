"""
Personas Page

Multi-page Streamlit app for editing model personas (system instructions).
"""

import streamlit as st
from utils.streamlit_styles import inject_custom_css
from utils.streamlit_session import initialize_session_state, apply_default_settings
from utils.streamlit_persistence import auto_save_session_state
from core.message_builder import load_system_prompt
from config import SYSTEM_PROMPT_PATH
from utils.logging_config import get_logger

# Initialize logging
logger = get_logger(__name__)

# Page config
st.set_page_config(
    page_title="Personas • Triadic",
    page_icon=":material/psychology:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state if needed
initialize_session_state()
apply_default_settings()

# Inject CSS
inject_custom_css()

# Initialize persona storage in session state
if "persona_gpt_a" not in st.session_state:
    st.session_state.persona_gpt_a = """You are GPT-A (The Analyst), the first AI guest on the talk show.

Your persona:
- More analytical and nerdy
- Likes to dig into mechanisms and structure
- Focuses on how things work, technical details, and logical analysis
- Asks probing questions about systems and processes
- Uses data and evidence to support your points
- Can be more abstract and theoretical

Your communication style:
- Clear, structured thinking
- References technical concepts when relevant
- Breaks down complex ideas into components
- Challenges assumptions with logical reasoning"""

if "persona_gpt_b" not in st.session_state:
    st.session_state.persona_gpt_b = """You are GPT-B (The Empath), the second AI guest on the talk show.

Your persona:
- More human-facing and empathetic
- Focuses on lived experience, emotions, and social impact
- Considers the human perspective and real-world implications
- Asks questions about feelings, values, and personal experiences
- Uses stories and examples to illustrate points
- Can be more intuitive and emotionally aware

Your communication style:
- Warm and relatable
- References human experiences and emotions
- Connects ideas to real-world impact
- Challenges assumptions with empathy and understanding"""

if "system_prompt_base" not in st.session_state:
    # Load from file
    try:
        with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            st.session_state.system_prompt_base = f.read()
    except FileNotFoundError:
        st.session_state.system_prompt_base = """You are participating in a live talk show with a live human host (Panagiotis) and an audience.

Participants:
- Host (Panagiotis): introduces topics, occasionally comments, may steer the conversation.
- GPT-A: first AI guest, more analytical, nerdy, likes to dig into mechanisms and structure.
- GPT-B: second AI guest, more human-facing, focuses on lived experience, emotions, and social impact.

Rules:
- Only speak as your own persona (GPT-A or GPT-B), never as the Host or the other AI.
- Respond directly to what was just said in the transcript.
- Be conversational and vivid, like a podcast or talk show, not like an academic essay.
- Keep your reply to at most 3 short paragraphs or ~6–7 sentences.
- Ideally, end with a question back to the other guest or to the Host, to keep the conversation flowing.

Tool Usage:
- If you have access to tools (web search, file search), use them automatically when you need current information, want to verify facts, or search through documents.
- Don't mention that you're using tools - just incorporate the information naturally into your response.
- Use tools proactively when the conversation requires up-to-date information or when searching documents would enhance your response."""

# Page header
st.title(":material/psychology: Personas & System Instructions")
st.caption("Edit the personas and system instructions for GPT-A and GPT-B models")

st.divider()

# General System Prompt
with st.container():
    st.markdown('<div class="settings-section-card">', unsafe_allow_html=True)
    st.markdown("### :material/article: General System Prompt")
    st.caption("Base instructions that apply to all participants. This is loaded from `system.txt`.")
    
    system_prompt = st.text_area(
        "**System Prompt**",
        value=st.session_state.system_prompt_base,
        height=300,
        key="system_prompt_editor",
        help="General system instructions for the talk show format. This is shared by all participants."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(" Save to File", icon=":material/save:", use_container_width=True, key="save_system_prompt"):
            try:
                with open(SYSTEM_PROMPT_PATH, "w", encoding="utf-8") as f:
                    f.write(system_prompt)
                st.session_state.system_prompt_base = system_prompt
                st.success("✅ System prompt saved to `system.txt`", icon=":material/check_circle:")
                logger.info("System prompt saved to file")
            except Exception as e:
                st.error(f"❌ Failed to save: {e}", icon=":material/error:")
                logger.error(f"Failed to save system prompt: {e}", exc_info=True)
    
    with col2:
        if st.button(" Reload from File", icon=":material/refresh:", use_container_width=True, key="reload_system_prompt"):
            try:
                with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
                    loaded = f.read()
                st.session_state.system_prompt_base = loaded
                st.session_state.system_prompt_editor = loaded
                st.success("✅ System prompt reloaded from `system.txt`", icon=":material/check_circle:")
                st.rerun()
            except FileNotFoundError:
                st.warning("⚠️ File not found. Using current session state.", icon=":material/warning:")
            except Exception as e:
                st.error(f"❌ Failed to reload: {e}", icon=":material/error:")
                logger.error(f"Failed to reload system prompt: {e}", exc_info=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# GPT-A Persona
with st.container():
    st.markdown('<div class="settings-section-card">', unsafe_allow_html=True)
    st.markdown("### :material/analytics: GPT-A (The Analyst) Persona")
    st.caption("Specific persona instructions for GPT-A. These are added to the system prompt when GPT-A is speaking.")
    
    persona_a = st.text_area(
        "**GPT-A Persona Instructions**",
        value=st.session_state.persona_gpt_a,
        height=250,
        key="persona_gpt_a_editor",
        help="Detailed persona instructions for GPT-A. These will be included in the system prompt when GPT-A is the active speaker."
    )
    
    if st.button("💾 Save GPT-A Persona", icon=":material/save:", use_container_width=True, key="save_persona_a"):
        st.session_state.persona_gpt_a = persona_a
        st.success("✅ GPT-A persona saved to session state", icon=":material/check_circle:")
        logger.info("GPT-A persona updated")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# GPT-B Persona
with st.container():
    st.markdown('<div class="settings-section-card">', unsafe_allow_html=True)
    st.markdown("### :material/favorite: GPT-B (The Empath) Persona")
    st.caption("Specific persona instructions for GPT-B. These are added to the system prompt when GPT-B is speaking.")
    
    persona_b = st.text_area(
        "**GPT-B Persona Instructions**",
        value=st.session_state.persona_gpt_b,
        height=250,
        key="persona_gpt_b_editor",
        help="Detailed persona instructions for GPT-B. These will be included in the system prompt when GPT-B is the active speaker."
    )
    
    if st.button("💾 Save GPT-B Persona", icon=":material/save:", use_container_width=True, key="save_persona_b"):
        st.session_state.persona_gpt_b = persona_b
        st.success("✅ GPT-B persona saved to session state", icon=":material/check_circle:")
        logger.info("GPT-B persona updated")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# Preview Section
with st.container():
    st.markdown('<div class="settings-section-card">', unsafe_allow_html=True)
    st.markdown("### :material/preview: Preview")
    st.caption("See how the system prompt will look for each model")
    
    preview_tabs = st.tabs(["GPT-A Preview", "GPT-B Preview"])
    
    with preview_tabs[0]:
        preview_a = f"{system_prompt}\n\n{persona_a}\n\nNow continue as GPT-A. Reply only with what you say next."
        st.code(preview_a, language="text")
    
    with preview_tabs[1]:
        preview_b = f"{system_prompt}\n\n{persona_b}\n\nNow continue as GPT-B. Reply only with what you say next."
        st.code(preview_b, language="text")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Auto-save settings when page is viewed
auto_save_session_state()

