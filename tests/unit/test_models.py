"""
Unit tests for the models module.
"""

import pytest
from datetime import datetime
from uuid import UUID

from dataverse_sdk.models import (
    Entity,
    EntityReference,
    QueryOptions,
    QueryResult,
    FetchXMLQuery,
    UpsertResult,
    BulkOperationResult,
    Account,
    Contact,
)


class TestEntityReference:
    """Test cases for EntityReference model."""
    
    def test_entity_reference_creation(self):
        """Test creating an entity reference."""
        ref = EntityReference(
            entity_type="account",
            entity_id="12345678-1234-1234-1234-123456789012",
            name="Test Account"
        )
        
        assert ref.entity_type == "account"
        assert ref.entity_id == "12345678-1234-1234-1234-123456789012"
        assert ref.name == "Test Account"
    
    def test_entity_reference_with_uuid(self):
        """Test creating entity reference with UUID."""
        entity_id = UUID("12345678-1234-1234-1234-123456789012")
        ref = EntityReference(
            entity_type="account",
            entity_id=entity_id
        )
        
        assert ref.entity_id == "12345678-1234-1234-1234-123456789012"
    
    def test_entity_reference_invalid_id(self):
        """Test entity reference with invalid ID."""
        with pytest.raises(ValueError) as exc_info:
            EntityReference(
                entity_type="account",
                entity_id="invalid-id"
            )
        
        assert "Entity ID must be a valid GUID" in str(exc_info.value)
    
    def test_to_odata_ref(self):
        """Test converting to OData reference format."""
        ref = EntityReference(
            entity_type="accounts",
            entity_id="12345678-1234-1234-1234-123456789012"
        )
        
        odata_ref = ref.to_odata_ref()
        assert odata_ref == "accounts(12345678-1234-1234-1234-123456789012)"


class TestEntity:
    """Test cases for Entity base model."""
    
    def test_entity_creation(self):
        """Test creating a basic entity."""
        entity = Entity(
            id="12345678-1234-1234-1234-123456789012",
            created_on=datetime(2023, 1, 1),
            modified_on=datetime(2023, 1, 2),
        )
        
        assert entity.id == "12345678-1234-1234-1234-123456789012"
        assert entity.created_on == datetime(2023, 1, 1)
        assert entity.modified_on == datetime(2023, 1, 2)
    
    def test_entity_with_alias_fields(self):
        """Test entity creation with alias fields."""
        entity = Entity(
            entityid="12345678-1234-1234-1234-123456789012",
            createdon=datetime(2023, 1, 1),
        )
        
        assert entity.id == "12345678-1234-1234-1234-123456789012"
        assert entity.created_on == datetime(2023, 1, 1)
    
    def test_entity_invalid_id(self):
        """Test entity with invalid ID."""
        with pytest.raises(ValueError) as exc_info:
            Entity(id="invalid-id")
        
        assert "Entity ID must be a valid GUID" in str(exc_info.value)
    
    def test_entity_extra_fields(self):
        """Test entity with extra fields."""
        entity = Entity(
            id="12345678-1234-1234-1234-123456789012",
            custom_field="custom_value",
            another_field=123,
        )
        
        assert entity.custom_field == "custom_value"
        assert entity.another_field == 123
    
    def test_get_entity_reference(self):
        """Test getting entity reference."""
        entity = Entity(
            id="12345678-1234-1234-1234-123456789012",
            name="Test Entity",
        )
        
        ref = entity.get_entity_reference("accounts")
        
        assert ref.entity_type == "accounts"
        assert ref.entity_id == "12345678-1234-1234-1234-123456789012"
        assert ref.name == "Test Entity"
    
    def test_get_entity_reference_without_id(self):
        """Test getting entity reference without ID."""
        entity = Entity()
        
        with pytest.raises(ValueError) as exc_info:
            entity.get_entity_reference("accounts")
        
        assert "Entity ID is required" in str(exc_info.value)


