# Microsoft Dataverse SDK for Python

[![PyPI version](https://badge.fury.io/py/crmadminbrasil-crmadminbrasil-dataverse-sdk.svg)](https://pypi.org/project/crmadminbrasil-crmadminbrasil-dataverse-sdk/)
[![Python Support](https://img.shields.io/pypi/pyversions/crmadminbrasil-crmadminbrasil-dataverse-sdk.svg)](https://pypi.org/project/crmadminbrasil-crmadminbrasil-dataverse-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://github.com/crmadminbrasil-dataverse-sdk/crmadminbrasil-dataverse-sdk/workflows/Tests/badge.svg)](https://github.com/crmadminbrasil-dataverse-sdk/crmadminbrasil-dataverse-sdk/actions)
[![Coverage](https://codecov.io/gh/crmadminbrasil-dataverse-sdk/crmadminbrasil-dataverse-sdk/branch/main/graph/badge.svg)](https://codecov.io/gh/crmadminbrasil-dataverse-sdk/crmadminbrasil-dataverse-sdk)

A comprehensive, enterprise-ready Python SDK for Microsoft Dataverse with async support, advanced features, and production-grade reliability.

## 🚀 Features

### Core Capabilities
- **100% Async Support**: Built with `httpx` and `asyncio` for high-performance async operations
- **Enterprise Ready**: Connection pooling, retry logic, rate limiting, and comprehensive error handling
- **Type Safety**: Full type hints with Pydantic models for strong typing and validation
- **Extensible**: Hook system for custom logging, telemetry, and request/response interceptors

### Operations
- **Complete CRUD**: Create, Read, Update, Delete, and Upsert operations
- **Bulk Operations**: High-performance batch processing with auto-chunking and parallel execution
- **Advanced Queries**: OData queries, FetchXML support, and intelligent pagination
- **Associations**: Entity relationship management (associate/disassociate)
- **Metadata**: Entity and attribute metadata retrieval
- **File Operations**: Attachment upload/download support

### Developer Experience
- **CLI Tool**: Full-featured command-line interface for all operations
- **Rich Documentation**: Comprehensive docs with examples and best practices
- **Testing**: Extensive test suite with unit and integration tests
- **CI/CD Ready**: GitHub Actions workflows and PyPI publishing automation

## 📦 Installation

### From PyPI (Recommended)
```bash
pip install crmadminbrasil-dataverse-sdk
```

### Development Installation
```bash
git clone https://github.com/crmadminbrasil-dataverse-sdk/crmadminbrasil-dataverse-sdk.git
cd crmadminbrasil-dataverse-sdk
pip install -e ".[dev]"
```

### Optional Dependencies
```bash
# For telemetry support
pip install "crmadminbrasil-dataverse-sdk[telemetry]"

# For documentation
pip install "crmadminbrasil-dataverse-sdk[docs]"

# All optional dependencies
pip install "crmadminbrasil-dataverse-sdk[dev,telemetry,docs]"
```

## 🔧 Quick Start

### Basic Usage

```python
import asyncio
from dataverse_sdk import DataverseSDK

async def main():
    # Initialize SDK
    sdk = DataverseSDK(
        dataverse_url="https://yourorg.crm.dynamics.com",
        client_id="your-client-id",
        client_secret="your-client-secret",
        tenant_id="your-tenant-id",
    )
    
    async with sdk:
        # Create an account
        account_data = {
            "name": "Contoso Ltd",
            "websiteurl": "https://contoso.com",
            "telephone1": "555-0123"
        }
        account_id = await sdk.create("accounts", account_data)
        print(f"Created account: {account_id}")
        
        # Query accounts
        accounts = await sdk.query("accounts", {
            "select": ["name", "websiteurl", "telephone1"],
            "filter": "statecode eq 0",
            "top": 10
        })
        
        for account in accounts.value:
            print(f"Account: {account['name']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Environment Configuration

Create a `.env` file:
```env
DATAVERSE_URL=https://yourorg.crm.dynamics.com
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
```

The SDK automatically loads environment variables:
```python
from dataverse_sdk import DataverseSDK

# Configuration loaded from environment
sdk = DataverseSDK()
```

## 📚 Documentation

### Table of Contents
- [Authentication](#authentication)
- [CRUD Operations](#crud-operations)
- [Query Operations](#query-operations)
- [Bulk Operations](#bulk-operations)
- [FetchXML Queries](#fetchxml-queries)
- [Entity Associations](#entity-associations)
- [Metadata Operations](#metadata-operations)
- [CLI Usage](#cli-usage)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Hooks and Extensibility](#hooks-and-extensibility)
- [Performance Optimization](#performance-optimization)
- [Testing](#testing)
- [Contributing](#contributing)




## 🔐 Authentication

The SDK supports multiple authentication flows for different scenarios:

### Client Credentials Flow (Service-to-Service)
Best for server applications and automation:

```python
from dataverse_sdk import DataverseSDK

sdk = DataverseSDK(
    dataverse_url="https://yourorg.crm.dynamics.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
    tenant_id="your-tenant-id",
)

async with sdk:
    # SDK automatically uses client credentials flow
    accounts = await sdk.query("accounts", {"top": 5})
```

### Device Code Flow (CLI Applications)
Best for command-line tools and development:

```python
from dataverse_sdk.auth import DataverseAuthenticator

authenticator = DataverseAuthenticator(
    client_id="your-client-id",
    tenant_id="your-tenant-id",
    dataverse_url="https://yourorg.crm.dynamics.com",
)

# This will prompt user to visit a URL and enter a code
token = await authenticator.authenticate_device_code()
```

### Interactive Flow (Desktop Applications)
For applications with user interaction:

```python
# Interactive flow with local redirect
token = await authenticator.authenticate_interactive(
    redirect_uri="http://localhost:8080",
    port=8080
)
```

### Token Caching
The SDK automatically caches tokens to minimize authentication requests:

```python
# Tokens are cached automatically
sdk = DataverseSDK(...)

async with sdk:
    # First request authenticates and caches token
    await sdk.query("accounts", {"top": 1})
    
    # Subsequent requests use cached token
    await sdk.query("contacts", {"top": 1})
    
    # Clear cache if needed
    await sdk.clear_auth_cache()
```

## 📝 CRUD Operations

### Create Operations

```python
# Create a single entity
account_data = {
    "name": "Acme Corporation",
    "websiteurl": "https://acme.com",
    "telephone1": "555-0123",
    "description": "Leading provider of innovative solutions"
}

account_id = await sdk.create("accounts", account_data)
print(f"Created account: {account_id}")

# Create with return data
account = await sdk.create("accounts", account_data, return_record=True)
print(f"Created account: {account['name']} ({account['accountid']})")
```

### Read Operations

```python
# Read by ID
account = await sdk.read("accounts", account_id)
print(f"Account name: {account['name']}")

# Read with specific fields
account = await sdk.read(
    "accounts", 
    account_id,
    select=["name", "websiteurl", "telephone1"]
)

# Read with related entities
account = await sdk.read(
    "accounts",
    account_id,
    expand=["primarycontactid", "createdby"]
)
```

### Update Operations

```python
# Update entity
update_data = {
    "websiteurl": "https://newacme.com",
    "description": "Updated description"
}

await sdk.update("accounts", account_id, update_data)

# Update with return data
updated_account = await sdk.update(
    "accounts", 
    account_id, 
    update_data, 
    return_record=True
)
```

### Delete Operations

```python
# Delete entity
await sdk.delete("accounts", account_id)
```

### Upsert Operations

```python
# Upsert (create or update)
account_data = {
    "name": "Upsert Test Account",
    "websiteurl": "https://upsert.com"
}

result = await sdk.upsert("accounts", account_data)
if result.was_created:
    print(f"Created new account: {result.entity_id}")
else:
    print(f"Updated existing account: {result.entity_id}")

# Upsert with alternate key
result = await sdk.upsert(
    "accounts",
    account_data,
    alternate_key={"accountnumber": "ACC-001"}
)
```

## 🔍 Query Operations

### Basic Queries

```python
from dataverse_sdk.models import QueryOptions

# Simple query
accounts = await sdk.query("accounts", {
    "select": ["name", "websiteurl"],
    "top": 10
})

for account in accounts.value:
    print(f"{account['name']}: {account['websiteurl']}")

# Using QueryOptions model
options = QueryOptions(
    select=["name", "websiteurl", "telephone1"],
    filter="statecode eq 0",
    order_by=["name asc"],
    top=20
)

accounts = await sdk.query("accounts", options)
```

### Advanced Filtering

```python
# Complex filters
accounts = await sdk.query("accounts", {
    "select": ["name", "revenue"],
    "filter": "revenue gt 1000000 and statecode eq 0",
    "order_by": ["revenue desc"]
})

# String operations
accounts = await sdk.query("accounts", {
    "select": ["name"],
    "filter": "contains(name, 'Microsoft') or startswith(name, 'Contoso')"
})

# Date filtering
from datetime import datetime, timedelta

last_month = datetime.now() - timedelta(days=30)
recent_accounts = await sdk.query("accounts", {
    "select": ["name", "createdon"],
    "filter": f"createdon gt {last_month.isoformat()}"
})
```

### Pagination

```python
# Manual pagination
result = await sdk.query("accounts", {
    "select": ["name"],
    "top": 100
})

all_accounts = result.value
while result.has_more:
    # Get next page
    result = await sdk.query("accounts", {
        "select": ["name"],
        "top": 100,
        "skip": len(all_accounts)
    })
    all_accounts.extend(result.value)

# Automatic pagination
all_accounts = await sdk.query_all("accounts", {
    "select": ["name", "websiteurl"],
    "filter": "statecode eq 0"
}, max_records=1000)
```

### Related Entity Expansion

```python
# Expand related entities
accounts = await sdk.query("accounts", {
    "select": ["name", "websiteurl"],
    "expand": [
        "primarycontactid($select=fullname,emailaddress1)",
        "createdby($select=fullname)"
    ],
    "top": 10
})

for account in accounts.value:
    print(f"Account: {account['name']}")
    if account.get('primarycontactid'):
        contact = account['primarycontactid']
        print(f"  Primary Contact: {contact['fullname']}")
```

## ⚡ Bulk Operations

### Bulk Create

```python
# Prepare data
contacts = [
    {
        "firstname": "John",
        "lastname": "Doe",
        "emailaddress1": "john.doe@example.com"
    },
    {
        "firstname": "Jane",
        "lastname": "Smith",
        "emailaddress1": "jane.smith@example.com"
    },
    # ... more contacts
]

# Bulk create with automatic batching
result = await sdk.bulk_create(
    "contacts",
    contacts,
    batch_size=100,  # Process in batches of 100
    parallel=True    # Execute batches in parallel
)

print(f"Processed: {result.total_processed}")
print(f"Successful: {result.successful}")
print(f"Failed: {result.failed}")
print(f"Success rate: {result.success_rate:.1f}%")

if result.has_errors:
    print("Errors:")
    for error in result.errors[:5]:  # Show first 5 errors
        print(f"  - {error}")
```

### Bulk Update

```python
# Prepare updates (must include entity ID)
updates = [
    {
        "id": "contact-id-1",
        "jobtitle": "Senior Developer"
    },
    {
        "id": "contact-id-2", 
        "jobtitle": "Project Manager"
    },
    # ... more updates
]

result = await sdk.bulk_update("contacts", updates)
```

### Bulk Delete

```python
# Delete multiple entities
contact_ids = [
    "contact-id-1",
    "contact-id-2",
    "contact-id-3",
    # ... more IDs
]

result = await sdk.bulk_delete("contacts", contact_ids)
```

### Custom Batch Operations

```python
from dataverse_sdk.batch import BatchProcessor

# Create custom batch processor
batch_processor = BatchProcessor(
    client=sdk.client,
    default_batch_size=50,
    max_parallel_batches=3
)

# Custom operations
operations = [
    {
        "method": "POST",
        "url": "accounts",
        "body": {"name": "Account 1"}
    },
    {
        "method": "PATCH", 
        "url": "accounts(existing-id)",
        "body": {"description": "Updated"}
    },
    {
        "method": "DELETE",
        "url": "accounts(delete-id)"
    }
]

result = await batch_processor.execute_bulk_operation(
    operations,
    parallel=True,
    transactional=False
)
```

## 📊 FetchXML Queries

### Basic FetchXML

```python
# Execute FetchXML string
fetchxml = """
<fetch top="10">
    <entity name="account">
        <attribute name="name" />
        <attribute name="websiteurl" />
        <attribute name="telephone1" />
        <filter type="and">
            <condition attribute="statecode" operator="eq" value="0" />
            <condition attribute="revenue" operator="gt" value="1000000" />
        </filter>
        <order attribute="revenue" descending="true" />
    </entity>
</fetch>
"""

accounts = await sdk.fetch_xml(fetchxml)
for account in accounts:
    print(f"{account['name']}: {account.get('revenue', 'N/A')}")
```

### FetchXML with Linked Entities

```python
fetchxml = """
<fetch top="5">
    <entity name="account">
        <attribute name="name" />
        <attribute name="websiteurl" />
        <link-entity name="contact" from="parentcustomerid" to="accountid" alias="contact">
            <attribute name="fullname" />
            <attribute name="emailaddress1" />
            <filter type="and">
                <condition attribute="statecode" operator="eq" value="0" />
            </filter>
        </link-entity>
        <filter type="and">
            <condition attribute="statecode" operator="eq" value="0" />
        </filter>
    </entity>
</fetch>
"""

results = await sdk.fetch_xml(fetchxml)
```

### FetchXML Builder (Programmatic)

```python
from dataverse_sdk.models import FetchXMLQuery

# Build FetchXML programmatically
query = FetchXMLQuery(
    entity="account",
    attributes=["name", "websiteurl", "revenue"],
    filters=[{
        "type": "and",
        "conditions": [
            {"attribute": "statecode", "operator": "eq", "value": "0"},
            {"attribute": "revenue", "operator": "gt", "value": "1000000"}
        ]
    }],
    orders=[
        {"attribute": "revenue", "descending": True}
    ],
    top=10
)

# Convert to FetchXML and execute
fetchxml_string = query.to_fetchxml()
accounts = await sdk.fetch_xml(fetchxml_string)
```

## 🔗 Entity Associations

### Associate Entities

```python
# Associate account with contact
await sdk.associate(
    primary_entity_type="accounts",
    primary_entity_id=account_id,
    relationship_name="account_primary_contact",
    related_entity_type="contacts",
    related_entity_id=contact_id
)

# Many-to-many association
await sdk.associate(
    primary_entity_type="systemusers",
    primary_entity_id=user_id,
    relationship_name="systemuserroles_association",
    related_entity_type="roles",
    related_entity_id=role_id
)
```

### Disassociate Entities

```python
# Remove association
await sdk.disassociate(
    primary_entity_type="accounts",
    primary_entity_id=account_id,
    relationship_name="account_primary_contact"
)

# Remove specific many-to-many association
await sdk.disassociate(
    primary_entity_type="systemusers",
    primary_entity_id=user_id,
    relationship_name="systemuserroles_association",
    related_entity_id=role_id
)
```

## 🔍 Metadata Operations

### Entity Metadata

```python
# Get entity metadata
account_metadata = await sdk.get_entity_metadata("account")

print(f"Display Name: {account_metadata['DisplayName']['UserLocalizedLabel']['Label']}")
print(f"Logical Name: {account_metadata['LogicalName']}")
print(f"Primary Key: {account_metadata['PrimaryIdAttribute']}")
print(f"Primary Name: {account_metadata['PrimaryNameAttribute']}")

# List all attributes
for attr in account_metadata['Attributes']:
    print(f"  {attr['LogicalName']}: {attr['AttributeType']}")
```

### Attribute Metadata

```python
# Get specific attribute metadata
name_attr = await sdk.get_attribute_metadata("account", "name")

print(f"Display Name: {name_attr['DisplayName']['UserLocalizedLabel']['Label']}")
print(f"Type: {name_attr['AttributeType']}")
print(f"Max Length: {name_attr.get('MaxLength', 'N/A')}")
print(f"Required: {name_attr['RequiredLevel']['Value']}")
```

### Generate Entity Models

```python
# Generate Pydantic models from metadata (utility function)
from dataverse_sdk.utils import generate_entity_model

# This would generate a Pydantic model class
AccountModel = await generate_entity_model(sdk, "account")

# Use the generated model
account_data = {
    "name": "Test Account",
    "websiteurl": "https://test.com"
}

# Validate data with the model
account = AccountModel(**account_data)
```


## 🖥️ CLI Usage

The SDK includes a powerful command-line interface for all operations:

### Installation and Setup

```bash
# Install the SDK
pip install crmadminbrasil-dataverse-sdk

# Initialize configuration
dv-cli config init
# Follow prompts to enter your Dataverse URL, Client ID, etc.

# Test connection
dv-cli config test
```

### Entity Operations

```bash
# List entities
dv-cli entity list accounts --select name,websiteurl --top 10
dv-cli entity list contacts --filter "statecode eq 0" --order-by createdon

# Get specific entity
dv-cli entity get accounts 12345678-1234-1234-1234-123456789012

# Create entity
dv-cli entity create accounts --file account_data.json
echo '{"name": "CLI Test Account"}' | dv-cli entity create accounts

# Update entity
dv-cli entity update accounts 12345678-1234-1234-1234-123456789012 --file updates.json

# Delete entity
dv-cli entity delete accounts 12345678-1234-1234-1234-123456789012 --yes
```

### Bulk Operations

```bash
# Bulk create from JSON file
dv-cli bulk create contacts --file contacts.json --batch-size 100

# Bulk operations with progress
dv-cli bulk create accounts --file large_accounts.json --parallel
```

### Data Export/Import

```bash
# Export data
dv-cli data export accounts --output accounts_backup.json
dv-cli data export contacts --filter "statecode eq 0" --select firstname,lastname,emailaddress1

# Import data
dv-cli data import accounts --file accounts_backup.json
```

### FetchXML Operations

```bash
# Execute FetchXML from file
dv-cli fetchxml execute --file complex_query.xml

# Save FetchXML results
dv-cli fetchxml execute --file query.xml --output results.json
```

### Configuration Management

```bash
# View current configuration
dv-cli config show

# Update configuration
dv-cli config set dataverse_url https://neworg.crm.dynamics.com
dv-cli config set log_level DEBUG

# Use different config file
dv-cli --config-file prod-config.json entity list accounts
```

### Output Formats

```bash
# Table format (default)
dv-cli entity list accounts --top 5

# JSON format
dv-cli entity list accounts --top 5 --output json

# Save to file
dv-cli entity list accounts --output json > accounts.json
```

## ⚙️ Configuration

### Environment Variables

```bash
# Required
export DATAVERSE_URL="https://yourorg.crm.dynamics.com"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_TENANT_ID="your-tenant-id"

# Optional
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_AUTHORITY="https://login.microsoftonline.com/your-tenant-id"
export AZURE_SCOPE="https://yourorg.crm.dynamics.com/.default"

# SDK Configuration
export MAX_CONNECTIONS=100
export MAX_RETRIES=3
export DEFAULT_BATCH_SIZE=100
export LOG_LEVEL=INFO
```

### Configuration File

Create `dataverse-config.json`:

```json
{
  "dataverse_url": "https://yourorg.crm.dynamics.com",
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "tenant_id": "your-tenant-id",
  "max_connections": 100,
  "max_retries": 3,
  "default_batch_size": 100,
  "log_level": "INFO"
}
```

### Programmatic Configuration

```python
from dataverse_sdk import DataverseSDK
from dataverse_sdk.utils import Config

# Custom configuration
config = Config(
    max_connections=50,
    max_retries=5,
    default_batch_size=200,
    connect_timeout=15.0,
    read_timeout=60.0,
    debug=True
)

sdk = DataverseSDK(
    dataverse_url="https://yourorg.crm.dynamics.com",
    client_id="your-client-id",
    client_secret="your-client-secret", 
    tenant_id="your-tenant-id",
    config=config
)
```

### Multi-Environment Setup

```python
# Development environment
dev_sdk = DataverseSDK(
    dataverse_url="https://dev-org.crm.dynamics.com",
    client_id="dev-client-id",
    client_secret="dev-client-secret",
    tenant_id="dev-tenant-id"
)

# Production environment
prod_sdk = DataverseSDK(
    dataverse_url="https://prod-org.crm.dynamics.com",
    client_id="prod-client-id",
    client_secret="prod-client-secret",
    tenant_id="prod-tenant-id"
)

# Use different configurations
async def sync_data():
    async with dev_sdk as dev, prod_sdk as prod:
        # Get data from dev
        dev_accounts = await dev.query_all("accounts", {"select": ["name"]})
        
        # Create in prod
        await prod.bulk_create("accounts", dev_accounts)
```

## 🚨 Error Handling

### Exception Types

```python
from dataverse_sdk.exceptions import (
    DataverseSDKError,          # Base exception
    AuthenticationError,        # Authentication failures
    AuthorizationError,         # Permission issues
    ConnectionError,            # Network connectivity
    TimeoutError,              # Request timeouts
    RateLimitError,            # Rate limiting
    ValidationError,           # Data validation
    EntityNotFoundError,       # Entity not found
    APIError,                  # API errors
    BatchOperationError,       # Batch operation failures
)

# Specific error handling
try:
    account = await sdk.read("accounts", "invalid-id")
except EntityNotFoundError as e:
    print(f"Account not found: {e.entity_id}")
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
    print(f"Error details: {e.response_data}")
```

### Retry and Rate Limiting

```python
from dataverse_sdk.exceptions import RateLimitError
import asyncio

async def robust_operation():
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        try:
            result = await sdk.query("accounts", {"top": 1000})
            return result
            
        except RateLimitError as e:
            attempt += 1
            if attempt >= max_attempts:
                raise
            
            # Wait for the suggested retry time
            wait_time = e.retry_after or 60
            print(f"Rate limited. Waiting {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            
        except ConnectionError as e:
            attempt += 1
            if attempt >= max_attempts:
                raise
            
            # Exponential backoff for connection errors
            wait_time = 2 ** attempt
            print(f"Connection error. Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
```

### Comprehensive Error Handling

```python
async def safe_bulk_operation(entities):
    try:
        result = await sdk.bulk_create("accounts", entities)
        
        if result.has_errors:
            print(f"Bulk operation completed with {result.failed} errors:")
            for error in result.errors:
                print(f"  - {error}")
        
        return result
        
    except BatchOperationError as e:
        print(f"Batch operation failed: {e.message}")
        print(f"Failed operations: {len(e.failed_operations)}")
        
        # Retry failed operations individually
        for failed_op in e.failed_operations:
            try:
                await sdk.create("accounts", failed_op["data"])
            except Exception as retry_error:
                print(f"Retry failed: {retry_error}")
                
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
```

## 🔌 Hooks and Extensibility

### Built-in Hooks

```python
from dataverse_sdk.hooks import (
    HookType,
    logging_hook,
    telemetry_hook,
    retry_logging_hook
)

# Register built-in hooks
sdk.register_hook(HookType.BEFORE_REQUEST, logging_hook)
sdk.register_hook(HookType.AFTER_RESPONSE, telemetry_hook)
sdk.register_hook(HookType.ON_RETRY, retry_logging_hook)
```

### Custom Hooks

```python
from dataverse_sdk.hooks import HookContext, HookType

def custom_request_hook(context: HookContext) -> None:
    """Custom hook to modify requests."""
    if context.hook_type == HookType.BEFORE_REQUEST:
        # Add custom headers
        context.request_data["headers"]["X-Custom-Header"] = "MyValue"
        
        # Log request details
        print(f"Making request to: {context.request_data['url']}")

def custom_response_hook(context: HookContext) -> None:
    """Custom hook to process responses."""
    if context.hook_type == HookType.AFTER_RESPONSE:
        # Log response time
        response_time = context.metadata.get("response_time", 0)
        print(f"Request completed in {response_time:.2f}s")
        
        # Store metrics
        context.set_custom_data("response_time", response_time)

# Register custom hooks
sdk.register_hook(HookType.BEFORE_REQUEST, custom_request_hook, priority=10)
sdk.register_hook(HookType.AFTER_RESPONSE, custom_response_hook)
```

### Async Hooks

```python
async def async_telemetry_hook(context: HookContext) -> None:
    """Async hook for telemetry."""
    if context.hook_type == HookType.AFTER_RESPONSE:
        # Send telemetry data asynchronously
        telemetry_data = {
            "url": context.request_data["url"],
            "method": context.request_data["method"],
            "status_code": context.response_data["status_code"],
            "response_time": context.metadata.get("response_time")
        }
        
        # Send to telemetry service (example)
        await send_telemetry(telemetry_data)

# Register async hook
sdk.register_hook(HookType.AFTER_RESPONSE, async_telemetry_hook)
```

### Hook Decorators

```python
from dataverse_sdk.hooks import hook, HookType

@hook(HookType.BEFORE_REQUEST, priority=5)
def request_validator(context: HookContext) -> None:
    """Validate requests before sending."""
    url = context.request_data["url"]
    method = context.request_data["method"]
    
    # Custom validation logic
    if method == "DELETE" and "accounts" in url:
        print("Warning: Deleting account!")

@hook(HookType.ON_ERROR)
def error_notifier(context: HookContext) -> None:
    """Notify on errors."""
    error = context.error
    url = context.request_data["url"]
    
    # Send notification (example)
    send_error_notification(f"Error in {url}: {error}")
```

### OpenTelemetry Integration

```python
from opentelemetry import trace
from dataverse_sdk.hooks import HookContext, HookType

tracer = trace.get_tracer(__name__)

def opentelemetry_hook(context: HookContext) -> None:
    """OpenTelemetry integration hook."""
    if context.hook_type == HookType.BEFORE_REQUEST:
        # Start span
        span = tracer.start_span(f"dataverse_{context.request_data['method']}")
        span.set_attribute("http.url", context.request_data["url"])
        span.set_attribute("http.method", context.request_data["method"])
        context.set_custom_data("span", span)
        
    elif context.hook_type == HookType.AFTER_RESPONSE:
        # End span
        span = context.get_custom_data("span")
        if span:
            span.set_attribute("http.status_code", context.response_data["status_code"])
            span.end()

# Register OpenTelemetry hook
sdk.register_hook(HookType.BEFORE_REQUEST, opentelemetry_hook)
sdk.register_hook(HookType.AFTER_RESPONSE, opentelemetry_hook)
```


## ⚡ Performance Optimization

### Connection Pooling

```python
from dataverse_sdk.utils import Config

# Optimize connection settings
config = Config(
    max_connections=200,           # Total connection pool size
    max_keepalive_connections=50,  # Keep-alive connections
    keepalive_expiry=30,          # Keep-alive timeout (seconds)
    connect_timeout=10.0,         # Connection timeout
    read_timeout=30.0,            # Read timeout
)

sdk = DataverseSDK(config=config)
```

### Batch Size Optimization

```python
# Optimize batch sizes based on data size
small_records = [...]  # Small records
large_records = [...]  # Records with many fields

# Use larger batches for small records
await sdk.bulk_create("contacts", small_records, batch_size=500)

# Use smaller batches for large records
await sdk.bulk_create("accounts", large_records, batch_size=50)
```

### Parallel Processing

```python
import asyncio

async def parallel_queries():
    # Execute multiple queries in parallel
    tasks = [
        sdk.query("accounts", {"select": ["name"], "top": 100}),
        sdk.query("contacts", {"select": ["fullname"], "top": 100}),
        sdk.query("opportunities", {"select": ["name"], "top": 100}),
    ]
    
    results = await asyncio.gather(*tasks)
    accounts, contacts, opportunities = results
    
    return {
        "accounts": accounts.value,
        "contacts": contacts.value,
        "opportunities": opportunities.value
    }

# Execute parallel queries
data = await parallel_queries()
```

### Memory-Efficient Streaming

```python
async def process_large_dataset():
    """Process large datasets efficiently."""
    page_size = 1000
    processed_count = 0
    
    # Process in chunks to avoid memory issues
    options = QueryOptions(
        select=["accountid", "name"],
        top=page_size
    )
    
    while True:
        result = await sdk.query("accounts", options)
        
        if not result.value:
            break
            
        # Process current batch
        for account in result.value:
            # Process individual account
            await process_account(account)
            processed_count += 1
        
        # Check for more data
        if not result.has_more:
            break
            
        # Update options for next page
        options.skip = processed_count
    
    print(f"Processed {processed_count} accounts")
```

### Caching Strategies

```python
from functools import lru_cache
import asyncio

class CachedDataverseSDK:
    def __init__(self, sdk):
        self.sdk = sdk
        self._metadata_cache = {}
    
    @lru_cache(maxsize=100)
    async def get_cached_entity_metadata(self, entity_type: str):
        """Cache entity metadata to avoid repeated API calls."""
        if entity_type not in self._metadata_cache:
            metadata = await self.sdk.get_entity_metadata(entity_type)
            self._metadata_cache[entity_type] = metadata
        
        return self._metadata_cache[entity_type]
    
    async def bulk_create_with_validation(self, entity_type: str, entities: list):
        """Bulk create with cached metadata validation."""
        # Get cached metadata
        metadata = await self.get_cached_entity_metadata(entity_type)
        
        # Validate entities against metadata
        validated_entities = []
        for entity in entities:
            if self._validate_entity(entity, metadata):
                validated_entities.append(entity)
        
        # Bulk create validated entities
        return await self.sdk.bulk_create(entity_type, validated_entities)

# Use cached SDK
cached_sdk = CachedDataverseSDK(sdk)
```

## 🧪 Testing

### Unit Tests

```python
import pytest
from unittest.mock import AsyncMock, patch
from dataverse_sdk import DataverseSDK

@pytest.mark.asyncio
async def test_account_creation():
    """Test account creation."""
    sdk = DataverseSDK(
        dataverse_url="https://test.crm.dynamics.com",
        client_id="test-client",
        tenant_id="test-tenant"
    )
    
    # Mock the create method
    sdk.create = AsyncMock(return_value="12345678-1234-1234-1234-123456789012")
    
    account_data = {"name": "Test Account"}
    account_id = await sdk.create("accounts", account_data)
    
    assert account_id == "12345678-1234-1234-1234-123456789012"
    sdk.create.assert_called_once_with("accounts", account_data)

@pytest.mark.asyncio
async def test_query_with_filter():
    """Test query with filter."""
    sdk = DataverseSDK(
        dataverse_url="https://test.crm.dynamics.com",
        client_id="test-client",
        tenant_id="test-tenant"
    )
    
    # Mock query response
    mock_response = {
        "value": [{"accountid": "123", "name": "Test Account"}],
        "@odata.count": 1
    }
    
    with patch.object(sdk, 'query', return_value=mock_response):
        result = await sdk.query("accounts", {"filter": "name eq 'Test'"})
        assert len(result["value"]) == 1
        assert result["value"][0]["name"] == "Test Account"
```

### Integration Tests

```python
import pytest
import os
from dataverse_sdk import DataverseSDK

# Skip if no credentials
pytestmark = pytest.mark.skipif(
    not os.getenv("DATAVERSE_URL"),
    reason="Integration tests require Dataverse credentials"
)

@pytest.fixture
async def sdk():
    """SDK fixture for integration tests."""
    sdk_instance = DataverseSDK()
    async with sdk_instance as sdk:
        yield sdk

@pytest.mark.asyncio
async def test_real_account_operations(sdk):
    """Test real account operations."""
    # Create test account
    account_data = {
        "name": "Integration Test Account",
        "description": "Created by integration test"
    }
    
    account_id = await sdk.create("accounts", account_data)
    
    try:
        # Read account
        account = await sdk.read("accounts", account_id)
        assert account["name"] == account_data["name"]
        
        # Update account
        await sdk.update("accounts", account_id, {"description": "Updated"})
        
        # Verify update
        updated_account = await sdk.read("accounts", account_id)
        assert updated_account["description"] == "Updated"
        
    finally:
        # Clean up
        await sdk.delete("accounts", account_id)
```

### Performance Tests

```python
import pytest
import time
from dataverse_sdk import DataverseSDK

@pytest.mark.slow
@pytest.mark.asyncio
async def test_bulk_operation_performance(sdk):
    """Test bulk operation performance."""
    # Create test data
    test_contacts = [
        {"firstname": f"Test{i}", "lastname": "Contact"}
        for i in range(100)
    ]
    
    start_time = time.time()
    
    # Bulk create
    result = await sdk.bulk_create("contacts", test_contacts)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Performance assertions
    assert duration < 30.0  # Should complete within 30 seconds
    assert result.success_rate > 90.0  # At least 90% success rate
    
    print(f"Bulk created {result.successful} contacts in {duration:.2f}s")
```

### Running Tests

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run unit tests
pytest tests/unit/

# Run integration tests (requires credentials)
pytest tests/integration/

# Run with coverage
pytest --cov=dataverse_sdk --cov-report=html

# Run performance tests
pytest -m slow

# Run specific test
pytest tests/unit/test_auth.py::TestDataverseAuthenticator::test_client_credentials
```

## 📚 Advanced Examples

### Data Migration Script

```python
import asyncio
from dataverse_sdk import DataverseSDK

async def migrate_accounts():
    """Migrate accounts from one environment to another."""
    
    # Source environment
    source_sdk = DataverseSDK(
        dataverse_url="https://source.crm.dynamics.com",
        client_id="source-client-id",
        client_secret="source-secret",
        tenant_id="source-tenant"
    )
    
    # Target environment
    target_sdk = DataverseSDK(
        dataverse_url="https://target.crm.dynamics.com",
        client_id="target-client-id",
        client_secret="target-secret",
        tenant_id="target-tenant"
    )
    
    async with source_sdk as source, target_sdk as target:
        # Export accounts from source
        print("Exporting accounts from source...")
        accounts = await source.query_all("accounts", {
            "select": ["name", "websiteurl", "telephone1", "description"],
            "filter": "statecode eq 0"
        })
        
        print(f"Found {len(accounts)} accounts to migrate")
        
        # Import to target
        print("Importing accounts to target...")
        result = await target.bulk_create("accounts", accounts, batch_size=100)
        
        print(f"Migration completed:")
        print(f"  Successful: {result.successful}")
        print(f"  Failed: {result.failed}")
        print(f"  Success rate: {result.success_rate:.1f}%")

if __name__ == "__main__":
    asyncio.run(migrate_accounts())
```

### Data Synchronization

```python
import asyncio
from datetime import datetime, timedelta
from dataverse_sdk import DataverseSDK

class DataSynchronizer:
    def __init__(self, primary_sdk, secondary_sdk):
        self.primary = primary_sdk
        self.secondary = secondary_sdk
    
    async def sync_entity(self, entity_type: str, sync_field: str = "modifiedon"):
        """Sync entities based on modification date."""
        
        # Get last sync time (stored somewhere)
        last_sync = await self.get_last_sync_time(entity_type)
        
        # Query modified records from primary
        filter_expr = f"{sync_field} gt {last_sync.isoformat()}"
        modified_records = await self.primary.query_all(entity_type, {
            "filter": filter_expr,
            "order_by": [f"{sync_field} asc"]
        })
        
        if not modified_records:
            print(f"No modified {entity_type} found")
            return
        
        print(f"Syncing {len(modified_records)} modified {entity_type}")
        
        # Upsert to secondary (assuming alternate key exists)
        for record in modified_records:
            try:
                await self.secondary.upsert(
                    entity_type,
                    record,
                    alternate_key={"name": record["name"]}  # Adjust key as needed
                )
            except Exception as e:
                print(f"Failed to sync {record.get('name', 'unknown')}: {e}")
        
        # Update last sync time
        await self.update_last_sync_time(entity_type, datetime.now())
    
    async def get_last_sync_time(self, entity_type: str) -> datetime:
        """Get last sync time (implement based on your storage)."""
        # This could be stored in a database, file, or Dataverse itself
        return datetime.now() - timedelta(hours=1)  # Default to 1 hour ago
    
    async def update_last_sync_time(self, entity_type: str, sync_time: datetime):
        """Update last sync time (implement based on your storage)."""
        pass

async def run_sync():
    primary_sdk = DataverseSDK(...)  # Primary environment
    secondary_sdk = DataverseSDK(...)  # Secondary environment
    
    async with primary_sdk as primary, secondary_sdk as secondary:
        synchronizer = DataSynchronizer(primary, secondary)
        
        # Sync different entity types
        await synchronizer.sync_entity("accounts")
        await synchronizer.sync_entity("contacts")
        await synchronizer.sync_entity("opportunities")

if __name__ == "__main__":
    asyncio.run(run_sync())
```

### Custom Entity Manager

```python
from dataverse_sdk import DataverseSDK
from dataverse_sdk.models import Entity
from typing import List, Optional

class EntityManager:
    """High-level entity manager with business logic."""
    
    def __init__(self, sdk: DataverseSDK):
        self.sdk = sdk
    
    async def create_account_with_contacts(
        self,
        account_data: dict,
        contacts_data: List[dict]
    ) -> dict:
        """Create account with associated contacts."""
        
        # Create account
        account_id = await self.sdk.create("accounts", account_data)
        
        try:
            # Create contacts and associate with account
            contact_ids = []
            for contact_data in contacts_data:
                contact_data["parentcustomerid@odata.bind"] = f"accounts({account_id})"
                contact_id = await self.sdk.create("contacts", contact_data)
                contact_ids.append(contact_id)
            
            return {
                "account_id": account_id,
                "contact_ids": contact_ids,
                "success": True
            }
            
        except Exception as e:
            # Rollback: delete account if contact creation fails
            try:
                await self.sdk.delete("accounts", account_id)
            except:
                pass  # Ignore rollback errors
            
            raise e
    
    async def get_account_summary(self, account_id: str) -> dict:
        """Get comprehensive account summary."""
        
        # Get account with related data
        account = await self.sdk.read("accounts", account_id, expand=[
            "primarycontactid($select=fullname,emailaddress1)",
            "account_parent_account($select=name)",
            "contact_customer_accounts($select=fullname,emailaddress1;$top=5)"
        ])
        
        # Get additional statistics
        contact_count_result = await self.sdk.query("contacts", {
            "filter": f"parentcustomerid eq '{account_id}'",
            "count": True,
            "top": 0  # Just get count
        })
        
        opportunity_count_result = await self.sdk.query("opportunities", {
            "filter": f"customerid eq '{account_id}'",
            "count": True,
            "top": 0
        })
        
        return {
            "account": account,
            "contact_count": contact_count_result.total_count,
            "opportunity_count": opportunity_count_result.total_count,
            "primary_contact": account.get("primarycontactid"),
            "parent_account": account.get("account_parent_account"),
            "recent_contacts": account.get("contact_customer_accounts", [])
        }

# Usage
async def main():
    sdk = DataverseSDK(...)
    
    async with sdk:
        manager = EntityManager(sdk)
        
        # Create account with contacts
        result = await manager.create_account_with_contacts(
            account_data={"name": "Acme Corp", "websiteurl": "https://acme.com"},
            contacts_data=[
                {"firstname": "John", "lastname": "Doe", "emailaddress1": "john@acme.com"},
                {"firstname": "Jane", "lastname": "Smith", "emailaddress1": "jane@acme.com"}
            ]
        )
        
        # Get account summary
        summary = await manager.get_account_summary(result["account_id"])
        print(f"Account: {summary['account']['name']}")
        print(f"Contacts: {summary['contact_count']}")
        print(f"Opportunities: {summary['opportunity_count']}")
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/crmadminbrasil-dataverse-sdk/crmadminbrasil-dataverse-sdk.git
cd crmadminbrasil-dataverse-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
black dataverse_sdk/
isort dataverse_sdk/
flake8 dataverse_sdk/
mypy dataverse_sdk/
```

### Code Style

We use several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **bandit**: Security analysis

### Testing Guidelines

- Write tests for all new features
- Maintain test coverage above 90%
- Include both unit and integration tests
- Use descriptive test names and docstrings

### Documentation

- Update README.md for new features
- Add docstrings to all public methods
- Include type hints for all parameters and return values
- Provide usage examples

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Microsoft Dataverse team for the excellent API
- The Python async community for inspiration
- All contributors who help improve this SDK

## 📞 Support

- **Documentation**: [https://crmadminbrasil-dataverse-sdk.readthedocs.io](https://crmadminbrasil-dataverse-sdk.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/crmadminbrasil-dataverse-sdk/crmadminbrasil-dataverse-sdk/issues)
- **Discussions**: [GitHub Discussions](https://github.com/crmadminbrasil-dataverse-sdk/crmadminbrasil-dataverse-sdk/discussions)
- **Email**: support@crmadminbrasil-dataverse-sdk.com

## 🗺️ Roadmap

### Version 1.1
- [ ] WebSocket support for real-time notifications
- [ ] Enhanced FetchXML builder with GUI
- [ ] Plugin system for custom entity types
- [ ] Performance monitoring dashboard

### Version 1.2
- [ ] GraphQL-style query interface
- [ ] Built-in data validation rules
- [ ] Advanced caching strategies
- [ ] Multi-tenant management tools

### Version 2.0
- [ ] Support for Dataverse for Teams
- [ ] AI-powered query optimization
- [ ] Visual query builder
- [ ] Enterprise governance features

---

**Made with ❤️ by the Dataverse SDK Team**



## ⚡ **Performance & Benchmarks**

O SDK foi projetado para ser extremamente performático, capaz de lidar com milhões de registros em uso diário:

### **Configurações Otimizadas**
- **Batch Size**: > 100 registros por lote (padrão: 500)
- **Paralelismo**: Até 32 operações simultâneas
- **Pool de Conexões**: 100 conexões simultâneas
- **Throughput**: > 1000 registros/segundo

### **Testes de Performance**
```bash
# Executar benchmarks de performance
cd benchmarks/
pip install -r requirements.txt
python benchmark_bulk_create.py

# Stress test com milhões de registros
python stress_test.py
```

### **Resultados Típicos**
- ✅ **Criação em massa**: 1000+ registros/segundo
- ✅ **Consultas**: < 100ms para consultas simples
- ✅ **Bulk operations**: 10000+ registros/minuto
- ✅ **Memória**: < 500MB para 100k registros

## 📁 **Estrutura do Projeto**

```
dataverse-sdk/
├── 📦 dataverse_sdk/          # Código principal do SDK
├── 🖥️ cli/                    # Interface de linha de comando
├── 🧪 tests/                  # Testes unitários e integração
├── 📚 examples/               # Exemplos de uso
├── ⚡ benchmarks/             # Testes de performance
├── 🔧 scripts/                # Scripts utilitários
├── 📖 docs/                   # Documentação completa
│   ├── getting-started/       # Guias iniciais
│   ├── guides/                # Guias avançados
│   ├── tutorials/             # Tutoriais
│   ├── api-reference/         # Referência da API
│   ├── contributing/          # Guias de contribuição
│   ├── deployment/            # Guias de deployment
│   └── jekyll/                # Site GitHub Pages
└── 🤖 .github/               # Configurações GitHub
```

## 🔗 **Links da Documentação**

- **[📖 Documentação Completa](docs/)** - Toda a documentação organizada
- **[🚀 Início Rápido](docs/getting-started/quickstart.md)** - Primeiros passos
- **[🏢 Configuração Corporativa](docs/deployment/CORPORATE_SETUP_GUIDE.md)** - Para ambientes empresariais
- **[⚡ Benchmarks](benchmarks/)** - Testes de performance
- **[🤝 Contribuição](docs/contributing/CONTRIBUTING.md)** - Como contribuir
- **[📋 API Reference](docs/api-reference/dataverse-sdk.md)** - Documentação técnica

