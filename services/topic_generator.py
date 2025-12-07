"""
Topic generation service for creating discussion topic suggestions.

This module provides framework-agnostic topic generation that can be used
by both Streamlit and Chainlit interfaces.
"""

from typing import List, Optional
from ai_api import call_model
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Fallback topics if generation fails
FALLBACK_TOPICS = [
    "The future of artificial intelligence",
    "Climate change and sustainability",
    "The impact of technology on society",
    "Philosophy of consciousness",
    "Innovation in healthcare"
]


def generate_topics(
    has_documents: bool,
    vector_store_id: Optional[str] = None,
    model_name: str = "gpt-5-mini"
) -> List[str]:
    """
    Generate discussion topic suggestions using AI.
    
    Args:
        has_documents: Whether documents are indexed in the knowledge base
        vector_store_id: Optional vector store ID for RAG context
        model_name: Model to use for topic generation (default: gpt-5-mini)
    
    Returns:
        List of topic suggestion strings (up to 5 topics)
    """
    try:
        # Build context-aware prompt
        if has_documents:
            prompt = """Generate 5 engaging discussion topics for a podcast conversation between two AI personas. 
The topics should be relevant to the documents that have been uploaded to the knowledge base.
Return only the topics, one per line, without numbering or bullets. Keep each topic concise (5-10 words)."""
        else:
            prompt = """Generate 5 engaging discussion topics for a podcast conversation between two AI personas.
Topics should be thought-provoking and suitable for deep discussion. 
Return only the topics, one per line, without numbering or bullets. Keep each topic concise (5-10 words)."""
        
        # Use a lightweight model for topic generation
        # Note: file_search tool requires reasoning_effort to be at least 'medium'
        # Use 'minimal' only when no vector store is provided (no file_search needed)
        reasoning_effort = "medium" if vector_store_id else "minimal"
        
        api_config = {
            "model_name": model_name,
            "reasoning_effort": reasoning_effort,
            "text_verbosity": "low",
            "reasoning_summary_enabled": False,
            "vector_store_id": vector_store_id  # Include for RAG if available
        }
        
        response = call_model(prompt, config=api_config)
        
        # Parse response into list of topics
        topics = [line.strip() for line in response.strip().split("\n") if line.strip()]
        # Filter out any lines that look like explanations or metadata
        topics = [t for t in topics if not t.startswith(("Here", "Here are", "Topics:", "1.", "2.", "3.", "-"))]
        # Limit to 5 topics
        topics = topics[:5]
        
        # If parsing failed, provide fallback topics
        if not topics or len(topics) < 3:
            logger.warning("Topic parsing failed or insufficient topics, using fallbacks")
            return FALLBACK_TOPICS
        
        logger.info(f"Generated {len(topics)} topic suggestions")
        return topics
        
    except Exception as e:
        logger.error(f"Error generating topic suggestions: {e}", exc_info=True)
        # Return fallback topics on error
        return FALLBACK_TOPICS

