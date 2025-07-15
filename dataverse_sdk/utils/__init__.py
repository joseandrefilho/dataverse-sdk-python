"""
Utility functions and helpers for the Dataverse SDK.

This module provides common utilities used throughout the SDK,
including retry logic, configuration management, and helper functions.
"""

import asyncio
import os
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from urllib.parse import urljoin, urlparse

import structlog
from tenacity import (
    AsyncRetrying,
    RetryError,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from ..exceptions import RateLimitError, ConnectionError, TimeoutError


logger = structlog.get_logger(__name__)

T = TypeVar("T")


class Config:
    """Configuration management for the Dataverse SDK."""
    
    def __init__(self, **kwargs: Any) -> None:
        """Initialize configuration with default values and overrides."""
        # Default configuration
        self._config = {
            # Connection settings
            "max_connections": 100,
            "max_keepalive_connections": 20,
            "keepalive_expiry": 30,
            
            # Timeout settings (in seconds)
            "connect_timeout": 10.0,
            "read_timeout": 30.0,
            "write_timeout": 10.0,
            "pool_timeout": 5.0,
            
            # Retry settings
            "max_retries": 3,
            "backoff_factor": 1.0,
            "retry_status_codes": [429, 500, 502, 503, 504],
            
            # Batch settings
            "default_batch_size": 100,
            "max_batch_size": 1000,
            
            # Logging
            "log_level": "INFO",
            "log_format": "json",
            "enable_telemetry": False,
            
            # Development
            "debug": False,
            "enable_mock_mode": False,
        }
        
        # Load from environment variables
        self._load_from_env()
        
        # Apply overrides
        self._config.update(kwargs)
        
        logger.debug("Configuration initialized", config=self._config)
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            "MAX_CONNECTIONS": ("max_connections", int),
            "MAX_KEEPALIVE_CONNECTIONS": ("max_keepalive_connections", int),
            "KEEPALIVE_EXPIRY": ("keepalive_expiry", int),
            "CONNECT_TIMEOUT": ("connect_timeout", float),
            "READ_TIMEOUT": ("read_timeout", float),
            "WRITE_TIMEOUT": ("write_timeout", float),
            "POOL_TIMEOUT": ("pool_timeout", float),
            "MAX_RETRIES": ("max_retries", int),
            "BACKOFF_FACTOR": ("backoff_factor", float),
            "RETRY_STATUS_CODES": ("retry_status_codes", lambda x: [int(i) for i in x.split(",")]),
            "DEFAULT_BATCH_SIZE": ("default_batch_size", int),
            "MAX_BATCH_SIZE": ("max_batch_size", int),
            "LOG_LEVEL": ("log_level", str),
            "LOG_FORMAT": ("log_format", str),
            "ENABLE_TELEMETRY": ("enable_telemetry", lambda x: x.lower() in ("true", "1", "yes")),
            "DEBUG": ("debug", lambda x: x.lower() in ("true", "1", "yes")),
            "ENABLE_MOCK_MODE": ("enable_mock_mode", lambda x: x.lower() in ("true", "1", "yes")),
        }
        
        for env_var, (config_key, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    self._config[config_key] = converter(value)
                except (ValueError, TypeError) as e:
                    logger.warning(
                        "Invalid environment variable value",
                        env_var=env_var,
                        value=value,
                        error=str(e),
                    )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value
        logger.debug("Configuration updated", key=key, value=value)
    
    def update(self, **kwargs: Any) -> None:
        """Update multiple configuration values."""
        self._config.update(kwargs)
        logger.debug("Configuration updated", updates=kwargs)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()


def build_url(base_url: str, *path_parts: str, **query_params: Any) -> str:
    """
    Build a URL from base URL, path parts, and query parameters.
    
    Args:
        base_url: Base URL
        *path_parts: Path segments to append
        **query_params: Query parameters to add
        
    Returns:
        Complete URL string
    """
    # Ensure base URL ends with /
    if not base_url.endswith("/"):
        base_url += "/"
    
    # Join path parts
    url = base_url
    for part in path_parts:
        part = str(part).strip("/")
        if part:
            url = urljoin(url, part + "/")
    
    # Remove trailing slash if no query params
    if not query_params and url.endswith("/") and url != base_url:
        url = url.rstrip("/")
    
    # Add query parameters
    if query_params:
        from urllib.parse import urlencode
        query_string = urlencode(query_params)
        url = f"{url}?{query_string}"
    
    return url


def parse_odata_url(url: str) -> Dict[str, Any]:
    """
    Parse OData URL and extract components.
    
    Args:
        url: OData URL to parse
        
    Returns:
        Dictionary with parsed components
    """
    parsed = urlparse(url)
    
    # Extract path components
    path_parts = [part for part in parsed.path.split("/") if part]
    
    # Parse query parameters
    from urllib.parse import parse_qs
    query_params = parse_qs(parsed.query)
    
    # Flatten single-value parameters
    for key, values in query_params.items():
        if len(values) == 1:
            query_params[key] = values[0]
    
    return {
        "scheme": parsed.scheme,
        "netloc": parsed.netloc,
        "path": parsed.path,
        "path_parts": path_parts,
        "query": parsed.query,
        "query_params": query_params,
        "fragment": parsed.fragment,
    }


def chunk_list(items: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        items: List to chunk
        chunk_size: Maximum size of each chunk
        
    Returns:
        List of chunks
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")
    
    chunks = []
    for i in range(0, len(items), chunk_size):
        chunks.append(items[i:i + chunk_size])
    
    return chunks


def extract_entity_id(entity_ref: Union[str, Dict[str, Any]]) -> Optional[str]:
    """
    Extract entity ID from various reference formats.
    
    Args:
        entity_ref: Entity reference (ID string, URL, or object with ID)
        
    Returns:
        Entity ID string or None if not found
    """
    if isinstance(entity_ref, str):
        # Check if it's a GUID
        if len(entity_ref) == 36 and entity_ref.count("-") == 4:
            return entity_ref
        
        # Check if it's a URL with ID
        if "/" in entity_ref:
            parts = entity_ref.split("/")
            for part in reversed(parts):
                if len(part) == 36 and part.count("-") == 4:
                    return part
    
    elif isinstance(entity_ref, dict):
        # Look for common ID fields
        for field in ["id", "entityid", "objectid", "recordid"]:
            if field in entity_ref:
                return str(entity_ref[field])
    
    return None


def format_odata_filter(filters: Dict[str, Any]) -> str:
    """
    Format filters as OData $filter query parameter.
    
    Args:
        filters: Dictionary of field filters
        
    Returns:
        OData filter string
    """
    filter_parts = []
    
    for field, value in filters.items():
        if isinstance(value, str):
            filter_parts.append(f"{field} eq '{value}'")
        elif isinstance(value, (int, float)):
            filter_parts.append(f"{field} eq {value}")
        elif isinstance(value, bool):
            filter_parts.append(f"{field} eq {str(value).lower()}")
        elif isinstance(value, dict):
            # Handle operators like {"gt": 100}, {"contains": "text"}
            for op, op_value in value.items():
                if op == "contains":
                    filter_parts.append(f"contains({field}, '{op_value}')")
                elif op == "startswith":
                    filter_parts.append(f"startswith({field}, '{op_value}')")
                elif op == "endswith":
                    filter_parts.append(f"endswith({field}, '{op_value}')")
                else:
                    filter_parts.append(f"{field} {op} {op_value}")
    
    return " and ".join(filter_parts)


async def retry_with_backoff(
    func: Callable[..., T],
    *args: Any,
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    retry_exceptions: tuple = (ConnectionError, TimeoutError),
    **kwargs: Any,
) -> T:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        *args: Function arguments
        max_retries: Maximum number of retries
        backoff_factor: Backoff multiplier
        retry_exceptions: Exceptions to retry on
        **kwargs: Function keyword arguments
        
    Returns:
        Function result
        
    Raises:
        RetryError: If all retries are exhausted
    """
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(max_retries + 1),
        wait=wait_exponential(multiplier=backoff_factor),
        retry=retry_if_exception_type(retry_exceptions),
    ):
        with attempt:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)


def handle_rate_limit(response_headers: Dict[str, str]) -> Optional[int]:
    """
    Extract rate limit information from response headers.
    
    Args:
        response_headers: HTTP response headers
        
    Returns:
        Retry-after seconds if rate limited, None otherwise
    """
    # Check for rate limit headers
    retry_after = response_headers.get("Retry-After")
    if retry_after:
        try:
            return int(retry_after)
        except ValueError:
            # Retry-After might be a date, not seconds
            pass
    
    # Check for custom Dataverse rate limit headers
    remaining = response_headers.get("x-ms-resource-usage")
    if remaining:
        # Parse resource usage header
        # Format: "ApiRequests=123/1000,PerConnectionApiRequests=456/1000"
        try:
            for part in remaining.split(","):
                if "ApiRequests=" in part:
                    usage_info = part.split("=")[1]
                    current, limit = map(int, usage_info.split("/"))
                    if current >= limit * 0.9:  # 90% threshold
                        return 60  # Wait 1 minute
        except (ValueError, IndexError):
            pass
    
    return None


def sanitize_entity_name(name: str) -> str:
    """
    Sanitize entity name for use in URLs and identifiers.
    
    Args:
        name: Entity name to sanitize
        
    Returns:
        Sanitized entity name
    """
    # Remove special characters and convert to lowercase
    import re
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "", name.lower())
    
    # Ensure it starts with a letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = "entity_" + sanitized
    
    return sanitized or "entity"


def format_datetime(dt: Any) -> str:
    """
    Format datetime for OData queries.
    
    Args:
        dt: Datetime object or string
        
    Returns:
        ISO formatted datetime string
    """
    if hasattr(dt, "isoformat"):
        return dt.isoformat()
    elif isinstance(dt, str):
        return dt
    else:
        return str(dt)


# Convenience exports
__all__ = [
    "Config",
    "build_url",
    "parse_odata_url",
    "chunk_list",
    "extract_entity_id",
    "format_odata_filter",
    "retry_with_backoff",
    "handle_rate_limit",
    "sanitize_entity_name",
    "format_datetime",
]