class TestQueryOptions:
    """Test cases for QueryOptions model."""
    
    def test_query_options_creation(self):
        """Test creating query options."""
        options = QueryOptions(
            select=["name", "websiteurl"],
            filter="name eq 'Test'",
            order_by=["name asc"],
            top=10,
            count=True,
        )
        
        assert options.select == ["name", "websiteurl"]
        assert options.filter == "name eq 'Test'"
        assert options.order_by == ["name asc"]
        assert options.top == 10
        assert options.count is True
    
    def test_to_odata_params(self):
        """Test converting to OData parameters."""
        options = QueryOptions(
            select=["name", "websiteurl"],
            filter="name eq 'Test'",
            order_by=["name asc", "createdon desc"],
            expand=["primarycontactid"],
            top=10,
            skip=5,
            count=True,
        )
        
        params = options.to_odata_params()
        
        assert params["$select"] == "name,websiteurl"
        assert params["$filter"] == "name eq 'Test'"
        assert params["$orderby"] == "name asc,createdon desc"
        assert params["$expand"] == "primarycontactid"
        assert params["$top"] == "10"
        assert params["$skip"] == "5"
        assert params["$count"] == "true"
    
    def test_empty_query_options(self):
        """Test empty query options."""
        options = QueryOptions()
        params = options.to_odata_params()
        
        assert params == {}


class TestQueryResult:
    """Test cases for QueryResult model."""
    
    def test_query_result_creation(self):
        """Test creating a query result."""
        result = QueryResult(
            value=[{"id": "123", "name": "Test"}],
            count=1,
            next_link="https://api.example.com/next",
        )
        
        assert len(result.value) == 1
        assert result.count == 1
        assert result.next_link == "https://api.example.com/next"
    
    def test_query_result_with_aliases(self):
        """Test query result with OData aliases."""
        result = QueryResult(**{
            "value": [{"id": "123", "name": "Test"}],
            "@odata.count": 1,
            "@odata.nextLink": "https://api.example.com/next",
        })
        
        assert result.count == 1
        assert result.next_link == "https://api.example.com/next"
    
    def test_has_more_property(self):
        """Test has_more property."""
        # With next link
        result_with_more = QueryResult(
            value=[],
            next_link="https://api.example.com/next",
        )
        assert result_with_more.has_more is True
        
        # Without next link
        result_without_more = QueryResult(value=[])
        assert result_without_more.has_more is False
    
    def test_total_count_property(self):
        """Test total_count property."""
        result = QueryResult(value=[], count=100)
        assert result.total_count == 100
        
        result_no_count = QueryResult(value=[])
        assert result_no_count.total_count is None


class TestFetchXMLQuery:
    """Test cases for FetchXMLQuery model."""
    
    def test_fetchxml_query_creation(self):
        """Test creating a FetchXML query."""
        query = FetchXMLQuery(
            entity="account",
            attributes=["name", "websiteurl"],
            top=10,
            distinct=True,
        )
        
        assert query.entity == "account"
        assert query.attributes == ["name", "websiteurl"]
        assert query.top == 10
        assert query.distinct is True
    
    def test_to_fetchxml_basic(self):
        """Test converting to FetchXML string."""
        query = FetchXMLQuery(
            entity="account",
            attributes=["name", "websiteurl"],
            top=10,
        )
        
        fetchxml = query.to_fetchxml()
        
        assert '<fetch top="10">' in fetchxml
        assert '<entity name="account">' in fetchxml
        assert '<attribute name="name" />' in fetchxml
        assert '<attribute name="websiteurl" />' in fetchxml
        assert '</entity>' in fetchxml
        assert '</fetch>' in fetchxml
    
    def test_to_fetchxml_with_filters(self):
        """Test FetchXML with filters."""
        query = FetchXMLQuery(
            entity="account",
            filters=[{
                "type": "and",
                "conditions": [
                    {"attribute": "name", "operator": "eq", "value": "Test"},
                    {"attribute": "statecode", "operator": "eq", "value": "0"},
                ]
            }]
        )
        
        fetchxml = query.to_fetchxml()
        
        assert '<filter type="and">' in fetchxml
        assert '<condition attribute="name" operator="eq" value="Test" />' in fetchxml
        assert '<condition attribute="statecode" operator="eq" value="0" />' in fetchxml
    
    def test_to_fetchxml_with_orders(self):
        """Test FetchXML with order specifications."""
        query = FetchXMLQuery(
            entity="account",
            orders=[
                {"attribute": "name", "descending": False},
                {"attribute": "createdon", "descending": True},
            ]
        )
        
        fetchxml = query.to_fetchxml()
        
        assert '<order attribute="name" />' in fetchxml
        assert '<order attribute="createdon" descending="true" />' in fetchxml
    
    def test_to_fetchxml_all_attributes(self):
        """Test FetchXML with all attributes."""
        query = FetchXMLQuery(entity="account")  # No specific attributes
        
        fetchxml = query.to_fetchxml()
        
        assert '<all-attributes />' in fetchxml


