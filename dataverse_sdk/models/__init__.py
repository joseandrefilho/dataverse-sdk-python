"""
Data models for the Dataverse SDK.

This module provides Pydantic models for strong typing and validation
of Dataverse entities and API responses.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator


class EntityReference(BaseModel):
    """Reference to a Dataverse entity."""
    
    entity_type: str = Field(..., description="Entity logical name")
    entity_id: Union[str, UUID] = Field(..., description="Entity ID")
    name: Optional[str] = Field(None, description="Entity display name")
    
    @validator("entity_id")
    def validate_entity_id(cls, v):
        """Validate entity ID format."""
        if isinstance(v, str):
            # Ensure it's a valid GUID format
            try:
                UUID(v)
            except ValueError:
                raise ValueError("Entity ID must be a valid GUID")
        return str(v)
    
    def to_odata_ref(self) -> str:
        """Convert to OData entity reference format."""
        return f"{self.entity_type}({self.entity_id})"


class EntityMetadata(BaseModel):
    """Metadata for a Dataverse entity."""
    
    logical_name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    primary_id_attribute: Optional[str] = None
    primary_name_attribute: Optional[str] = None
    entity_set_name: Optional[str] = None
    is_custom: bool = False
    is_activity: bool = False
    attributes: List[Dict[str, Any]] = Field(default_factory=list)


class AttributeMetadata(BaseModel):
    """Metadata for a Dataverse attribute."""
    
    logical_name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    attribute_type: str
    is_primary_id: bool = False
    is_primary_name: bool = False
    is_required: bool = False
    is_custom: bool = False
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None


class Entity(BaseModel):
    """Base class for Dataverse entities."""
    
    id: Optional[Union[str, UUID]] = Field(None, alias="entityid")
    created_on: Optional[datetime] = Field(None, alias="createdon")
    modified_on: Optional[datetime] = Field(None, alias="modifiedon")
    version_number: Optional[int] = Field(None, alias="versionnumber")
    
    class Config:
        populate_by_name = True  # Renamed from allow_population_by_field_name in Pydantic v2
        extra = "allow"  # Allow additional fields for dynamic entities
    
    @validator("id")
    def validate_id(cls, v):
        """Validate entity ID format."""
        if v is not None:
            if isinstance(v, str):
                try:
                    UUID(v)
                except ValueError:
                    raise ValueError("Entity ID must be a valid GUID")
            return str(v)
        return v
    
    def get_entity_reference(self, entity_type: str) -> EntityReference:
        """Get entity reference for this entity."""
        if not self.id:
            raise ValueError("Entity ID is required for entity reference")
        
        return EntityReference(
            entity_type=entity_type,
            entity_id=self.id,
            name=getattr(self, "name", None),
        )


class QueryOptions(BaseModel):
    """Options for querying Dataverse entities."""
    
    select: Optional[List[str]] = Field(None, description="Fields to select")
    filter: Optional[str] = Field(None, description="OData filter expression")
    order_by: Optional[List[str]] = Field(None, description="Order by fields")
    expand: Optional[List[str]] = Field(None, description="Related entities to expand")
    top: Optional[int] = Field(None, description="Maximum number of records")
    skip: Optional[int] = Field(None, description="Number of records to skip")
    count: bool = Field(False, description="Include total count")
    
    def to_odata_params(self) -> Dict[str, str]:
        """Convert to OData query parameters."""
        params = {}
        
        if self.select:
            params["$select"] = ",".join(self.select)
        
        if self.filter:
            params["$filter"] = self.filter
        
        if self.order_by:
            params["$orderby"] = ",".join(self.order_by)
        
        if self.expand:
            params["$expand"] = ",".join(self.expand)
        
        if self.top is not None:
            params["$top"] = str(self.top)
        
        if self.skip is not None:
            params["$skip"] = str(self.skip)
        
        if self.count:
            params["$count"] = "true"
        
        return params


class QueryResult(BaseModel):
    """Result of a query operation."""
    
    value: List[Dict[str, Any]] = Field(default_factory=list)
    count: Optional[int] = Field(None, alias="@odata.count")
    next_link: Optional[str] = Field(None, alias="@odata.nextLink")
    context: Optional[str] = Field(None, alias="@odata.context")
    
    class Config:
        populate_by_name = True  # Renamed from allow_population_by_field_name in Pydantic v2
    
    @property
    def has_more(self) -> bool:
        """Check if there are more results available."""
        return self.next_link is not None
    
    @property
    def total_count(self) -> Optional[int]:
        """Get total count if available."""
        return self.count


class BatchRequest(BaseModel):
    """Batch request for multiple operations."""
    
    requests: List[Dict[str, Any]] = Field(default_factory=list)
    change_set_id: Optional[str] = None
    
    def add_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a request to the batch."""
        request = {
            "method": method.upper(),
            "url": url,
        }
        
        if headers:
            request["headers"] = headers
        
        if body:
            request["body"] = body
        
        self.requests.append(request)


class BatchResponse(BaseModel):
    """Response from a batch operation."""
    
    responses: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    
    @property
    def success_count(self) -> int:
        """Number of successful operations."""
        return len([r for r in self.responses if r.get("status", 0) < 400])
    
    @property
    def error_count(self) -> int:
        """Number of failed operations."""
        return len(self.errors) + len([r for r in self.responses if r.get("status", 0) >= 400])
    
    @property
    def is_success(self) -> bool:
        """Check if all operations succeeded."""
        return self.error_count == 0


