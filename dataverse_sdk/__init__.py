"""
Microsoft Dataverse SDK for Python.

A comprehensive, async Python SDK for Microsoft Dataverse with enterprise features
including connection pooling, retry logic, batch operations, and extensibility hooks.

Example usage:
    ```python
    import asyncio
    from dataverse_sdk import DataverseSDK
    
    async def main():
        sdk = DataverseSDK(
            dataverse_url="https://yourorg.crm.dynamics.com",
            client_id="your-client-id",
            client_secret="your-client-secret",
            tenant_id="your-tenant-id",
        )
        
        async with sdk:
            # Create an account
            account = await sdk.create("accounts", {
                "name": "Contoso Ltd",
                "websiteurl": "https://contoso.com"
            })
            
            # Query accounts
            accounts = await sdk.query("accounts", {
                "select": ["name", "websiteurl"],
                "filter": "name eq 'Contoso Ltd'"
            })
            
            # Bulk operations
            result = await sdk.bulk_create("contacts", [
                {"firstname": "John", "lastname": "Doe"},
                {"firstname": "Jane", "lastname": "Smith"},
            ])
    
    asyncio.run(main())
    ```
"""

import asyncio
import os
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

import structlog
from dotenv import load_dotenv

from .auth import DataverseAuthenticator
from .batch import BatchProcessor
from .client import AsyncDataverseClient
from .exceptions import (
    ConfigurationError,
    EntityNotFoundError,
    ValidationError,
)
from .hooks import HookManager, register_global_hook
from .models import (
    Entity,
    EntityReference,
    QueryOptions,
    QueryResult,
    FetchXMLQuery,
    UpsertResult,
    BulkOperationResult,
)
from .utils import Config, build_url, format_odata_filter, extract_entity_id


# Load environment variables
load_dotenv()

logger = structlog.get_logger(__name__)


