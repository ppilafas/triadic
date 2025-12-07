"""
Conversation state management - Framework-agnostic.

Manages conversation history, speaker alternation, and turn counting.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from config import speaker_config
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Speaker profiles from config
SPEAKER_PROFILES = speaker_config.PROFILES


@dataclass
class ConversationState:
    """
    Represents the state of a conversation.
    
    Attributes:
        messages: List of message dictionaries
        next_speaker: Next speaker key (gpt_a or gpt_b)
        turn_count: Number of AI turns completed
    """
    messages: List[Dict[str, Any]] = field(default_factory=list)
    next_speaker: str = "gpt_a"
    turn_count: int = 0
    
    def add_message(
        self,
        speaker_key: str,
        content: str,
        audio_bytes: Optional[bytes] = None,
        timestamp: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Add a message to the conversation.
        
        Args:
            speaker_key: Speaker key (host, gpt_a, gpt_b)
            content: Message content
            audio_bytes: Optional audio data
            timestamp: Optional timestamp
            **kwargs: Additional message metadata
        """
        message = {
            "speaker": speaker_key,
            "author_key": speaker_key,  # For compatibility
            "author": self._get_author_name(speaker_key),
            "content": content,
            "audio_bytes": audio_bytes,
            "timestamp": timestamp,
            **kwargs
        }
        self.messages.append(message)
        
        # Update next speaker if this was an AI turn
        if speaker_key in ["gpt_a", "gpt_b"]:
            self.turn_count += 1
            self.next_speaker = get_next_speaker_key(speaker_key)
    
    def _get_author_name(self, speaker_key: str) -> str:
        """Get display name for speaker key."""
        if speaker_key == "host":
            return "Host"
        elif speaker_key == "gpt_a":
            return "GPT-A"
        elif speaker_key == "gpt_b":
            return "GPT-B"
        else:
            return speaker_key
    
    def get_history(self, format: str = "chainlit") -> List[Dict[str, Any]]:
        """
        Get conversation history in specified format.
        
        Args:
            format: Format type ("chainlit" or "streamlit")
        
        Returns:
            List of message dictionaries in requested format
        """
        if format == "chainlit":
            return [
                {
                    "author": msg.get("author", msg.get("speaker", "Unknown")),
                    "author_key": msg.get("author_key", msg.get("speaker", "unknown")),
                    "content": msg.get("content", "")
                }
                for msg in self.messages
            ]
        else:  # streamlit format
            return [
                {
                    "speaker": msg.get("speaker", msg.get("author_key", "host")),
                    "content": msg.get("content", ""),
                    "audio_bytes": msg.get("audio_bytes"),
                    "timestamp": msg.get("timestamp"),
                    "chars": msg.get("chars", len(msg.get("content", "")))
                }
                for msg in self.messages
            ]
    
    def reset(self, keep_welcome: bool = True) -> None:
        """
        Reset conversation to initial state.
        
        Args:
            keep_welcome: If True, keep the welcome message
        """
        if keep_welcome and self.messages:
            welcome_msg = self.messages[0]
            self.messages = [welcome_msg]
        else:
            self.messages = []
        self.next_speaker = "gpt_a"
        self.turn_count = 0
        logger.info("Conversation reset")


def get_next_speaker_key(last_speaker_key: str) -> str:
    """
    Determine the next speaker key (alternating between gpt_a and gpt_b).
    
    Args:
        last_speaker_key: The key of the last speaker
    
    Returns:
        Next speaker key (gpt_a or gpt_b)
    """
    if last_speaker_key == "host":
        return "gpt_a"
    elif last_speaker_key == "gpt_a":
        return "gpt_b"
    else:
        return "gpt_a"


def get_next_speaker_display_name(last_speaker_key: str) -> str:
    """
    Get the display name of the next speaker.
    
    Args:
        last_speaker_key: The key of the last speaker
    
    Returns:
        Display name (GPT-A or GPT-B)
    """
    next_key = get_next_speaker_key(last_speaker_key)
    return "GPT-A" if next_key == "gpt_a" else "GPT-B"


def calculate_turn_count(history: List[Dict[str, Any]]) -> int:
    """
    Calculate the number of AI turns (excludes host messages).
    
    Args:
        history: List of message dictionaries
    
    Returns:
        Number of turns by gpt_a or gpt_b
    """
    return len([
        m for m in history 
        if m.get("author_key") in ["gpt_a", "gpt_b"] or 
           m.get("speaker") in ["gpt_a", "gpt_b"]
    ])

