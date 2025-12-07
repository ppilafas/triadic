"""
Streamlit CSS styling module.

Contains all custom CSS for the Streamlit UI, organized by component type.
CSS is loaded from external file for better maintainability.
"""

import streamlit as st
from pathlib import Path
from utils.logging_config import get_logger

logger = get_logger(__name__)

# CSS file path (relative to project root)
_CSS_FILE_PATH = Path(__file__).parent.parent / "public" / "streamlit.css"

# Cache CSS content at module load (performance optimization)
_CSS_CACHE: str | None = None


def _load_css_file() -> str:
    """
    Load CSS from external file.
    
    Returns:
        CSS content as string (without <style> tags)
    
    Raises:
        FileNotFoundError: If CSS file doesn't exist
    """
    global _CSS_CACHE
    
    # Return cached content if available
    if _CSS_CACHE is not None:
        return _CSS_CACHE
    
    # Load from file
    try:
        with open(_CSS_FILE_PATH, "r", encoding="utf-8") as f:
            _CSS_CACHE = f.read()
        logger.debug(f"Loaded CSS from {_CSS_FILE_PATH} ({len(_CSS_CACHE)} characters)")
        return _CSS_CACHE
    except FileNotFoundError:
        logger.error(f"CSS file not found: {_CSS_FILE_PATH}")
        # Return minimal fallback CSS
        return "/* CSS file not found - using fallback */"


def get_custom_css() -> str:
    """
    Get all custom CSS for the Streamlit UI.
    
    Loads CSS from external file and wraps it in <style> tags with scoping.
    This is the native Streamlit approach - CSS must be injected via st.markdown().
    
    Returns:
        Complete CSS string ready to inject via st.markdown (wrapped in <style> tags with scoping)
    """
    css_content = _load_css_file()
    # Add scoping attribute to prevent CSS conflicts with other Streamlit apps/components
    return f'<style data-triadic-scope>\n{css_content}\n</style>'


def inject_custom_css() -> None:
    """
    Inject scoped custom CSS into Streamlit app.
    
    Uses data attribute for scoping to prevent conflicts with other CSS.
    This is a native Streamlit pattern with improved isolation.
    """
    st.markdown(get_custom_css(), unsafe_allow_html=True)
