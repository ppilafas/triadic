"""
Custom exception classes for Triadic application.
Provides better error handling and debugging context.
"""


class TriadicError(Exception):
    """Base exception for all Triadic application errors"""
    pass


class ConfigurationError(TriadicError):
    """Error related to application configuration"""
    pass


class VectorStoreError(TriadicError):
    """Error creating or accessing vector store"""
    pass


class TranscriptionError(TriadicError):
    """Error during audio transcription"""
    pass


class ModelGenerationError(TriadicError):
    """Error during model response generation"""
    pass


class FileIndexingError(TriadicError):
    """Error during file indexing for RAG"""
    pass


class ValidationError(TriadicError):
    """Error during input validation"""
    pass


class SessionError(TriadicError):
    """Error related to session management"""
    pass

