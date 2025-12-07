"""
Conversation summarization service for generating periodic discussion summaries.

This module provides framework-agnostic conversation summarization that can be used
by both Streamlit and Chainlit interfaces.
"""

from typing import List, Optional, Dict, Any
from ai_api import call_model
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Default summary interval (every N turns)
DEFAULT_SUMMARY_INTERVAL = 5


def generate_conversation_summary(
    messages: List[Dict[str, Any]],
    previous_summary: Optional[str] = None,
    model_name: str = "gpt-5-mini"
) -> str:
    """
    Generate a concise summary of the conversation so far.
    
    Args:
        messages: List of conversation messages
        previous_summary: Optional previous summary to build upon (for incremental summaries)
        model_name: Model to use for summarization (default: gpt-5-mini)
    
    Returns:
        Concise summary string (2-3 sentences)
    """
    try:
        # Extract conversation text (exclude audio and metadata)
        conversation_text = []
        for msg in messages:
            speaker = msg.get("speaker", "unknown")
            content = msg.get("content", "")
            if content and not content.startswith("(Error"):
                # Format: "Speaker: content"
                speaker_name = {
                    "host": "Host",
                    "gpt_a": "GPT-A",
                    "gpt_b": "GPT-B"
                }.get(speaker, speaker)
                conversation_text.append(f"{speaker_name}: {content}")
        
        conversation_str = "\n".join(conversation_text[-20:])  # Last 20 messages for context
        
        # Build prompt
        if previous_summary:
            prompt = f"""Based on the previous summary and new conversation, provide a concise 2-3 sentence summary of the discussion progress.

Previous Summary: {previous_summary}

Recent Conversation:
{conversation_str}

Provide an updated summary that captures:
1. The main topics being discussed
2. Key points or conclusions reached
3. The current direction of the conversation

Keep it concise (2-3 sentences, max 150 words)."""
        else:
            prompt = f"""Provide a concise 2-3 sentence summary of this podcast conversation.

Conversation:
{conversation_str}

Summarize:
1. The main topics being discussed
2. Key points or conclusions reached
3. The current direction of the conversation

Keep it concise (2-3 sentences, max 150 words)."""
        
        # Use lightweight model for summarization
        # Note: file_search and web_search tools require reasoning_effort to be at least 'medium'
        # For summaries, we use 'minimal' reasoning, so we must explicitly disable all tools
        api_config = {
            "model_name": model_name,
            "reasoning_effort": "minimal",  # Summarization doesn't need high reasoning
            "text_verbosity": "low",
            "reasoning_summary_enabled": False,
            "web_search_enabled": False,  # Explicitly disable web_search
            "vector_store_id": "",  # Explicitly disable file_search (empty string prevents tool addition)
        }
        
        summary = call_model(prompt, config=api_config)
        
        # Clean up the summary
        summary = summary.strip()
        # Remove any prefix like "Summary:" or "Here's a summary:"
        if summary.lower().startswith("summary:"):
            summary = summary[8:].strip()
        if summary.lower().startswith("here's a summary:"):
            summary = summary[17:].strip()
        
        logger.info(f"Generated conversation summary: {len(summary)} characters")
        return summary
        
    except Exception as e:
        logger.error(f"Error generating conversation summary: {e}", exc_info=True)
        return "Summary generation failed. Conversation in progress."


def should_generate_summary(total_turns: int, summary_interval: int = DEFAULT_SUMMARY_INTERVAL) -> bool:
    """
    Check if a summary should be generated based on turn count.
    
    Args:
        total_turns: Current total number of turns
        summary_interval: Interval between summaries (default: 5)
    
    Returns:
        True if summary should be generated, False otherwise
    """
    return total_turns > 0 and total_turns % summary_interval == 0

