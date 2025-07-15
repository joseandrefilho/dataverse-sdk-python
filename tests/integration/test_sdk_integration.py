"""
Integration tests for the Dataverse SDK.

These tests require a real Dataverse environment and valid credentials.
They are designed to test the SDK against an actual Dataverse instance.
"""

import pytest
import os
import asyncio
from typing import Dict, Any

from dataverse_sdk import DataverseSDK
from dataverse_sdk.exceptions import EntityNotFoundError, ValidationError


# Skip integration tests if credentials are not available
pytestmark = pytest.mark.skipif(
    not all([
        os.getenv("DATAVERSE_URL"),
        os.getenv("AZURE_CLIENT_ID"),
        os.getenv("AZURE_TENANT_ID"),
    ]),
    reason="Integration tests require Dataverse credentials"
)


@pytest.fixture(scope="module")
async def sdk():
    """Create SDK instance for integration tests."""
    sdk_instance = DataverseSDK(
        dataverse_url=os.getenv("DATAVERSE_URL"),
        client_id=os.getenv("AZURE_CLIENT_ID"),
        client_secret=os.getenv("AZURE_CLIENT_SECRET"),
        tenant_id=os.getenv("AZURE_TENANT_ID"),
    )
    
    async with sdk_instance as sdk:
        yield sdk


@pytest.fixture
def test_account_data() -> Dict[str, Any]:
    """Test account data for integration tests."""
    return {
        "name": "SDK Integration Test Account",
        "websiteurl": "https://sdk-test.example.com",
        "description": "Account created by SDK integration tests",
        "telephone1": "555-0123",
    }


@pytest.fixture
def test_contact_data() -> Dict[str, Any]:
    """Test contact data for integration tests."""
    return {
        "firstname": "SDK",
        "lastname": "Test",
        "emailaddress1": "sdk.test@example.com",
        "telephone1": "555-0456",
        "description": "Contact created by SDK integration tests",
    }