class DataverseSDK:
    """
    Main SDK class providing high-level interface to Microsoft Dataverse.
    
    This class integrates all SDK components and provides a simple, intuitive
    interface for common Dataverse operations.
    """
    
    def __init__(
        self,
        dataverse_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        tenant_id: Optional[str] = None,
        authority: Optional[str] = None,
        scope: Optional[str] = None,
        config: Optional[Config] = None,
        hook_manager: Optional[HookManager] = None,
    ) -> None:
        """
        Initialize the Dataverse SDK.
        
        Args:
            dataverse_url: Dataverse environment URL
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
            tenant_id: Azure AD tenant ID
            authority: Authority URL (optional)
            scope: OAuth scope (optional)
            config: Configuration object (optional)
            hook_manager: Hook manager for extensibility (optional)
        """
        # Load configuration from environment if not provided
        self.dataverse_url = dataverse_url or os.getenv("DATAVERSE_URL")
        self.client_id = client_id or os.getenv("AZURE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AZURE_CLIENT_SECRET")
        self.tenant_id = tenant_id or os.getenv("AZURE_TENANT_ID")
        self.authority = authority or os.getenv("AZURE_AUTHORITY")
        self.scope = scope or os.getenv("AZURE_SCOPE")
        
        # Validate required configuration
        if not all([self.dataverse_url, self.client_id, self.tenant_id]):
            raise ConfigurationError(
                "Missing required configuration. Please provide dataverse_url, "
                "client_id, and tenant_id either as parameters or environment variables."
            )
        
        # Initialize components
        self.config = config or Config()
        self.hook_manager = hook_manager or HookManager()
        
        # Initialize authenticator
        self.authenticator = DataverseAuthenticator(
            client_id=self.client_id,
            tenant_id=self.tenant_id,
            dataverse_url=self.dataverse_url,
            client_secret=self.client_secret,
            authority=self.authority,
            scope=self.scope,
        )
        
        # Initialize client
        self.client = AsyncDataverseClient(
            dataverse_url=self.dataverse_url,
            authenticator=self.authenticator,
            config=self.config,
            hook_manager=self.hook_manager,
        )
        
        # Initialize batch processor
        self.batch_processor = BatchProcessor(
            client=self.client,
            default_batch_size=self.config.get("default_batch_size", 100),
            max_batch_size=self.config.get("max_batch_size", 1000),
        )
        
        logger.info(
            "Dataverse SDK initialized",
            dataverse_url=self.dataverse_url,
            client_id=self.client_id,
            tenant_id=self.tenant_id,
        )
    
    async def __aenter__(self) -> "DataverseSDK":
        """Async context manager entry."""
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    # CRUD Operations
    
    async def create(
        self,
        entity_type: str,
        data: Dict[str, Any],
        return_record: bool = False,
    ) -> Union[str, Dict[str, Any]]:
        """
        Create a new entity.
        
        Args:
            entity_type: Entity logical name
            data: Entity data
            return_record: Whether to return the created record
            
        Returns:
            Entity ID or full record if return_record=True
        """
        headers = {}
        if return_record:
            headers["Prefer"] = "return=representation"
        
        response = await self.client.post(entity_type, data, headers=headers)
        
        if return_record:
            return response
        else:
            # Extract entity ID from Location header or response
            entity_id = response.get("id") or extract_entity_id(
                response.get("@odata.id", "")
            )
            return entity_id
    
    async def read(
        self,
        entity_type: str,
        entity_id: str,
        select: Optional[List[str]] = None,
        expand: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Read an entity by ID.
        
        Args:
            entity_type: Entity logical name
            entity_id: Entity ID
            select: Fields to select
            expand: Related entities to expand
            
        Returns:
            Entity data
            
        Raises:
            EntityNotFoundError: If entity is not found
        """
        params = {}
        
        if select:
            params["$select"] = ",".join(select)
        
        if expand:
            params["$expand"] = ",".join(expand)
        
        try:
            endpoint = f"{entity_type}({entity_id})"
            return await self.client.get(endpoint, params=params)
        except Exception as e:
            if "404" in str(e) or "Not Found" in str(e):
                raise EntityNotFoundError(entity_type, entity_id) from e
            raise
    
    async def update(
        self,
        entity_type: str,
        entity_id: str,
        data: Dict[str, Any],
        return_record: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Update an entity.
        
        Args:
            entity_type: Entity logical name
            entity_id: Entity ID
            data: Update data
            return_record: Whether to return the updated record
            
        Returns:
            Updated record if return_record=True, None otherwise
        """
        headers = {}
        if return_record:
            headers["Prefer"] = "return=representation"
        
        endpoint = f"{entity_type}({entity_id})"
        response = await self.client.patch(endpoint, data, headers=headers)
        
        return response if return_record else None
    
    async def delete(self, entity_type: str, entity_id: str) -> None:
        """
        Delete an entity.
        
        Args:
            entity_type: Entity logical name
            entity_id: Entity ID
        """
        endpoint = f"{entity_type}({entity_id})"
        await self.client.delete(endpoint)
    
    async def upsert(
        self,
        entity_type: str,
        data: Dict[str, Any],
        alternate_key: Optional[Dict[str, Any]] = None,
        return_record: bool = False,
    ) -> Union[UpsertResult, Dict[str, Any]]:
        """
        Upsert (create or update) an entity.
        
        Args:
            entity_type: Entity logical name
            data: Entity data
            alternate_key: Alternate key for upsert
            return_record: Whether to return the record
            
        Returns:
            UpsertResult or full record if return_record=True
        """
        headers = {
            "Prefer": "return=representation" if return_record else "return=minimal",
        }
        
        if alternate_key:
            # Build alternate key path
            key_parts = []
            for key, value in alternate_key.items():
                key_parts.append(f"{key}='{value}'")
            endpoint = f"{entity_type}({','.join(key_parts)})"
        else:
            endpoint = entity_type
        
        response = await self.client.patch(endpoint, data, headers=headers)
        
        # Determine if entity was created or updated
        # This is typically indicated by the response status or headers
        created = response.get("@odata.context", "").endswith("/$entity")
        
        if return_record:
            return response
        else:
            entity_id = response.get("id") or extract_entity_id(
                response.get("@odata.id", "")
            )
            return UpsertResult(entity_id=entity_id, created=created)
    
    # Query Operations
    
    async def query(
        self,
        entity_type: str,
        options: Optional[Union[QueryOptions, Dict[str, Any]]] = None,
    ) -> QueryResult:
        """
        Query entities with OData options.
        
        Args:
            entity_type: Entity logical name
            options: Query options
            
        Returns:
            Query result with entities and metadata
        """
        if isinstance(options, dict):
            options = QueryOptions(**options)
        elif options is None:
            options = QueryOptions()
        
        params = options.to_odata_params()
        response = await self.client.get(entity_type, params=params)
        
        return QueryResult(**response)
    
    async def query_all(
        self,
        entity_type: str,
        options: Optional[Union[QueryOptions, Dict[str, Any]]] = None,
        max_records: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query all entities with automatic pagination.
        
        Args:
            entity_type: Entity logical name
            options: Query options
            max_records: Maximum number of records to retrieve
            
        Returns:
            List of all matching entities
        """
        all_entities = []
        current_options = options
        records_retrieved = 0
        
        while True:
            result = await self.query(entity_type, current_options)
            all_entities.extend(result.value)
            records_retrieved += len(result.value)
            
            # Check limits
            if max_records and records_retrieved >= max_records:
                all_entities = all_entities[:max_records]
                break
            
            # Check for more pages
            if not result.has_more:
                break
            
            # Prepare next page options
            if isinstance(current_options, QueryOptions):
                current_options = QueryOptions(
                    select=current_options.select,
                    filter=current_options.filter,
                    order_by=current_options.order_by,
                    expand=current_options.expand,
                    count=current_options.count,
                )
            else:
                current_options = QueryOptions()
            
            # Extract skip value from next link
            # This is a simplified implementation
            if result.next_link:
                import urllib.parse as urlparse
                parsed = urlparse.urlparse(result.next_link)
                query_params = urlparse.parse_qs(parsed.query)
                if "$skip" in query_params:
                    current_options.skip = int(query_params["$skip"][0])
        
        return all_entities
    
    async def fetch_xml(self, fetch_xml: Union[str, FetchXMLQuery]) -> List[Dict[str, Any]]:
        """
        Execute FetchXML query.
        
        Args:
            fetch_xml: FetchXML query string or FetchXMLQuery object
            
        Returns:
            List of entities matching the query
        """
        if isinstance(fetch_xml, FetchXMLQuery):
            fetch_xml = fetch_xml.to_fetchxml()
        
        # URL encode the FetchXML
        import urllib.parse
        encoded_fetch_xml = urllib.parse.quote(fetch_xml)
        
        endpoint = f"accounts?fetchXml={encoded_fetch_xml}"
        response = await self.client.get(endpoint)
        
        return response.get("value", [])
    
    # Association Operations
    
    async def associate(
        self,
        primary_entity_type: str,
        primary_entity_id: str,
        relationship_name: str,
        related_entity_type: str,
        related_entity_id: str,
    ) -> None:
        """
        Associate two entities.
        
        Args:
            primary_entity_type: Primary entity logical name
            primary_entity_id: Primary entity ID
            relationship_name: Relationship name
            related_entity_type: Related entity logical name
            related_entity_id: Related entity ID
        """
        endpoint = f"{primary_entity_type}({primary_entity_id})/{relationship_name}/$ref"
        
        data = {
            "@odata.id": f"{self.client.api_base_url}{related_entity_type}({related_entity_id})"
        }
        
        await self.client.post(endpoint, data)
    
    async def disassociate(
        self,
        primary_entity_type: str,
        primary_entity_id: str,
        relationship_name: str,
        related_entity_id: Optional[str] = None,
    ) -> None:
        """
        Disassociate entities.
        
        Args:
            primary_entity_type: Primary entity logical name
            primary_entity_id: Primary entity ID
            relationship_name: Relationship name
            related_entity_id: Related entity ID (for many-to-many relationships)
        """
        if related_entity_id:
            endpoint = f"{primary_entity_type}({primary_entity_id})/{relationship_name}({related_entity_id})/$ref"
        else:
            endpoint = f"{primary_entity_type}({primary_entity_id})/{relationship_name}/$ref"
        
        await self.client.delete(endpoint)
    
    # Bulk Operations
    
    async def bulk_create(
        self,
        entity_type: str,
        entities: List[Dict[str, Any]],
        batch_size: Optional[int] = None,
        parallel: bool = True,
    ) -> BulkOperationResult:
        """
        Bulk create entities.
        
        Args:
            entity_type: Entity logical name
            entities: List of entity data
            batch_size: Batch size for operations
            parallel: Whether to execute batches in parallel
            
        Returns:
            Bulk operation result
        """
        return await self.batch_processor.bulk_create(
            entity_type, entities, batch_size, parallel
        )
    
    async def bulk_update(
        self,
        entity_type: str,
        updates: List[Dict[str, Any]],
        batch_size: Optional[int] = None,
        parallel: bool = True,
    ) -> BulkOperationResult:
        """
        Bulk update entities.
        
        Args:
            entity_type: Entity logical name
            updates: List of updates (must include entity ID)
            batch_size: Batch size for operations
            parallel: Whether to execute batches in parallel
            
        Returns:
            Bulk operation result
        """
        return await self.batch_processor.bulk_update(
            entity_type, updates, batch_size, parallel
        )
    
    async def bulk_delete(
        self,
        entity_type: str,
        entity_ids: List[str],
        batch_size: Optional[int] = None,
        parallel: bool = True,
    ) -> BulkOperationResult:
        """
        Bulk delete entities.
        
        Args:
            entity_type: Entity logical name
            entity_ids: List of entity IDs to delete
            batch_size: Batch size for operations
            parallel: Whether to execute batches in parallel
            
        Returns:
            Bulk operation result
        """
        return await self.batch_processor.bulk_delete(
            entity_type, entity_ids, batch_size, parallel
        )
    
    # Metadata Operations
    
    async def get_entity_metadata(self, entity_type: str) -> Dict[str, Any]:
        """
        Get metadata for an entity.
        
        Args:
            entity_type: Entity logical name
            
        Returns:
            Entity metadata
        """
        endpoint = f"EntityDefinitions(LogicalName='{entity_type}')"
        return await self.client.get(endpoint)
    
    async def get_attribute_metadata(
        self, entity_type: str, attribute_name: str
    ) -> Dict[str, Any]:
        """
        Get metadata for an attribute.
        
        Args:
            entity_type: Entity logical name
            attribute_name: Attribute logical name
            
        Returns:
            Attribute metadata
        """
        endpoint = f"EntityDefinitions(LogicalName='{entity_type}')/Attributes(LogicalName='{attribute_name}')"
        return await self.client.get(endpoint)
    
    # Utility Methods
    
    def register_hook(self, hook_type, hook_func, priority: int = 0) -> None:
        """Register a hook function."""
        self.hook_manager.register_hook(hook_type, hook_func, priority)
    
    def unregister_hook(self, hook_type, hook_func) -> bool:
        """Unregister a hook function."""
        return self.hook_manager.unregister_hook(hook_type, hook_func)
    
    async def clear_auth_cache(self) -> None:
        """Clear authentication token cache."""
        await self.authenticator.clear_cache()


# Convenience exports
__all__ = [
    "DataverseSDK",
    # Re-export commonly used classes
    "Entity",
    "EntityReference", 
    "QueryOptions",
    "QueryResult",
    "FetchXMLQuery",
    "UpsertResult",
    "BulkOperationResult",
    "Config",
    # Re-export exceptions
    "ConfigurationError",
    "EntityNotFoundError",
    "ValidationError",
]

# Package metadata
__version__ = "1.0.0"
__author__ = "Dataverse SDK Team"
__email__ = "team@dataverse-sdk.com"