class TestUpsertResult:
    """Test cases for UpsertResult model."""
    
    def test_upsert_result_created(self):
        """Test upsert result for created entity."""
        result = UpsertResult(
            entity_id="12345678-1234-1234-1234-123456789012",
            created=True,
        )
        
        assert result.entity_id == "12345678-1234-1234-1234-123456789012"
        assert result.was_created is True
        assert result.was_updated is False
    
    def test_upsert_result_updated(self):
        """Test upsert result for updated entity."""
        result = UpsertResult(
            entity_id="12345678-1234-1234-1234-123456789012",
            created=False,
        )
        
        assert result.was_created is False
        assert result.was_updated is True


class TestBulkOperationResult:
    """Test cases for BulkOperationResult model."""
    
    def test_bulk_operation_result_creation(self):
        """Test creating bulk operation result."""
        result = BulkOperationResult(
            total_processed=100,
            successful=95,
            failed=5,
            errors=[{"error": "Test error"}],
        )
        
        assert result.total_processed == 100
        assert result.successful == 95
        assert result.failed == 5
        assert len(result.errors) == 1
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = BulkOperationResult(
            total_processed=100,
            successful=80,
            failed=20,
        )
        
        assert result.success_rate == 80.0
        
        # Test with zero processed
        empty_result = BulkOperationResult()
        assert empty_result.success_rate == 0.0
    
    def test_has_errors_property(self):
        """Test has_errors property."""
        result_with_errors = BulkOperationResult(failed=5)
        assert result_with_errors.has_errors is True
        
        result_without_errors = BulkOperationResult(failed=0)
        assert result_without_errors.has_errors is False


class TestAccountModel:
    """Test cases for Account entity model."""
    
    def test_account_creation(self):
        """Test creating an Account entity."""
        account = Account(
            id="12345678-1234-1234-1234-123456789012",
            name="Test Account",
            account_number="ACC-001",
            website="https://test.com",
            telephone1="555-0123",
            email_address1="test@test.com",
        )
        
        assert account.name == "Test Account"
        assert account.account_number == "ACC-001"
        assert account.website == "https://test.com"
        assert account.telephone1 == "555-0123"
        assert account.email_address1 == "test@test.com"
    
    def test_account_with_aliases(self):
        """Test Account with alias fields."""
        account = Account(
            accountnumber="ACC-002",
            emailaddress1="alias@test.com",
        )
        
        assert account.account_number == "ACC-002"
        assert account.email_address1 == "alias@test.com"


class TestContactModel:
    """Test cases for Contact entity model."""
    
    def test_contact_creation(self):
        """Test creating a Contact entity."""
        contact = Contact(
            id="12345678-1234-1234-1234-123456789012",
            first_name="John",
            last_name="Doe",
            full_name="John Doe",
            email_address1="john.doe@test.com",
            telephone1="555-0123",
        )
        
        assert contact.first_name == "John"
        assert contact.last_name == "Doe"
        assert contact.full_name == "John Doe"
        assert contact.email_address1 == "john.doe@test.com"
        assert contact.telephone1 == "555-0123"
    
    def test_contact_with_aliases(self):
        """Test Contact with alias fields."""
        contact = Contact(
            firstname="Jane",
            lastname="Smith",
            fullname="Jane Smith",
            emailaddress1="jane.smith@test.com",
        )
        
        assert contact.first_name == "Jane"
        assert contact.last_name == "Smith"
        assert contact.full_name == "Jane Smith"
        assert contact.email_address1 == "jane.smith@test.com"