class FetchXMLQuery(BaseModel):
    """FetchXML query definition."""
    
    entity: str = Field(..., description="Entity logical name")
    attributes: List[str] = Field(default_factory=list, description="Attributes to fetch")
    filters: List[Dict[str, Any]] = Field(default_factory=list, description="Filter conditions")
    links: List[Dict[str, Any]] = Field(default_factory=list, description="Entity links")
    orders: List[Dict[str, str]] = Field(default_factory=list, description="Order specifications")
    top: Optional[int] = Field(None, description="Maximum records")
    page: Optional[int] = Field(None, description="Page number")
    count: Optional[int] = Field(None, description="Page size")
    distinct: bool = Field(False, description="Return distinct records")
    
    def to_fetchxml(self) -> str:
        """Convert to FetchXML string."""
        # Build FetchXML structure
        fetch_attrs = []
        
        if self.top:
            fetch_attrs.append(f'top="{self.top}"')
        
        if self.page:
            fetch_attrs.append(f'page="{self.page}"')
        
        if self.count:
            fetch_attrs.append(f'count="{self.count}"')
        
        if self.distinct:
            fetch_attrs.append('distinct="true"')
        
        fetch_tag = f"<fetch {' '.join(fetch_attrs)}>" if fetch_attrs else "<fetch>"
        
        # Entity tag
        xml_parts = [
            fetch_tag,
            f'  <entity name="{self.entity}">',
        ]
        
        # Attributes
        if self.attributes:
            for attr in self.attributes:
                xml_parts.append(f'    <attribute name="{attr}" />')
        else:
            xml_parts.append('    <all-attributes />')
        
        # Filters
        for filter_def in self.filters:
            filter_type = filter_def.get("type", "and")
            xml_parts.append(f'    <filter type="{filter_type}">')
            
            for condition in filter_def.get("conditions", []):
                attr = condition.get("attribute")
                operator = condition.get("operator", "eq")
                value = condition.get("value", "")
                xml_parts.append(f'      <condition attribute="{attr}" operator="{operator}" value="{value}" />')
            
            xml_parts.append('    </filter>')
        
        # Orders
        for order in self.orders:
            attr = order.get("attribute")
            descending = order.get("descending", False)
            desc_attr = ' descending="true"' if descending else ''
            xml_parts.append(f'    <order attribute="{attr}"{desc_attr} />')
        
        # Links (simplified)
        for link in self.links:
            to_entity = link.get("to")
            from_attr = link.get("from")
            to_attr = link.get("to_attr", f"{to_entity}id")
            xml_parts.append(f'    <link-entity name="{to_entity}" from="{to_attr}" to="{from_attr}">')
            
            # Link attributes
            for attr in link.get("attributes", []):
                xml_parts.append(f'      <attribute name="{attr}" />')
            
            xml_parts.append('    </link-entity>')
        
        xml_parts.extend([
            '  </entity>',
            '</fetch>',
        ])
        
        return '\n'.join(xml_parts)


class UpsertResult(BaseModel):
    """Result of an upsert operation."""
    
    entity_id: str
    created: bool = Field(description="True if entity was created, False if updated")
    
    @property
    def was_created(self) -> bool:
        """Check if entity was created."""
        return self.created
    
    @property
    def was_updated(self) -> bool:
        """Check if entity was updated."""
        return not self.created


class AssociationRequest(BaseModel):
    """Request for entity association."""
    
    relationship_name: str
    primary_entity_id: str
    related_entity_id: str
    related_entity_type: str


class BulkOperationResult(BaseModel):
    """Result of a bulk operation."""
    
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_processed == 0:
            return 0.0
        return (self.successful / self.total_processed) * 100
    
    @property
    def has_errors(self) -> bool:
        """Check if there were any errors."""
        return self.failed > 0


# Common entity models (can be extended by users)

class Account(Entity):
    """Account entity model."""
    
    name: Optional[str] = None
    account_number: Optional[str] = Field(None, alias="accountnumber")
    website: Optional[str] = None
    telephone1: Optional[str] = None
    email_address1: Optional[str] = Field(None, alias="emailaddress1")
    
    class Config:
        populate_by_name = True  # Renamed from allow_population_by_field_name in Pydantic v2


class Contact(Entity):
    """Contact entity model."""
    
    first_name: Optional[str] = Field(None, alias="firstname")
    last_name: Optional[str] = Field(None, alias="lastname")
    full_name: Optional[str] = Field(None, alias="fullname")
    email_address1: Optional[str] = Field(None, alias="emailaddress1")
    telephone1: Optional[str] = None
    
    class Config:
        populate_by_name = True  # Renamed from allow_population_by_field_name in Pydantic v2


# Convenience exports
__all__ = [
    "Entity",
    "EntityReference",
    "EntityMetadata",
    "AttributeMetadata",
    "QueryOptions",
    "QueryResult",
    "BatchRequest",
    "BatchResponse",
    "FetchXMLQuery",
    "UpsertResult",
    "AssociationRequest",
    "BulkOperationResult",
    "Account",
    "Contact",
]

