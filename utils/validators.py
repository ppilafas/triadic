"""
Input validation utilities for Triadic application.
"""
from typing import Any
from config import model_config, timing_config
from exceptions import ValidationError


def validate_model_name(model: str) -> str:
    """Validate that model name is in allowed list."""
    if model not in model_config.ALLOWED_MODELS:
        raise ValidationError(
            f"Invalid model: {model}. Must be one of {model_config.ALLOWED_MODELS}"
        )
    return model


def validate_reasoning_effort(effort: str) -> str:
    """Validate that reasoning effort is in allowed list."""
    if effort not in model_config.ALLOWED_EFFORT_LEVELS:
        raise ValidationError(
            f"Invalid reasoning effort: {effort}. Must be one of {model_config.ALLOWED_EFFORT_LEVELS}"
        )
    return effort


def validate_auto_delay(delay: float) -> float:
    """Validate that auto delay is within allowed range."""
    if not (timing_config.MIN_AUTO_DELAY <= delay <= timing_config.MAX_AUTO_DELAY):
        raise ValidationError(
            f"Invalid auto delay: {delay}. Must be between {timing_config.MIN_AUTO_DELAY} "
            f"and {timing_config.MAX_AUTO_DELAY} seconds"
        )
    return delay


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and other issues."""
    # Remove path components
    filename = filename.replace("/", "_").replace("\\", "_")
    # Remove null bytes
    filename = filename.replace("\x00", "")
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    return filename

