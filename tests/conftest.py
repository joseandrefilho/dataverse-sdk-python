"""
Pytest configuration and fixtures for Dataverse SDK tests.
"""

import asyncio
import os
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import httpx

from dataverse_sdk import DataverseSDK
from dataverse_sdk.auth import DataverseAuthenticator
from dataverse_sdk.client import AsyncDataverseClient
from dataverse_sdk.utils import Config


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config() -> Config:
    """Create a mock configuration for testing."""
    return Config(
        max_connections=10,
        max_retries=2,
        default_batch_size=5,
        debug=True,
    )


@pytest.fixture
def mock_auth_config() -> Dict[str, str]:
    """Create mock authentication configuration."""
    return {
        "dataverse_url": "https://test.crm.dynamics.com",
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "tenant_id": "test-tenant-id",
    }


@pytest.fixture
def mock_authenticator(mock_auth_config) -> DataverseAuthenticator:
    """Create a mock authenticator."""
    auth = DataverseAuthenticator(**mock_auth_config)
    auth.get_token = AsyncMock(return_value="mock-access-token")
    return auth


@pytest.fixture
async def mock_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create a mock HTTP client."""
    async with httpx.AsyncClient() as client:
        yield client


@pytest.fixture
async def mock_dataverse_client(
    mock_authenticator, mock_config, mock_http_client
) -> AsyncGenerator[AsyncDataverseClient, None]:
    """Create a mock Dataverse client."""
    client = AsyncDataverseClient(
        dataverse_url="https://test.crm.dynamics.com",
        authenticator=mock_authenticator,
        config=mock_config,
    )
    
    # Mock the HTTP client
    client._client = mock_http_client
    
    yield client
    
    await client.close()


@pytest.fixture
async def mock_sdk(mock_auth_config, mock_config) -> AsyncGenerator[DataverseSDK, None]:
    """Create a mock SDK instance."""
    sdk = DataverseSDK(
        **mock_auth_config,
        config=mock_config,
    )
    
    # Mock the authenticator
    sdk.authenticator.get_token = AsyncMock(return_value="mock-access-token")
    
    yield sdk
    
    await sdk.client.close()


@pytest.fixture
def sample_entity_data() -> Dict[str, Any]:
    """Sample entity data for testing."""
    return {
        "name": "Test Account",
        "websiteurl": "https://test.com",
        "telephone1": "555-0123",
        "emailaddress1": "test@test.com",
    }


@pytest.fixture
def sample_query_response() -> Dict[str, Any]:
    """Sample query response for testing."""
    return {
        "@odata.context": "https://test.crm.dynamics.com/api/data/v9.2/$metadata#accounts",
        "@odata.count": 2,
        "value": [
            {
                "accountid": "12345678-1234-1234-1234-123456789012",
                "name": "Test Account 1",
                "websiteurl": "https://test1.com",
            },
            {
                "accountid": "87654321-4321-4321-4321-210987654321",
                "name": "Test Account 2", 
                "websiteurl": "https://test2.com",
            },
        ],
        "@odata.nextLink": "https://test.crm.dynamics.com/api/data/v9.2/accounts?$skip=2",
    }


@pytest.fixture
def sample_batch_response() -> str:
    """Sample batch response for testing."""
    return """--batchresponse_12345
Content-Type: application/http
Content-Transfer-Encoding: binary

HTTP/1.1 201 Created
Content-Type: application/json; odata.metadata=minimal
OData-Version: 4.0

{
  "@odata.context": "https://test.crm.dynamics.com/api/data/v9.2/$metadata#accounts/$entity",
  "accountid": "12345678-1234-1234-1234-123456789012",
  "name": "Test Account"
}

--batchresponse_12345
Content-Type: application/http
Content-Transfer-Encoding: binary

HTTP/1.1 400 Bad Request
Content-Type: application/json; odata.metadata=minimal
OData-Version: 4.0

{
  "error": {
    "code": "0x80040203",
    "message": "Invalid data"
  }
}

--batchresponse_12345--"""


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx response."""
    def _create_response(
        status_code: int = 200,
        json_data: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        content: str = "",
    ) -> MagicMock:
        response = MagicMock(spec=httpx.Response)
        response.status_code = status_code
        response.is_success = status_code < 400
        response.headers = headers or {}
        response.content = content.encode() if content else b""
        response.text = content
        response.json.return_value = json_data or {}
        response.reason_phrase = "OK" if status_code == 200 else "Error"
        return response
    
    return _create_response


# Environment setup for tests
@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment variables."""
    test_env = {
        "DATAVERSE_URL": "https://test.crm.dynamics.com",
        "AZURE_CLIENT_ID": "test-client-id",
        "AZURE_CLIENT_SECRET": "test-client-secret",
        "AZURE_TENANT_ID": "test-tenant-id",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG",
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)


# Async test helpers
def async_test(coro):
    """Decorator to run async tests."""
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper


# Mock data generators
class MockDataGenerator:
    """Generate mock data for testing."""
    
    @staticmethod
    def create_entity(entity_type: str = "account", **kwargs) -> Dict[str, Any]:
        """Create mock entity data."""
        base_data = {
            "accountid": "12345678-1234-1234-1234-123456789012",
            "name": "Test Account",
            "createdon": "2023-01-01T00:00:00Z",
            "modifiedon": "2023-01-01T00:00:00Z",
        }
        base_data.update(kwargs)
        return base_data
    
    @staticmethod
    def create_query_result(entities: list = None, count: int = None) -> Dict[str, Any]:
        """Create mock query result."""
        entities = entities or [MockDataGenerator.create_entity()]
        return {
            "@odata.context": "https://test.crm.dynamics.com/api/data/v9.2/$metadata#accounts",
            "@odata.count": count or len(entities),
            "value": entities,
        }


@pytest.fixture
def mock_data_generator() -> MockDataGenerator:
    """Provide mock data generator."""
    return MockDataGenerator()

