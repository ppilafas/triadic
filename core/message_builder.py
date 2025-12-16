"""
Message and prompt building - Framework-agnostic.

Handles system prompt loading and prompt construction from conversation history.
"""

from typing import List, Dict, Any, Tuple, Optional
from config import speaker_config, SYSTEM_PROMPT_PATH
from utils.logging_config import get_logger
from core.conversation import get_next_speaker_key

logger = get_logger(__name__)

# Speaker profiles from config
SPEAKER_PROFILES = speaker_config.PROFILES


def load_system_prompt() -> str:
    """
    Load system prompt from file.
    
    Returns:
        System prompt text or default if file not found
    """
    try:
        with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"System prompt not found at {SYSTEM_PROMPT_PATH}, using default")
        return "Participate in a talk show. Be concise."


def build_prompt(history: List[Dict[str, str]]) -> Tuple[str, str]:
    """
    Build prompt from conversation history (Chainlit format).
    
    Args:
        history: List of message dictionaries with 'author', 'author_key', and 'content'
    
    Returns:
        Tuple of (prompt_text, next_speaker_key)
    """
    system_prompt = load_system_prompt()
    script = f"{system_prompt}\n\nTranscript so far:\n\n"
    
    for msg in history:
        script += f"{msg['author']}: {msg['content']}\n"
    
    last_speaker_key = history[-1].get('author_key', 'host') if history else 'host'
    next_speaker = get_next_speaker_key(last_speaker_key)
    
    script += f"\nContinue as {SPEAKER_PROFILES[next_speaker]['name']}."
    logger.debug(f"Built prompt for {next_speaker}, length: {len(script)}")
    return script, next_speaker


def build_prompt_from_messages(
    next_speaker: str, 
    messages: List[Dict[str, Any]], 
    available_tools: Optional[List[str]] = None
) -> str:
    """
    Build prompt from Streamlit message format.
    
    Args:
        next_speaker: Next speaker key (gpt_a or gpt_b)
        messages: List of message dicts with 'speaker' and 'content'
        available_tools: List of available tool names (e.g., ['web_search', 'file_search'])
    
    Returns:
        Formatted prompt string
    """
    system_instructions = load_system_prompt()
    lines = [system_instructions]
    
    # Add persona-specific instructions if available in session state
    try:
        import streamlit as st
        if next_speaker == "gpt_a" and "persona_gpt_a" in st.session_state:
            persona = st.session_state.persona_gpt_a.strip()
            if persona:
                lines.append("")
                lines.append(persona)
        elif next_speaker == "gpt_b" and "persona_gpt_b" in st.session_state:
            persona = st.session_state.persona_gpt_b.strip()
            if persona:
                lines.append("")
                lines.append(persona)
    except (ImportError, RuntimeError):
        # Not in Streamlit context, skip persona instructions
        pass
    
    # Add tool availability information if tools are available
    if available_tools:
        tool_info = []
        if "web_search" in available_tools:
            tool_info.append("web search (to find current information, recent events, or verify facts)")
        if "file_search" in available_tools:
            tool_info.append("file search (to search through uploaded documents)")
        
        if tool_info:
            lines.append("")
            lines.append("IMPORTANT - Available Tools:")
            lines.append("You have access to the following tools that you can and should use automatically:")
            for tool_desc in tool_info:
                lines.append(f"- {tool_desc}")
            lines.append("")
            lines.append("Tool Usage Guidelines:")
            lines.append("- Use web search when discussing current events, recent news, or when you need up-to-date information")
            lines.append("- Use web search to verify facts, statistics, or claims that might be outdated")
            lines.append("- Use file search when the conversation references uploaded documents or when searching documents would help")
            lines.append("- The tools will be called automatically - you don't need to ask permission, just use them when relevant")
            lines.append("- Incorporate tool results naturally into your response without mentioning the tool usage")
    
    lines.extend(["", "Transcript so far:", ""])
    
    for m in messages:
        speaker_key = m.get("speaker", "host")
        if speaker_key == "host":
            label = "Host"
        elif speaker_key == "gpt_a":
            label = "GPT-A"
        else:
            label = "GPT-B"
        lines.append(f"{label}: {m.get('content', '')}")
    
    target = "GPT-A" if next_speaker == "gpt_a" else "GPT-B"
    lines.append(f"\nNow continue as {target}. Reply only with what you say next.")
    
    prompt_text = "\n".join(lines)
    logger.debug(f"Built prompt for {next_speaker}, length: {len(prompt_text)}")
    return prompt_text

