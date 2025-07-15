"""
Authentication module for Microsoft Dataverse SDK.

This module provides authentication capabilities using MSAL (Microsoft Authentication Library)
with support for various authentication flows and token management.
"""

import asyncio
import time
from typing import Dict, Optional, Any
from urllib.parse import urlparse

import msal
import structlog
from msal import ConfidentialClientApplication, PublicClientApplication

from ..exceptions import AuthenticationError, ConfigurationError


logger = structlog.get_logger(__name__)


class TokenCache:
    """Thread-safe token cache for storing and retrieving access tokens."""
    
    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get_token(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get a cached token if it's still valid."""
        async with self._lock:
            token_data = self._cache.get(cache_key)
            if not token_data:
                return None
            
            # Check if token is expired (with 5 minute buffer)
            expires_at = token_data.get("expires_at", 0)
            if time.time() + 300 >= expires_at:
                logger.debug("Token expired, removing from cache", cache_key=cache_key)
                del self._cache[cache_key]
                return None
            
            return token_data
    
    async def set_token(self, cache_key: str, token_data: Dict[str, Any]) -> None:
        """Cache a token with expiration time."""
        async with self._lock:
            # Calculate expiration time
            expires_in = token_data.get("expires_in", 3600)
            token_data["expires_at"] = time.time() + expires_in
            self._cache[cache_key] = token_data
            logger.debug("Token cached", cache_key=cache_key, expires_in=expires_in)
    
    async def clear(self) -> None:
        """Clear all cached tokens."""
        async with self._lock:
            self._cache.clear()
            logger.debug("Token cache cleared")


class DataverseAuthenticator:
    """
    Handles authentication to Microsoft Dataverse using various flows.
    
    Supports:
    - Client credentials flow (service-to-service)
    - Authorization code flow (interactive)
    - Device code flow (for CLI applications)
    """
    
    def __init__(
        self,
        client_id: str,
        tenant_id: str,
        dataverse_url: str,
        client_secret: Optional[str] = None,
        authority: Optional[str] = None,
        scope: Optional[str] = None,
        verify_ssl: bool = True,
        disable_ssl_warnings: bool = False,
        ssl_ca_bundle: Optional[str] = None,
        ssl_cert_file: Optional[str] = None,
        ssl_key_file: Optional[str] = None,
        proxy_url: Optional[str] = None,
        proxy_username: Optional[str] = None,
        proxy_password: Optional[str] = None,
    ) -> None:
        """
        Initialize the authenticator.
        
        Args:
            client_id: Azure AD application client ID
            tenant_id: Azure AD tenant ID
            dataverse_url: Dataverse environment URL
            client_secret: Client secret (for confidential client apps)
            authority: Authority URL (defaults to login.microsoftonline.com)
            scope: OAuth scope (defaults to dataverse_url/.default)
            verify_ssl: Whether to verify SSL certificates
            disable_ssl_warnings: Whether to disable SSL warnings
            ssl_ca_bundle: Path to CA bundle file
            ssl_cert_file: Path to client certificate file
            ssl_key_file: Path to client private key file
            proxy_url: Proxy URL
            proxy_username: Proxy username
            proxy_password: Proxy password
        """
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.dataverse_url = dataverse_url.rstrip("/")
        self.client_secret = client_secret
        
        # SSL and proxy configurations
        self.verify_ssl = verify_ssl
        self.disable_ssl_warnings = disable_ssl_warnings
        self.ssl_ca_bundle = ssl_ca_bundle
        self.ssl_cert_file = ssl_cert_file
        self.ssl_key_file = ssl_key_file
        self.proxy_url = proxy_url
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        
        # Disable SSL warnings if requested
        if disable_ssl_warnings and not verify_ssl:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Set default authority if not provided
        if authority is None:
            authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.authority = authority
        
        # Set default scope if not provided
        if scope is None:
            parsed_url = urlparse(self.dataverse_url)
            scope = f"{parsed_url.scheme}://{parsed_url.netloc}/.default"
        self.scope = scope
        
        # Initialize MSAL application
        self._app: Optional[ConfidentialClientApplication | PublicClientApplication] = None
        self._token_cache = TokenCache()
        
        logger.info(
            "Dataverse authenticator initialized",
            client_id=client_id,
            tenant_id=tenant_id,
            dataverse_url=dataverse_url,
            authority=authority,
            scope=scope,
        )
    
    def _get_msal_app(self) -> ConfidentialClientApplication | PublicClientApplication:
        """Get or create MSAL application instance."""
        if self._app is None:
            # Configurar SSL e proxy ANTES de criar o app MSAL
            self._configure_ssl_and_proxy_environment()
            
            if self.client_secret:
                # Confidential client (with secret)
                self._app = ConfidentialClientApplication(
                    client_id=self.client_id,
                    client_credential=self.client_secret,
                    authority=self.authority,
                )
                logger.debug("Created confidential client application with SSL/proxy config")
            else:
                # Public client (no secret)
                self._app = PublicClientApplication(
                    client_id=self.client_id,
                    authority=self.authority,
                )
                logger.debug("Created public client application with SSL/proxy config")
        
        return self._app
    
    def _configure_ssl_and_proxy_environment(self) -> None:
        """Configure SSL and proxy environment variables before MSAL initialization."""
        import os
        
        # Configurar proxy se fornecido
        if self.proxy_url:
            proxy_url = self.proxy_url
            
            # Adicionar autenticação se fornecida
            if self.proxy_username and self.proxy_password:
                from urllib.parse import urlparse, urlunparse
                parsed = urlparse(self.proxy_url)
                proxy_url = urlunparse((
                    parsed.scheme,
                    f"{self.proxy_username}:{self.proxy_password}@{parsed.netloc}",
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ))
            
            # Configurar variáveis de ambiente de proxy
            os.environ['HTTP_PROXY'] = proxy_url
            os.environ['HTTPS_PROXY'] = proxy_url
            os.environ['http_proxy'] = proxy_url
            os.environ['https_proxy'] = proxy_url
            
            logger.debug("Proxy environment configured", proxy_url=self.proxy_url)
        
        # Configurar SSL se desabilitado
        if not self.verify_ssl:
            # Configurar variáveis de ambiente para desabilitar SSL
            os.environ['PYTHONHTTPSVERIFY'] = '0'
            os.environ['CURL_CA_BUNDLE'] = ''
            os.environ['REQUESTS_CA_BUNDLE'] = ''
            
            # Desabilitar warnings SSL se solicitado
            if self.disable_ssl_warnings:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                import warnings
                warnings.filterwarnings('ignore', message='Unverified HTTPS request')
            
            logger.debug("SSL verification disabled via environment variables")
    
    async def get_access_token(self) -> str:
        """
        Get access token using the configured authentication method.
        This method mimics the working implementation shown by the user.
        
        Returns:
            Access token string
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Configurar ambiente antes de obter token
            self._configure_ssl_and_proxy_environment()
            
            # Obter token usando client credentials
            app = self._get_msal_app()
            
            # Tentar obter token do cache primeiro
            cache_key = self._get_cache_key("client_credentials")
            cached_token = await self._token_cache.get_token(cache_key)
            if cached_token:
                logger.debug("Using cached access token")
                return cached_token["access_token"]
            
            # Obter novo token
            result = app.acquire_token_for_client(scopes=[self.scope])
            
            if "access_token" not in result:
                error_msg = result.get("error_description", "Unknown authentication error")
                logger.error("Failed to get access token", error=error_msg)
                raise AuthenticationError(f"Authentication failed: {error_msg}")
            
            # Cache do token
            await self._token_cache.set_token(cache_key, result)
            
            logger.info("Access token obtained successfully")
            return result["access_token"]
            
        except Exception as e:
            logger.error("Failed to get access token", error=str(e))
            raise AuthenticationError(f"Authentication error: {str(e)}") from e
    
    def _get_cache_key(self, flow_type: str, **kwargs: Any) -> str:
        """Generate cache key for token storage."""
        key_parts = [
            self.client_id,
            self.tenant_id,
            flow_type,
        ]
        
        # Add additional parameters for cache key uniqueness
        for key, value in sorted(kwargs.items()):
            if value is not None:
                key_parts.append(f"{key}:{value}")
        
        return ":".join(key_parts)
    
    async def authenticate_client_credentials(self) -> str:
        """
        Authenticate using client credentials flow (service-to-service).
        
        Returns:
            Access token string
            
        Raises:
            AuthenticationError: If authentication fails
            ConfigurationError: If client secret is not provided
        """
        if not self.client_secret:
            raise ConfigurationError(
                "Client secret is required for client credentials flow"
            )
        
        cache_key = self._get_cache_key("client_credentials")
        
        # Check cache first
        cached_token = await self._token_cache.get_token(cache_key)
        if cached_token:
            logger.debug("Using cached token for client credentials")
            return cached_token["access_token"]
        
        # Acquire new token
        app = self._get_msal_app()
        
        try:
            result = app.acquire_token_for_client(scopes=[self.scope])
            
            if "access_token" not in result:
                error_msg = result.get("error_description", "Unknown authentication error")
                logger.error("Client credentials authentication failed", error=error_msg)
                raise AuthenticationError(f"Authentication failed: {error_msg}")
            
            # Cache the token
            await self._token_cache.set_token(cache_key, result)
            
            logger.info("Client credentials authentication successful")
            return result["access_token"]
            
        except Exception as e:
            logger.error("Client credentials authentication error", error=str(e))
            raise AuthenticationError(f"Authentication error: {str(e)}") from e
    
    async def authenticate_device_code(self) -> str:
        """
        Authenticate using device code flow (for CLI applications).
        
        Returns:
            Access token string
            
        Raises:
            AuthenticationError: If authentication fails
        """
        cache_key = self._get_cache_key("device_code")
        
        # Check cache first
        cached_token = await self._token_cache.get_token(cache_key)
        if cached_token:
            logger.debug("Using cached token for device code")
            return cached_token["access_token"]
        
        app = self._get_msal_app()
        
        try:
            # Initiate device flow
            flow = app.initiate_device_flow(scopes=[self.scope])
            
            if "user_code" not in flow:
                raise AuthenticationError("Failed to initiate device flow")
            
            # Display user instructions
            print(flow["message"])
            
            # Poll for completion
            result = app.acquire_token_by_device_flow(flow)
            
            if "access_token" not in result:
                error_msg = result.get("error_description", "Unknown authentication error")
                logger.error("Device code authentication failed", error=error_msg)
                raise AuthenticationError(f"Authentication failed: {error_msg}")
            
            # Cache the token
            await self._token_cache.set_token(cache_key, result)
            
            logger.info("Device code authentication successful")
            return result["access_token"]
            
        except Exception as e:
            logger.error("Device code authentication error", error=str(e))
            raise AuthenticationError(f"Authentication error: {str(e)}") from e
    
    async def authenticate_interactive(
        self,
        redirect_uri: str = "http://localhost:8080",
        port: int = 8080,
    ) -> str:
        """
        Authenticate using authorization code flow (interactive).
        
        Args:
            redirect_uri: Redirect URI for OAuth flow
            port: Local port for redirect server
            
        Returns:
            Access token string
            
        Raises:
            AuthenticationError: If authentication fails
        """
        cache_key = self._get_cache_key("interactive", redirect_uri=redirect_uri)
        
        # Check cache first
        cached_token = await self._token_cache.get_token(cache_key)
        if cached_token:
            logger.debug("Using cached token for interactive")
            return cached_token["access_token"]
        
        app = self._get_msal_app()
        
        try:
            # Get authorization URL
            auth_url = app.get_authorization_request_url(
                scopes=[self.scope],
                redirect_uri=redirect_uri,
            )
            
            print(f"Please visit this URL to authenticate: {auth_url}")
            
            # Start local server to receive callback
            # Note: In a real implementation, you'd implement a proper callback server
            # For now, we'll use device code flow as fallback
            logger.warning("Interactive flow not fully implemented, falling back to device code")
            return await self.authenticate_device_code()
            
        except Exception as e:
            logger.error("Interactive authentication error", error=str(e))
            raise AuthenticationError(f"Authentication error: {str(e)}") from e
    
    async def get_token(self, flow: str = "client_credentials", **kwargs: Any) -> str:
        """
        Get an access token using the specified authentication flow.
        
        Args:
            flow: Authentication flow ("client_credentials", "device_code", "interactive")
            **kwargs: Additional arguments for specific flows
            
        Returns:
            Access token string
            
        Raises:
            AuthenticationError: If authentication fails
            ConfigurationError: If flow is not supported or configured incorrectly
        """
        if flow == "client_credentials":
            return await self.get_access_token()
        elif flow == "device_code":
            return await self.authenticate_device_code()
        elif flow == "interactive":
            return await self.authenticate_interactive(**kwargs)
        else:
            raise ConfigurationError(f"Unsupported authentication flow: {flow}")
    
    async def clear_cache(self) -> None:
        """Clear all cached tokens."""
        await self._token_cache.clear()
        logger.info("Authentication cache cleared")


# Convenience exports
__all__ = [
    "DataverseAuthenticator",
    "TokenCache",
]

