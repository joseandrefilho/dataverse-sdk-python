"""
Unit tests for the async client module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from dataverse_sdk.client import AsyncDataverseClient
from dataverse_sdk.auth import DataverseAuthenticator
from dataverse_sdk.exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    RateLimitError,
    TimeoutError,
)
from dataverse_sdk.utils import Config


class TestAsyncDataverseClient:
    """Test cases for AsyncDataverseClient class."""
    
    @pytest.fixture
    def mock_authenticator(self):
        """Create a mock authenticator."""
        auth = MagicMock(spec=DataverseAuthenticator)
        auth.get_token = AsyncMock(return_value="mock-token")
        return auth
    
    @pytest.fixture
    def client_config(self):
        """Create test configuration."""
        return Config(
            connect_timeout=5.0,
            read_timeout=10.0,
            max_connections=10,
            max_retries=2,
        )
    
    @pytest.fixture
    def client(self, mock_authenticator, client_config):
        """Create test client instance."""
        return AsyncDataverseClient(
            dataverse_url="https://test.crm.dynamics.com",
            authenticator=mock_authenticator,
            config=client_config,
        )
    
    def test_client_initialization(self, client, mock_authenticator, client_config):
        """Test client initialization."""
        assert client.dataverse_url == "https://test.crm.dynamics.com"
        assert client.authenticator == mock_authenticator
        assert client.config == client_config
        assert client.api_base_url == "https://test.crm.dynamics.com/api/data/v9.2/"
    
    @pytest.mark.asyncio
    async def test_context_manager(self, client):
        """Test async context manager functionality."""
        async with client as c:
            assert c == client
            assert not client.is_closed()
        
        # Client should be closed after exiting context
        assert client.is_closed()
    
    @pytest.mark.asyncio
    async def test_ensure_client_initialization(self, client):
        """Test HTTP client initialization."""
        await client._ensure_client()
        
        assert client._client is not None
        assert isinstance(client._client, httpx.AsyncClient)
        assert not client.is_closed()
    
    @pytest.mark.asyncio
    async def test_get_auth_headers(self, client, mock_authenticator):
        """Test authentication header generation."""
        headers = await client._get_auth_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer mock-token"
        mock_authenticator.get_token.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_auth_headers_failure(self, client, mock_authenticator):
        """Test authentication header generation failure."""
        mock_authenticator.get_token.side_effect = Exception("Auth failed")
        
        with pytest.raises(AuthenticationError) as exc_info:
            await client._get_auth_headers()
        
        assert "Authentication failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_successful_get_request(self, client, mock_httpx_response):
        """Test successful GET request."""
        # Mock response
        response_data = {"value": [{"id": "123", "name": "Test"}]}
        mock_response = mock_httpx_response(200, response_data)
        
        with patch.object(client, '_client') as mock_http_client:
            mock_http_client.request = AsyncMock(return_value=mock_response)
            await client._ensure_client()
            
            result = await client.get("accounts")
            
            assert result == response_data
            mock_http_client.request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_successful_post_request(self, client, mock_httpx_response):
        """Test successful POST request."""
        # Mock response
        response_data = {"id": "123", "name": "Test Account"}
        mock_response = mock_httpx_response(201, response_data)
        
        with patch.object(client, '_client') as mock_http_client:
            mock_http_client.request = AsyncMock(return_value=mock_response)
            await client._ensure_client()
            
            data = {"name": "Test Account"}
            result = await client.post("accounts", data)
            
            assert result == response_data
            mock_http_client.request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, client, mock_httpx_response):
        """Test rate limit handling with retry."""
        # First response: rate limited
        rate_limit_response = mock_httpx_response(
            429,
            {"error": {"message": "Rate limit exceeded"}},
            headers={"Retry-After": "1"}
        )
        
        # Second response: success
        success_response = mock_httpx_response(200, {"value": []})
        
        with patch.object(client, '_client') as mock_http_client:
            mock_http_client.request = AsyncMock(side_effect=[rate_limit_response, success_response])
            await client._ensure_client()
            
            with patch('asyncio.sleep') as mock_sleep:
                result = await client.get("accounts")
                
                assert result == {"value": []}
                assert mock_http_client.request.call_count == 2
                mock_sleep.assert_called_once_with(1)
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, client, mock_httpx_response):
        """Test API error handling."""
        # Mock error response
        error_response = mock_httpx_response(
            400,
            {"error": {"message": "Bad request", "code": "0x80040203"}}
        )
        
        with patch.object(client, '_client') as mock_http_client:
            mock_http_client.request = AsyncMock(return_value=error_response)
            await client._ensure_client()
            
            with pytest.raises(APIError) as exc_info:
                await client.get("accounts")
            
            assert exc_info.value.status_code == 400
            assert "Bad request" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, client):
        """Test connection error handling."""
        with patch.object(client, '_client') as mock_http_client:
            mock_http_client.request = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
            await client._ensure_client()
            
            with pytest.raises(ConnectionError) as exc_info:
                await client.get("accounts")
            
            assert "Connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, client):
        """Test timeout error handling."""
        with patch.object(client, '_client') as mock_http_client:
            mock_http_client.request = AsyncMock(side_effect=httpx.ReadTimeout("Read timeout"))
            await client._ensure_client()
            
            with pytest.raises(TimeoutError) as exc_info:
                await client.get("accounts")
            
            assert "Read timeout" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_retry_logic(self, client, mock_httpx_response):
        """Test retry logic for transient errors."""
        # First two responses: server errors
        error_response = mock_httpx_response(500, {"error": {"message": "Internal server error"}})
        
        # Third response: success
        success_response = mock_httpx_response(200, {"value": []})
        
        with patch.object(client, '_client') as mock_http_client:
            mock_http_client.request = AsyncMock(side_effect=[error_response, error_response, success_response])
            await client._ensure_client()
            
            result = await client.get("accounts")
            
            assert result == {"value": []}
            assert mock_http_client.request.call_count == 3
    
    @pytest.mark.asyncio
    async def test_patch_request(self, client, mock_httpx_response):
        """Test PATCH request."""
        response_data = {"id": "123", "name": "Updated Account"}
        mock_response = mock_httpx_response(200, response_data)
        
        with patch.object(client, '_client') as mock_http_client:
            mock_http_client.request = AsyncMock(return_value=mock_response)
            await client._ensure_client()
            
            data = {"name": "Updated Account"}
            result = await client.patch("accounts(123)", data)
            
            assert result == response_data
    
    @pytest.mark.asyncio
    async def test_delete_request(self, client, mock_httpx_response):
        """Test DELETE request."""
        mock_response = mock_httpx_response(204)  # No content
        
        with patch.object(client, '_client') as mock_http_client:
            mock_http_client.request = AsyncMock(return_value=mock_response)
            await client._ensure_client()
            
            await client.delete("accounts(123)")
            
            mock_http_client.request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_put_request(self, client, mock_httpx_response):
        """Test PUT request."""
        response_data = {"id": "123", "name": "Replaced Account"}
        mock_response = mock_httpx_response(200, response_data)
        
        with patch.object(client, '_client') as mock_http_client:
            mock_http_client.request = AsyncMock(return_value=mock_response)
            await client._ensure_client()
            
            data = {"name": "Replaced Account"}
            result = await client.put("accounts(123)", data)
            
            assert result == response_data
    
    @pytest.mark.asyncio
    async def test_request_with_params(self, client, mock_httpx_response):
        """Test request with query parameters."""
        response_data = {"value": []}
        mock_response = mock_httpx_response(200, response_data)
        
        with patch.object(client, '_client') as mock_http_client:
            mock_http_client.request = AsyncMock(return_value=mock_response)
            await client._ensure_client()
            
            params = {"$select": "name,websiteurl", "$top": "10"}
            await client.get("accounts", params=params)
            
            # Verify params were passed
            call_args = mock_http_client.request.call_args
            assert call_args[1]["params"] == params
    
    @pytest.mark.asyncio
    async def test_request_with_headers(self, client, mock_httpx_response):
        """Test request with custom headers."""
        response_data = {"value": []}
        mock_response = mock_httpx_response(200, response_data)
        
        with patch.object(client, '_client') as mock_http_client:
            mock_http_client.request = AsyncMock(return_value=mock_response)
            await client._ensure_client()
            
            headers = {"Prefer": "return=representation"}
            await client.get("accounts", headers=headers)
            
            # Verify headers were merged with auth headers
            call_args = mock_http_client.request.call_args
            request_headers = call_args[1]["headers"]
            assert "Prefer" in request_headers
            assert "Authorization" in request_headers
    
    @pytest.mark.asyncio
    async def test_close_client(self, client):
        """Test client cleanup."""
        await client._ensure_client()
        assert not client.is_closed()
        
        await client.close()
        assert client.is_closed()
    
    @pytest.mark.asyncio
    async def test_hook_integration(self, client):
        """Test hook system integration."""
        # This would test that hooks are called during requests
        # For now, we'll just verify the hook manager exists
        assert client.hook_manager is not None
    
    @pytest.mark.asyncio
    async def test_empty_response_handling(self, client, mock_httpx_response):
        """Test handling of empty responses."""
        mock_response = mock_httpx_response(204)  # No content
        mock_response.content = b""
        
        with patch.object(client, '_client') as mock_http_client:
            mock_http_client.request = AsyncMock(return_value=mock_response)
            await client._ensure_client()
            
            result = await client.get("accounts")
            
            assert result == {}  # Should return empty dict for no content

