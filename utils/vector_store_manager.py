"""
Vector Store Management Module

Provides functions to manage OpenAI vector stores:
- List all vector stores
- Create new vector stores
- Delete vector stores
- Get vector store details
- List files in a vector store
- Attach/detach files from vector stores
"""

from typing import List, Dict, Any, Optional
from openai import OpenAI
from config import OPENAI_API_KEY
from exceptions import VectorStoreError
from utils.logging_config import get_logger

logger = get_logger(__name__)


def get_client() -> OpenAI:
    """Get OpenAI client instance."""
    if not OPENAI_API_KEY:
        raise VectorStoreError("OpenAI API key not configured")
    return OpenAI(api_key=OPENAI_API_KEY)


def list_vector_stores(limit: int = 100) -> List[Dict[str, Any]]:
    """
    List all vector stores for the organization.
    
    Args:
        limit: Maximum number of vector stores to return
    
    Returns:
        List of vector store dictionaries with id, name, status, file_counts, etc.
    
    Raises:
        VectorStoreError: If listing fails
    """
    try:
        client = get_client()
        response = client.vector_stores.list(limit=limit)
        
        stores = []
        for vs in response.data:
            # Handle file_counts - it's a Pydantic object, not a dict
            file_counts_obj = getattr(vs, "file_counts", None)
            file_counts_dict = {}
            if file_counts_obj:
                # Convert Pydantic object to dict
                file_counts_dict = {
                    "in_progress": getattr(file_counts_obj, "in_progress", 0),
                    "completed": getattr(file_counts_obj, "completed", 0),
                    "failed": getattr(file_counts_obj, "failed", 0),
                    "cancelled": getattr(file_counts_obj, "cancelled", 0),
                }
            
            stores.append({
                "id": vs.id,
                "name": getattr(vs, "name", "Unnamed"),
                "status": getattr(vs, "status", "unknown"),
                "file_counts": file_counts_dict,
                "created_at": getattr(vs, "created_at", None),
                "expires_after": getattr(vs, "expires_after", None),
            })
        
        logger.info(f"Listed {len(stores)} vector stores")
        return stores
    except Exception as e:
        logger.error(f"Failed to list vector stores: {e}", exc_info=True)
        raise VectorStoreError(f"Failed to list vector stores: {e}") from e


def get_vector_store_details(vector_store_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific vector store.
    
    Args:
        vector_store_id: ID of the vector store
    
    Returns:
        Dictionary with vector store details
    
    Raises:
        VectorStoreError: If retrieval fails
    """
    try:
        client = get_client()
        vs = client.vector_stores.retrieve(vector_store_id)
        
        # Handle file_counts - it's a Pydantic object, not a dict
        file_counts_obj = getattr(vs, "file_counts", None)
        file_counts_dict = {}
        if file_counts_obj:
            # Convert Pydantic object to dict
            file_counts_dict = {
                "in_progress": getattr(file_counts_obj, "in_progress", 0),
                "completed": getattr(file_counts_obj, "completed", 0),
                "failed": getattr(file_counts_obj, "failed", 0),
                "cancelled": getattr(file_counts_obj, "cancelled", 0),
            }
        
        return {
            "id": vs.id,
            "name": getattr(vs, "name", "Unnamed"),
            "status": getattr(vs, "status", "unknown"),
            "file_counts": file_counts_dict,
            "created_at": getattr(vs, "created_at", None),
            "expires_after": getattr(vs, "expires_after", None),
        }
    except Exception as e:
        logger.error(f"Failed to get vector store details: {e}", exc_info=True)
        raise VectorStoreError(f"Failed to get vector store details: {e}") from e


def create_vector_store(name: str) -> str:
    """
    Create a new vector store.
    
    Args:
        name: Name for the vector store
    
    Returns:
        Vector store ID
    
    Raises:
        VectorStoreError: If creation fails
    """
    try:
        client = get_client()
        vs = client.vector_stores.create(name=name)
        logger.info(f"Created vector store: {vs.id} ({name})")
        return vs.id
    except Exception as e:
        logger.error(f"Failed to create vector store: {e}", exc_info=True)
        raise VectorStoreError(f"Failed to create vector store: {e}") from e


def delete_vector_store(vector_store_id: str) -> None:
    """
    Delete a vector store.
    
    Args:
        vector_store_id: ID of the vector store to delete
    
    Raises:
        VectorStoreError: If deletion fails
    """
    try:
        client = get_client()
        client.vector_stores.delete(vector_store_id)
        logger.info(f"Deleted vector store: {vector_store_id}")
    except Exception as e:
        logger.error(f"Failed to delete vector store: {e}", exc_info=True)
        raise VectorStoreError(f"Failed to delete vector store: {e}") from e


def list_vector_store_files(vector_store_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    List all files in a vector store.
    
    Optimized to use ONLY the vector store files list API call.
    Does NOT make individual API calls per file to avoid runaway loops.
    
    Args:
        vector_store_id: ID of the vector store
        limit: Maximum number of files to return
    
    Returns:
        List of file dictionaries with id, name, status, etc.
        Note: name may be "unknown" if not available from vector store file object
    
    Raises:
        VectorStoreError: If listing fails
    """
    try:
        client = get_client()
        response = client.vector_stores.files.list(
            vector_store_id=vector_store_id,
            limit=limit
        )
        
        files = []
        # Use ONLY data from vector store files list - NO individual API calls
        for file in response.data:
            file_id = file.id
            file_status = getattr(file, "status", "unknown")
            
            # Extract what we can from the vector store file object
            # The vector store file object may not have filename, but that's OK
            # We avoid individual API calls to prevent runaway loops
            files.append({
                "id": file_id,
                "name": getattr(file, "filename", f"file-{file_id[:8]}"),  # Use file ID prefix if no name
                "status": file_status,
                "created_at": getattr(file, "created_at", None),
                "bytes": getattr(file, "bytes", 0),
            })
        
        logger.debug(f"Listed {len(files)} files in vector store {vector_store_id} (no individual API calls)")
        return files
    except Exception as e:
        logger.error(f"Failed to list vector store files: {e}", exc_info=True)
        raise VectorStoreError(f"Failed to list vector store files: {e}") from e


def remove_file_from_vector_store(vector_store_id: str, file_id: str) -> None:
    """
    Remove a file from a vector store.
    
    Args:
        vector_store_id: ID of the vector store
        file_id: ID of the file to remove
    
    Raises:
        VectorStoreError: If removal fails
    """
    try:
        client = get_client()
        client.vector_stores.files.delete(
            vector_store_id=vector_store_id,
            file_id=file_id
        )
        logger.info(f"Removed file {file_id} from vector store {vector_store_id}")
    except Exception as e:
        logger.error(f"Failed to remove file from vector store: {e}", exc_info=True)
        raise VectorStoreError(f"Failed to remove file from vector store: {e}") from e

