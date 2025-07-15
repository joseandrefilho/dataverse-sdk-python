"""
Custom exceptions for the Dataverse SDK.

This module defines all custom exceptions used throughout the SDK,
providing clear error handling and debugging capabilities.
"""

from typing import Any, Dict, Optional


class DataverseSDKError(Exception):
    """Base exception for all Dataverse SDK errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class AuthenticationError(DataverseSDKError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(DataverseSDKError):
    """Raised when authorization fails (insufficient permissions)."""
    pass


class ConnectionError(DataverseSDKError):
    """Raised when connection to Dataverse fails."""
    pass


class TimeoutError(DataverseSDKError):
    """Raised when a request times out."""
    pass


class RateLimitError(DataverseSDKError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code, details)
        self.retry_after = retry_after


class ValidationError(DataverseSDKError):
    """Raised when data validation fails."""
    pass


class EntityNotFoundError(DataverseSDKError):
    """Raised when an entity is not found."""
    
    def __init__(
        self,
        entity_type: str,
        entity_id: Optional[str] = None,
        message: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        if message is None:
            if entity_id:
                message = f"{entity_type} with ID '{entity_id}' not found"
            else:
                message = f"{entity_type} not found"
        
        super().__init__(message, error_code, details)
        self.entity_type = entity_type
        self.entity_id = entity_id


class DuplicateEntityError(DataverseSDKError):
    """Raised when attempting to create a duplicate entity."""
    pass


class BatchOperationError(DataverseSDKError):
    """Raised when a batch operation fails."""
    
    def __init__(
        self,
        message: str,
        failed_operations: Optional[list] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code, details)
        self.failed_operations = failed_operations or []


class MetadataError(DataverseSDKError):
    """Raised when metadata operations fail."""
    pass


class FetchXMLError(DataverseSDKError):
    """Raised when FetchXML operations fail."""
    pass


class ConfigurationError(DataverseSDKError):
    """Raised when SDK configuration is invalid."""
    pass


class APIError(DataverseSDKError):
    """Raised when the Dataverse API returns an error."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code, details)
        self.status_code = status_code
        self.response_data = response_data or {}


# Convenience exports
__all__ = [
    "DataverseSDKError",
    "AuthenticationError", 
    "AuthorizationError",
    "ConnectionError",
    "TimeoutError",
    "RateLimitError",
    "ValidationError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "BatchOperationError",
    "MetadataError",
    "FetchXMLError",
    "ConfigurationError",
    "APIError",
]

