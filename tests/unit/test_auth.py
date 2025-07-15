"""
Unit tests for the authentication module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time

from dataverse_sdk.auth import DataverseAuthenticator, TokenCache
from dataverse_sdk.exceptions import AuthenticationError, ConfigurationError


class TestTokenCache:
    """Test cases for TokenCache class."""
    
    @pytest.mark.asyncio
    async def test_token_cache_set_and_get(self):
        """Test setting and getting tokens from cache."""
        cache = TokenCache()
        cache_key = "test_key"
        token_data = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        
        # Set token
        await cache.set_token(cache_key, token_data)
        
        # Get token
        cached_token = await cache.get_token(cache_key)
        
        assert cached_token is not None
        assert cached_token["access_token"] == "test_token"
        assert "expires_at" in cached_token
    
    @pytest.mark.asyncio
    async def test_token_cache_expiration(self):
        """Test token expiration handling."""
        cache = TokenCache()
        cache_key = "test_key"
        
        # Set expired token
        token_data = {
            "access_token": "expired_token",
            "expires_in": -1,  # Already expired
        }
        
        await cache.set_token(cache_key, token_data)
        
        # Should return None for expired token
        cached_token = await cache.get_token(cache_key)
        assert cached_token is None
    
    @pytest.mark.asyncio
    async def test_token_cache_clear(self):
        """Test clearing token cache."""
        cache = TokenCache()
        cache_key = "test_key"
        token_data = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        
        await cache.set_token(cache_key, token_data)
        await cache.clear()
        
        cached_token = await cache.get_token(cache_key)
        assert cached_token is None


class TestDataverseAuthenticator:
    """Test cases for DataverseAuthenticator class."""
    
    def test_authenticator_initialization(self):
        """Test authenticator initialization."""
        auth = DataverseAuthenticator(
            client_id="test_client_id",
            tenant_id="test_tenant_id",
            dataverse_url="https://test.crm.dynamics.com",
            client_secret="test_secret",
        )
        
        assert auth.client_id == "test_client_id"
        assert auth.tenant_id == "test_tenant_id"
        assert auth.dataverse_url == "https://test.crm.dynamics.com"
        assert auth.client_secret == "test_secret"
        assert auth.authority == "https://login.microsoftonline.com/test_tenant_id"
        assert auth.scope == "https://test.crm.dynamics.com/.default"
    
    def test_authenticator_custom_authority_and_scope(self):
        """Test authenticator with custom authority and scope."""
        auth = DataverseAuthenticator(
            client_id="test_client_id",
            tenant_id="test_tenant_id",
            dataverse_url="https://test.crm.dynamics.com",
            authority="https://custom.authority.com",
            scope="custom.scope",
        )
        
        assert auth.authority == "https://custom.authority.com"
        assert auth.scope == "custom.scope"
    
    @patch('dataverse_sdk.auth.ConfidentialClientApplication')
    @pytest.mark.asyncio
    async def test_client_credentials_authentication_success(self, mock_msal_app):
        """Test successful client credentials authentication."""
        # Mock MSAL application
        mock_app_instance = MagicMock()
        mock_app_instance.acquire_token_for_client.return_value = {
            "access_token": "test_access_token",
            "expires_in": 3600,
        }
        mock_msal_app.return_value = mock_app_instance
        
        auth = DataverseAuthenticator(
            client_id="test_client_id",
            tenant_id="test_tenant_id",
            dataverse_url="https://test.crm.dynamics.com",
            client_secret="test_secret",
        )
        
        token = await auth.authenticate_client_credentials()
        
        assert token == "test_access_token"
        mock_app_instance.acquire_token_for_client.assert_called_once()
    
    @patch('dataverse_sdk.auth.ConfidentialClientApplication')
    @pytest.mark.asyncio
    async def test_client_credentials_authentication_failure(self, mock_msal_app):
        """Test failed client credentials authentication."""
        # Mock MSAL application
        mock_app_instance = MagicMock()
        mock_app_instance.acquire_token_for_client.return_value = {
            "error": "invalid_client",
            "error_description": "Invalid client credentials",
        }
        mock_msal_app.return_value = mock_app_instance
        
        auth = DataverseAuthenticator(
            client_id="test_client_id",
            tenant_id="test_tenant_id",
            dataverse_url="https://test.crm.dynamics.com",
            client_secret="test_secret",
        )
        
        with pytest.raises(AuthenticationError) as exc_info:
            await auth.authenticate_client_credentials()
        
        assert "Invalid client credentials" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_client_credentials_without_secret(self):
        """Test client credentials authentication without secret."""
        auth = DataverseAuthenticator(
            client_id="test_client_id",
            tenant_id="test_tenant_id",
            dataverse_url="https://test.crm.dynamics.com",
            # No client_secret provided
        )
        
        with pytest.raises(ConfigurationError) as exc_info:
            await auth.authenticate_client_credentials()
        
        assert "Client secret is required" in str(exc_info.value)
    
    @patch('dataverse_sdk.auth.PublicClientApplication')
    @pytest.mark.asyncio
    async def test_device_code_authentication_success(self, mock_msal_app):
        """Test successful device code authentication."""
        # Mock MSAL application
        mock_app_instance = MagicMock()
        mock_app_instance.initiate_device_flow.return_value = {
            "user_code": "ABC123",
            "device_code": "device123",
            "verification_uri": "https://microsoft.com/devicelogin",
            "message": "To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code ABC123 to authenticate.",
        }
        mock_app_instance.acquire_token_by_device_flow.return_value = {
            "access_token": "test_access_token",
            "expires_in": 3600,
        }
        mock_msal_app.return_value = mock_app_instance
        
        auth = DataverseAuthenticator(
            client_id="test_client_id",
            tenant_id="test_tenant_id",
            dataverse_url="https://test.crm.dynamics.com",
        )
        
        # Mock print to avoid output during tests
        with patch('builtins.print'):
            token = await auth.authenticate_device_code()
        
        assert token == "test_access_token"
        mock_app_instance.initiate_device_flow.assert_called_once()
        mock_app_instance.acquire_token_by_device_flow.assert_called_once()
    
    @patch('dataverse_sdk.auth.PublicClientApplication')
    @pytest.mark.asyncio
    async def test_device_code_authentication_failure(self, mock_msal_app):
        """Test failed device code authentication."""
        # Mock MSAL application
        mock_app_instance = MagicMock()
        mock_app_instance.initiate_device_flow.return_value = {
            "user_code": "ABC123",
            "device_code": "device123",
            "verification_uri": "https://microsoft.com/devicelogin",
            "message": "To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code ABC123 to authenticate.",
        }
        mock_app_instance.acquire_token_by_device_flow.return_value = {
            "error": "authorization_pending",
            "error_description": "User has not completed authentication",
        }
        mock_msal_app.return_value = mock_app_instance
        
        auth = DataverseAuthenticator(
            client_id="test_client_id",
            tenant_id="test_tenant_id",
            dataverse_url="https://test.crm.dynamics.com",
        )
        
        with patch('builtins.print'):
            with pytest.raises(AuthenticationError) as exc_info:
                await auth.authenticate_device_code()
        
        assert "User has not completed authentication" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_token_with_different_flows(self):
        """Test get_token method with different authentication flows."""
        auth = DataverseAuthenticator(
            client_id="test_client_id",
            tenant_id="test_tenant_id",
            dataverse_url="https://test.crm.dynamics.com",
            client_secret="test_secret",
        )
        
        # Mock authentication methods
        auth.authenticate_client_credentials = AsyncMock(return_value="client_creds_token")
        auth.authenticate_device_code = AsyncMock(return_value="device_code_token")
        auth.authenticate_interactive = AsyncMock(return_value="interactive_token")
        
        # Test client credentials flow
        token = await auth.get_token("client_credentials")
        assert token == "client_creds_token"
        auth.authenticate_client_credentials.assert_called_once()
        
        # Test device code flow
        token = await auth.get_token("device_code")
        assert token == "device_code_token"
        auth.authenticate_device_code.assert_called_once()
        
        # Test interactive flow
        token = await auth.get_token("interactive")
        assert token == "interactive_token"
        auth.authenticate_interactive.assert_called_once()
        
        # Test unsupported flow
        with pytest.raises(ConfigurationError) as exc_info:
            await auth.get_token("unsupported_flow")
        
        assert "Unsupported authentication flow" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_token_caching(self):
        """Test token caching functionality."""
        auth = DataverseAuthenticator(
            client_id="test_client_id",
            tenant_id="test_tenant_id",
            dataverse_url="https://test.crm.dynamics.com",
            client_secret="test_secret",
        )
        
        # Mock MSAL to return token
        with patch('dataverse_sdk.auth.ConfidentialClientApplication') as mock_msal_app:
            mock_app_instance = MagicMock()
            mock_app_instance.acquire_token_for_client.return_value = {
                "access_token": "cached_token",
                "expires_in": 3600,
            }
            mock_msal_app.return_value = mock_app_instance
            
            # First call should hit MSAL
            token1 = await auth.authenticate_client_credentials()
            assert token1 == "cached_token"
            assert mock_app_instance.acquire_token_for_client.call_count == 1
            
            # Second call should use cache
            token2 = await auth.authenticate_client_credentials()
            assert token2 == "cached_token"
            assert mock_app_instance.acquire_token_for_client.call_count == 1  # No additional calls
    
    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """Test clearing authentication cache."""
        auth = DataverseAuthenticator(
            client_id="test_client_id",
            tenant_id="test_tenant_id",
            dataverse_url="https://test.crm.dynamics.com",
            client_secret="test_secret",
        )
        
        # Mock token cache
        auth._token_cache.clear = AsyncMock()
        
        await auth.clear_cache()
        
        auth._token_cache.clear.assert_called_once()
    
    def test_cache_key_generation(self):
        """Test cache key generation for different scenarios."""
        auth = DataverseAuthenticator(
            client_id="test_client_id",
            tenant_id="test_tenant_id",
            dataverse_url="https://test.crm.dynamics.com",
            client_secret="test_secret",
        )
        
        # Test basic cache key
        key1 = auth._get_cache_key("client_credentials")
        assert "test_client_id" in key1
        assert "test_tenant_id" in key1
        assert "client_credentials" in key1
        
        # Test cache key with additional parameters
        key2 = auth._get_cache_key("interactive", redirect_uri="http://localhost:8080")
        assert "redirect_uri:http://localhost:8080" in key2
        
        # Keys should be different for different parameters
        assert key1 != key2

