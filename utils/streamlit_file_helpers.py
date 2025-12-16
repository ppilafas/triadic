"""
File utility helpers for Streamlit UI components.

Provides reusable functions for file-related operations like formatting
file sizes and parsing file keys.
"""

from typing import Tuple, Optional


def format_file_size(bytes: int) -> str:
    """
    Format file size in bytes to human-readable string.
    
    Args:
        bytes: File size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB", "256 KB", "512 B")
    """
    if bytes > 1024 * 1024:
        return f"{bytes / (1024 * 1024):.1f} MB"
    elif bytes > 1024:
        return f"{bytes / 1024:.1f} KB"
    else:
        return f"{bytes} B"


def parse_file_key(key: str) -> Tuple[str, Optional[int]]:
    """
    Parse file key format "filename:size" to extract filename and size.
    
    Args:
        key: File key in format "filename:size" or just "filename"
        
    Returns:
        Tuple of (filename, size_in_bytes or None)
    """
    if ":" in key:
        parts = key.split(":", 1)
        file_name = parts[0]
        try:
            file_size = int(parts[1])
            return file_name, file_size
        except (ValueError, IndexError):
            return file_name, None
    else:
        return key, None

