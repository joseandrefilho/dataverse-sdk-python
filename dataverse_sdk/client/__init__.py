"""
Async HTTP client for Microsoft Dataverse SDK.

This module provides the core async HTTP client with connection pooling,
retry logic, rate limiting, and hook integration.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import httpx
import structlog
from tenacity import (
    AsyncRetrying,
    RetryError,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from ..auth import DataverseAuthenticator
from ..exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    RateLimitError,
    TimeoutError,
)
from ..hooks import (
    HookContext,
    HookManager,
    HookType,
    execute_global_hooks,
)
from ..utils import Config, build_url, handle_rate_limit


logger = structlog.get_logger(__name__)


class AsyncDataverseClient:
    """
    Async HTTP client for Microsoft Dataverse with enterprise features.
    
    Features:
    - Connection pooling and keep-alive
    - Automatic retry with exponential backoff
    - Rate limit handling
    - Hook system for extensibility
    - Comprehensive error handling
    - Request/response logging
    """
    
    def __init__(
        self,
        dataverse_url: str,
        authenticator: DataverseAuthenticator,
        config: Optional[Config] = None,
        hook_manager: Optional[HookManager] = None,
    ) -> None:
        """
        Initialize the Dataverse client.
        
        Args:
            dataverse_url: Dataverse environment URL
            authenticator: Authentication handler
            config: Configuration object
            hook_manager: Hook manager for extensibility
        """
        self.dataverse_url = dataverse_url.rstrip("/")
        self.authenticator = authenticator
        self.config = config or Config()
        self.hook_manager = hook_manager or HookManager()
        
        # Build API base URL
        api_version = "v9.2"  # Default API version
        self.api_base_url = f"{self.dataverse_url}/api/data/{api_version}/"
        
        # HTTP client will be initialized in __aenter__
        self._client: Optional[httpx.AsyncClient] = None
        self._closed = False
        
        logger.info(
            "Dataverse client initialized",
            dataverse_url=dataverse_url,
            api_base_url=self.api_base_url,
        )
    
    async def __aenter__(self) -> "AsyncDataverseClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_client(self) -> None:
        """Ensure HTTP client is initialized."""
        if self._client is None or self._client.is_closed:
            # Configure timeouts
            timeout = httpx.Timeout(
                connect=self.config.get("connect_timeout", 10.0),
                read=self.config.get("read_timeout", 30.0),
                write=self.config.get("write_timeout", 10.0),
                pool=self.config.get("pool_timeout", 5.0),
            )
            
            # Configure connection limits
            limits = httpx.Limits(
                max_connections=self.config.get("max_connections", 100),
                max_keepalive_connections=self.config.get("max_keepalive_connections", 20),
                keepalive_expiry=self.config.get("keepalive_expiry", 30),
            )
            
            # Configure proxy settings
            proxy = None
            proxy_url = self.config.get("proxy_url")
            if proxy_url:
                proxy_username = self.config.get("proxy_username")
                proxy_password = self.config.get("proxy_password")
                
                if proxy_username and proxy_password:
                    # Add auth to proxy URL
                    from urllib.parse import urlparse, urlunparse
                    parsed = urlparse(proxy_url)
                    auth_proxy_url = urlunparse((
                        parsed.scheme,
                        f"{proxy_username}:{proxy_password}@{parsed.netloc}",
                        parsed.path,
                        parsed.params,
                        parsed.query,
                        parsed.fragment
                    ))
                    proxy = auth_proxy_url
                else:
                    proxy = proxy_url
            
            # Configure SSL/TLS settings
            verify_ssl = self.config.get("verify_ssl", True)
            ssl_context = self.config.get("ssl_context")
            ssl_cert_file = self.config.get("ssl_cert_file")
            ssl_key_file = self.config.get("ssl_key_file")
            ssl_ca_bundle = self.config.get("ssl_ca_bundle")
            
            # Handle SSL verification
            if not verify_ssl:
                verify = False
                # Disable SSL warnings if requested
                if self.config.get("disable_ssl_warnings", False):
                    import urllib3
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            elif ssl_ca_bundle:
                verify = ssl_ca_bundle
            else:
                verify = True
            
            # Handle client certificates
            cert = None
            if ssl_cert_file:
                if ssl_key_file:
                    cert = (ssl_cert_file, ssl_key_file)
                else:
                    cert = ssl_cert_file
            
            # Create HTTP client
            client_kwargs = {
                "timeout": timeout,
                "limits": limits,
                "follow_redirects": True,
                "verify": verify,
                "trust_env": self.config.get("trust_env", True),
                "headers": {
                    "User-Agent": "dataverse-sdk/1.0.0",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "OData-MaxVersion": "4.0",
                    "OData-Version": "4.0",
                },
            }
            
            # Add proxy configuration
            if proxy:
                client_kwargs["proxy"] = proxy
            
            # Add client certificate
            if cert:
                client_kwargs["cert"] = cert
            
            # Add custom SSL context if provided
            if ssl_context:
                client_kwargs["verify"] = ssl_context
            
            self._client = httpx.AsyncClient(**client_kwargs)
            
            self._closed = False
            logger.debug(
                "HTTP client initialized",
                proxy_configured=bool(proxy),
                ssl_verification=verify_ssl,
                client_cert=bool(cert),
            )
    
    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.debug("HTTP client closed")
        
        self._closed = True
    
    def is_closed(self) -> bool:
        """Check if the client is closed."""
        return self._closed or (self._client is not None and self._client.is_closed)
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        try:
            token = await self.authenticator.get_token()
            return {"Authorization": f"Bearer {token}"}
        except Exception as e:
            logger.error("Failed to get authentication token", error=str(e))
            raise AuthenticationError(f"Authentication failed: {str(e)}") from e
    
    async def _execute_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        content: Optional[bytes] = None,
    ) -> httpx.Response:
        """
        Execute HTTP request with retry logic and hook integration.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            params: Query parameters
            json_data: JSON request body
            content: Raw request content
            
        Returns:
            HTTP response
            
        Raises:
            Various SDK exceptions based on response
        """
        await self._ensure_client()
        
        # Prepare request data
        request_data = {
            "method": method.upper(),
            "url": url,
            "headers": headers or {},
            "params": params or {},
            "json": json_data,
            "content": content,
        }
        
        # Add authentication headers
        auth_headers = await self._get_auth_headers()
        request_data["headers"].update(auth_headers)
        
        # Execute before_request hooks
        context = HookContext(
            hook_type=HookType.BEFORE_REQUEST,
            request_data=request_data,
        )
        context = await execute_global_hooks(HookType.BEFORE_REQUEST, context)
        context = await self.hook_manager.execute_hooks(HookType.BEFORE_REQUEST, context)
        
        # Update request data from hooks
        request_data = context.request_data
        
        # Configure retry logic
        max_retries = self.config.get("max_retries", 3)
        backoff_factor = self.config.get("backoff_factor", 1.0)
        retry_status_codes = self.config.get("retry_status_codes", [429, 500, 502, 503, 504])
        
        last_exception = None
        
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(max_retries + 1),
            wait=wait_exponential(multiplier=backoff_factor),
            retry=retry_if_exception_type((ConnectionError, TimeoutError, RateLimitError)),
        ):
            with attempt:
                try:
                    start_time = time.time()
                    
                    # Make the request
                    response = await self._client.request(
                        method=request_data["method"],
                        url=request_data["url"],
                        headers=request_data["headers"],
                        params=request_data["params"],
                        json=request_data["json"],
                        content=request_data["content"],
                    )
                    
                    response_time = time.time() - start_time
                    
                    # Handle rate limiting
                    if response.status_code == 429:
                        retry_after = handle_rate_limit(dict(response.headers))
                        
                        # Execute rate limit hooks
                        rate_limit_context = HookContext(
                            hook_type=HookType.ON_RATE_LIMIT,
                            request_data=request_data,
                            response_data={"status_code": response.status_code},
                            metadata={"retry_after": retry_after},
                        )
                        await execute_global_hooks(HookType.ON_RATE_LIMIT, rate_limit_context)
                        await self.hook_manager.execute_hooks(HookType.ON_RATE_LIMIT, rate_limit_context)
                        
                        if retry_after:
                            await asyncio.sleep(retry_after)
                        
                        raise RateLimitError(
                            "Rate limit exceeded",
                            retry_after=retry_after,
                            details={"status_code": response.status_code},
                        )
                    
                    # Handle other retry-able status codes
                    if response.status_code in retry_status_codes:
                        error_msg = f"HTTP {response.status_code}: {response.reason_phrase}"
                        if response.status_code >= 500:
                            raise ConnectionError(error_msg)
                        else:
                            raise APIError(
                                error_msg,
                                status_code=response.status_code,
                                response_data=response.json() if response.content else {},
                            )
                    
                    # Prepare response data
                    response_data = {
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "content": response.content,
                    }
                    
                    # Try to parse JSON response
                    if response.content:
                        try:
                            response_data["json"] = response.json()
                        except Exception:
                            # Not JSON, keep as content
                            pass
                    
                    # Execute after_response hooks
                    response_context = HookContext(
                        hook_type=HookType.AFTER_RESPONSE,
                        request_data=request_data,
                        response_data=response_data,
                        metadata={"response_time": response_time},
                    )
                    response_context = await execute_global_hooks(HookType.AFTER_RESPONSE, response_context)
                    response_context = await self.hook_manager.execute_hooks(HookType.AFTER_RESPONSE, response_context)
                    
                    # Check for API errors
                    if not response.is_success:
                        error_data = response_data.get("json", {})
                        error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                        
                        raise APIError(
                            error_message,
                            status_code=response.status_code,
                            response_data=error_data,
                        )
                    
                    return response
                    
                except (httpx.ConnectError, httpx.ConnectTimeout) as e:
                    last_exception = ConnectionError(f"Connection failed: {str(e)}")
                    raise last_exception
                
                except httpx.ReadTimeout as e:
                    last_exception = TimeoutError(f"Read timeout: {str(e)}")
                    raise last_exception
                
                except (RateLimitError, APIError):
                    # Re-raise these as-is
                    raise
                
                except Exception as e:
                    last_exception = APIError(f"Request failed: {str(e)}")
                    
                    # Execute error hooks
                    error_context = HookContext(
                        hook_type=HookType.ON_ERROR,
                        request_data=request_data,
                        error=last_exception,
                    )
                    await execute_global_hooks(HookType.ON_ERROR, error_context)
                    await self.hook_manager.execute_hooks(HookType.ON_ERROR, error_context)
                    
                    raise last_exception
        
        # If we get here, all retries were exhausted
        if last_exception:
            raise last_exception
        else:
            raise APIError("Request failed after all retries")
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a GET request.
        
        Args:
            endpoint: API endpoint (relative to base URL)
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Response JSON data
        """
        url = urljoin(self.api_base_url, endpoint)
        response = await self._execute_request("GET", url, headers, params)
        return response.json() if response.content else {}
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a POST request.
        
        Args:
            endpoint: API endpoint (relative to base URL)
            data: JSON request body
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Response JSON data
        """
        url = urljoin(self.api_base_url, endpoint)
        response = await self._execute_request("POST", url, headers, params, data)
        return response.json() if response.content else {}
    
    async def patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a PATCH request.
        
        Args:
            endpoint: API endpoint (relative to base URL)
            data: JSON request body
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Response JSON data
        """
        url = urljoin(self.api_base_url, endpoint)
        response = await self._execute_request("PATCH", url, headers, params, data)
        return response.json() if response.content else {}
    
    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Make a DELETE request.
        
        Args:
            endpoint: API endpoint (relative to base URL)
            params: Query parameters
            headers: Additional headers
        """
        url = urljoin(self.api_base_url, endpoint)
        await self._execute_request("DELETE", url, headers, params)
    
    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a PUT request.
        
        Args:
            endpoint: API endpoint (relative to base URL)
            data: JSON request body
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Response JSON data
        """
        url = urljoin(self.api_base_url, endpoint)
        response = await self._execute_request("PUT", url, headers, params, data)
        return response.json() if response.content else {}


# Convenience exports
__all__ = [
    "AsyncDataverseClient",
]