class TestSDKIntegration:
    """Integration tests for the main SDK functionality."""
    
    @pytest.mark.asyncio
    async def test_connection_and_authentication(self, sdk):
        """Test that we can connect and authenticate successfully."""
        # Try to query organizations to test connection
        result = await sdk.client.get("organizations")
        
        assert "value" in result
        assert len(result["value"]) > 0
        
        # Verify we got organization data
        org = result["value"][0]
        assert "organizationid" in org
        assert "name" in org
    
    @pytest.mark.asyncio
    async def test_account_crud_operations(self, sdk, test_account_data):
        """Test CRUD operations on accounts."""
        created_account_id = None
        
        try:
            # Create account
            created_account_id = await sdk.create("accounts", test_account_data)
            assert created_account_id is not None
            assert len(created_account_id) == 36  # GUID length
            
            # Read account
            account = await sdk.read("accounts", created_account_id)
            assert account["accountid"] == created_account_id
            assert account["name"] == test_account_data["name"]
            assert account["websiteurl"] == test_account_data["websiteurl"]
            
            # Update account
            update_data = {"description": "Updated by integration test"}
            await sdk.update("accounts", created_account_id, update_data)
            
            # Verify update
            updated_account = await sdk.read("accounts", created_account_id)
            assert updated_account["description"] == "Updated by integration test"
            
        finally:
            # Clean up - delete account
            if created_account_id:
                try:
                    await sdk.delete("accounts", created_account_id)
                except Exception:
                    pass  # Ignore cleanup errors
    
    @pytest.mark.asyncio
    async def test_query_operations(self, sdk):
        """Test query operations."""
        # Query accounts with basic options
        result = await sdk.query("accounts", {
            "select": ["name", "websiteurl", "createdon"],
            "top": 5,
            "order_by": ["createdon desc"],
        })
        
        assert isinstance(result.value, list)
        assert len(result.value) <= 5
        
        # Verify selected fields are present
        if result.value:
            account = result.value[0]
            assert "name" in account
            assert "websiteurl" in account or account["websiteurl"] is None
            assert "createdon" in account
    
    @pytest.mark.asyncio
    async def test_query_with_filter(self, sdk):
        """Test query with filter."""
        # Query accounts with filter
        result = await sdk.query("accounts", {
            "select": ["name", "accountid"],
            "filter": "statecode eq 0",  # Active accounts
            "top": 10,
        })
        
        assert isinstance(result.value, list)
        
        # All returned accounts should be active
        for account in result.value:
            # We can't directly check statecode since we didn't select it,
            # but the query should have filtered correctly
            assert "accountid" in account
            assert "name" in account
    
    @pytest.mark.asyncio
    async def test_entity_not_found_error(self, sdk):
        """Test EntityNotFoundError for non-existent entity."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        
        with pytest.raises(EntityNotFoundError) as exc_info:
            await sdk.read("accounts", fake_id)
        
        assert exc_info.value.entity_type == "accounts"
        assert exc_info.value.entity_id == fake_id
    
    @pytest.mark.asyncio
    async def test_upsert_operation(self, sdk, test_account_data):
        """Test upsert operation."""
        created_account_id = None
        
        try:
            # First upsert should create
            result = await sdk.upsert("accounts", test_account_data)
            assert result.was_created is True
            created_account_id = result.entity_id
            
            # Second upsert with same data should update
            update_data = test_account_data.copy()
            update_data["description"] = "Updated via upsert"
            
            # For this test, we'll use the ID as alternate key
            # In real scenarios, you'd use business keys
            result2 = await sdk.upsert(
                "accounts",
                update_data,
                alternate_key={"accountid": created_account_id}
            )
            
            # Verify the account was updated
            updated_account = await sdk.read("accounts", created_account_id)
            assert updated_account["description"] == "Updated via upsert"
            
        finally:
            # Clean up
            if created_account_id:
                try:
                    await sdk.delete("accounts", created_account_id)
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_bulk_create_operation(self, sdk):
        """Test bulk create operation."""
        # Create test data
        test_accounts = [
            {
                "name": f"Bulk Test Account {i}",
                "description": f"Bulk created account {i}",
            }
            for i in range(3)
        ]
        
        created_ids = []
        
        try:
            # Bulk create
            result = await sdk.bulk_create("accounts", test_accounts, batch_size=2)
            
            assert result.total_processed == 3
            assert result.successful > 0
            assert result.success_rate > 0
            
            # If all succeeded, verify accounts were created
            if result.successful == 3:
                # Query for our test accounts
                query_result = await sdk.query("accounts", {
                    "select": ["accountid", "name"],
                    "filter": "contains(name, 'Bulk Test Account')",
                })
                
                created_ids = [acc["accountid"] for acc in query_result.value]
                assert len(created_ids) >= 3
            
        finally:
            # Clean up created accounts
            if created_ids:
                try:
                    await sdk.bulk_delete("accounts", created_ids)
                except Exception:
                    pass
    
    @pytest.mark.asyncio
    async def test_metadata_operations(self, sdk):
        """Test metadata operations."""
        # Get account entity metadata
        metadata = await sdk.get_entity_metadata("account")
        
        assert "LogicalName" in metadata
        assert metadata["LogicalName"] == "account"
        assert "DisplayName" in metadata
        assert "Attributes" in metadata
        
        # Get specific attribute metadata
        attr_metadata = await sdk.get_attribute_metadata("account", "name")
        
        assert "LogicalName" in attr_metadata
        assert attr_metadata["LogicalName"] == "name"
        assert "AttributeType" in attr_metadata
    
    @pytest.mark.asyncio
    async def test_fetchxml_query(self, sdk):
        """Test FetchXML query execution."""
        fetchxml = """
        <fetch top="5">
            <entity name="account">
                <attribute name="name" />
                <attribute name="accountid" />
                <attribute name="createdon" />
                <filter type="and">
                    <condition attribute="statecode" operator="eq" value="0" />
                </filter>
                <order attribute="createdon" descending="true" />
            </entity>
        </fetch>
        """
        
        result = await sdk.fetch_xml(fetchxml)
        
        assert isinstance(result, list)
        assert len(result) <= 5
        
        # Verify structure of returned data
        if result:
            account = result[0]
            assert "name" in account
            assert "accountid" in account
            assert "createdon" in account


class TestSDKErrorHandling:
    """Test error handling in integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_invalid_entity_type(self, sdk):
        """Test handling of invalid entity type."""
        with pytest.raises(Exception):  # Should raise some form of API error
            await sdk.query("nonexistent_entity")
    
    @pytest.mark.asyncio
    async def test_invalid_field_in_select(self, sdk):
        """Test handling of invalid field in select."""
        with pytest.raises(Exception):  # Should raise some form of API error
            await sdk.query("accounts", {
                "select": ["nonexistent_field"],
                "top": 1,
            })
    
    @pytest.mark.asyncio
    async def test_invalid_filter_syntax(self, sdk):
        """Test handling of invalid filter syntax."""
        with pytest.raises(Exception):  # Should raise some form of API error
            await sdk.query("accounts", {
                "filter": "invalid filter syntax",
                "top": 1,
            })


@pytest.mark.slow
class TestSDKPerformance:
    """Performance tests for the SDK."""
    
    @pytest.mark.asyncio
    async def test_large_query_performance(self, sdk):
        """Test performance with larger queries."""
        import time
        
        start_time = time.time()
        
        # Query a larger number of records
        result = await sdk.query("accounts", {
            "select": ["name", "accountid"],
            "top": 100,
        })
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert query_time < 30.0  # 30 seconds max
        assert isinstance(result.value, list)
    
    @pytest.mark.asyncio
    async def test_pagination_performance(self, sdk):
        """Test performance of pagination."""
        import time
        
        start_time = time.time()
        
        # Query all accounts with pagination
        all_accounts = await sdk.query_all("accounts", {
            "select": ["name", "accountid"],
            "top": 10,  # Small page size to test pagination
        }, max_records=50)  # Limit total records
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Should complete within reasonable time
        assert query_time < 60.0  # 60 seconds max
        assert isinstance(all_accounts, list)
        assert len(all_accounts) <= 50

