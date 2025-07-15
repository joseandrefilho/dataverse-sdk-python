#!/usr/bin/env python3
"""
Command Line Interface for the Dataverse SDK.

This CLI provides a comprehensive set of commands for interacting with
Microsoft Dataverse environments, including CRUD operations, bulk processing,
data export/import, and administrative tasks.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich import print as rprint

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dataverse_sdk import DataverseSDK
from dataverse_sdk.exceptions import DataverseSDKError
from dataverse_sdk.models import QueryOptions, FetchXMLQuery


# Initialize Typer app and Rich console
app = typer.Typer(
    name="dv-cli",
    help="Microsoft Dataverse SDK Command Line Interface",
    add_completion=False,
)
console = Console()


# Global configuration
class CLIConfig:
    def __init__(self):
        self.dataverse_url: Optional[str] = None
        self.client_id: Optional[str] = None
        self.client_secret: Optional[str] = None
        self.tenant_id: Optional[str] = None
        self.config_file: Optional[Path] = None
        self.output_format: str = "table"
        self.verbose: bool = False


cli_config = CLIConfig()


def load_config(config_file: Optional[Path] = None) -> None:
    """Load configuration from file or environment."""
    # Try to load from specified config file or default locations
    config_paths = []
    
    if config_file:
        config_paths.append(config_file)
    
    # Add default config file locations
    config_paths.extend([
        Path("dataverse-config.json"),  # Current directory
        Path.home() / ".dataverse-config.json",  # Home directory
        Path.home() / ".config" / "dataverse" / "config.json",  # XDG config
    ])
    
    # Try to load from the first existing config file
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config_data = json.load(f)
                
                cli_config.dataverse_url = config_data.get("dataverse_url")
                cli_config.client_id = config_data.get("client_id")
                cli_config.client_secret = config_data.get("client_secret")
                cli_config.tenant_id = config_data.get("tenant_id")
                
                if cli_config.verbose:
                    console.print(f"[dim]Loaded configuration from {config_path}[/dim]")
                break
            except (json.JSONDecodeError, IOError) as e:
                if cli_config.verbose:
                    console.print(f"[yellow]Warning: Could not load config from {config_path}: {e}[/yellow]")
                continue
    
    # Override with environment variables (they take precedence)
    cli_config.dataverse_url = os.getenv("DATAVERSE_URL", cli_config.dataverse_url)
    cli_config.client_id = os.getenv("AZURE_CLIENT_ID", cli_config.client_id)
    cli_config.client_secret = os.getenv("AZURE_CLIENT_SECRET", cli_config.client_secret)
    cli_config.tenant_id = os.getenv("AZURE_TENANT_ID", cli_config.tenant_id)


def validate_config() -> None:
    """Validate that required configuration is present."""
    missing = []
    
    if not cli_config.dataverse_url:
        missing.append("dataverse_url")
    if not cli_config.client_id:
        missing.append("client_id")
    if not cli_config.tenant_id:
        missing.append("tenant_id")
    
    if missing:
        console.print(f"[red]Missing required configuration: {', '.join(missing)}[/red]")
        console.print("Please set environment variables or use --config-file option.")
        raise typer.Exit(1)


def create_sdk() -> DataverseSDK:
    """Create and return configured SDK instance."""
    return DataverseSDK(
        dataverse_url=cli_config.dataverse_url,
        client_id=cli_config.client_id,
        client_secret=cli_config.client_secret,
        tenant_id=cli_config.tenant_id,
    )


def format_output(data: Any, format_type: str = "table") -> None:
    """Format and display output data."""
    if format_type == "json":
        console.print_json(json.dumps(data, indent=2, default=str))
    elif format_type == "table" and isinstance(data, list) and data:
        # Create table for list of records
        table = Table()
        
        # Add columns based on first record
        first_record = data[0]
        for key in first_record.keys():
            table.add_column(key, style="cyan")
        
        # Add rows
        for record in data:
            row = [str(record.get(key, "")) for key in first_record.keys()]
            table.add_row(*row)
        
        console.print(table)
    else:
        # Fallback to simple print
        console.print(data)


# Global options callback
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    config_file: Optional[Path] = typer.Option(
        None,
        "--config-file",
        "-c",
        help="Configuration file path",
    ),
    output_format: str = typer.Option(
        "table",
        "--output",
        "-o",
        help="Output format (table, json)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version information",
    ),
) -> None:
    """Microsoft Dataverse SDK CLI."""
    cli_config.config_file = config_file
    cli_config.output_format = output_format
    cli_config.verbose = verbose
    
    if version:
        show_version()
        raise typer.Exit()
    
    # If no command is provided, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()
    
    load_config(config_file)


def show_version() -> None:
    """Display version information."""
    try:
        # Try to get version from installed package
        import pkg_resources
        try:
            version = pkg_resources.get_distribution("crmadminbrasil-dataverse-sdk").version
        except pkg_resources.DistributionNotFound:
            # Fallback to reading from pyproject.toml if in development
            import tomllib
            pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    pyproject_data = tomllib.load(f)
                version = pyproject_data.get("project", {}).get("version", "unknown")
            else:
                version = "unknown"
    except ImportError:
        # If tomllib is not available (Python < 3.11), try tomli
        try:
            import tomli
            pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    pyproject_data = tomli.load(f)
                version = pyproject_data.get("project", {}).get("version", "unknown")
            else:
                version = "unknown"
        except ImportError:
            version = "unknown"
    
    console.print(f"[bold blue]Dataverse SDK CLI[/bold blue]")
    console.print(f"Version: [green]{version}[/green]")
    console.print(f"Package: [cyan]crmadminbrasil-dataverse-sdk[/cyan]")
    
    # Show additional system information if verbose
    if cli_config.verbose:
        import platform
        import sys
        console.print(f"\n[dim]System Information:[/dim]")
        console.print(f"Python: {sys.version}")
        console.print(f"Platform: {platform.platform()}")
        console.print(f"Architecture: {platform.architecture()[0]}")


# Add version command as well
@app.command("version")
def version_command() -> None:
    """Show version information."""
    show_version()


# Configuration commands
config_app = typer.Typer(name="config", help="Configuration management")
app.add_typer(config_app)


@config_app.command("init")
def config_init(
    dataverse_url: str = typer.Option(..., prompt=True, help="Dataverse URL"),
    client_id: str = typer.Option(..., prompt=True, help="Azure AD Client ID"),
    tenant_id: str = typer.Option(..., prompt=True, help="Azure AD Tenant ID"),
    client_secret: str = typer.Option(
        None,
        prompt=True,
        hide_input=True,
        help="Azure AD Client Secret (optional)",
    ),
    output_file: Path = typer.Option(
        Path("dataverse-config.json"),
        "--output",
        "-o",
        help="Output configuration file",
    ),
) -> None:
    """Initialize configuration file."""
    config_data = {
        "dataverse_url": dataverse_url,
        "client_id": client_id,
        "tenant_id": tenant_id,
    }
    
    if client_secret:
        config_data["client_secret"] = client_secret
    
    with open(output_file, "w") as f:
        json.dump(config_data, f, indent=2)
    
    console.print(f"[green]Configuration saved to {output_file}[/green]")


@config_app.command("test")
def config_test() -> None:
    """Test configuration and connection."""
    validate_config()
    
    async def test_connection():
        try:
            sdk = create_sdk()
            async with sdk:
                # Try to get organization info
                result = await sdk.client.get("organizations")
                console.print("[green]✓ Connection successful[/green]")
                
                if result.get("value"):
                    org = result["value"][0]
                    console.print(f"Organization: {org.get('name', 'Unknown')}")
                    console.print(f"Version: {org.get('version', 'Unknown')}")
        
        except Exception as e:
            console.print(f"[red]✗ Connection failed: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(test_connection())


# Entity commands
entity_app = typer.Typer(name="entity", help="Entity operations")
app.add_typer(entity_app)


@entity_app.command("list")
def entity_list(
    entity_type: str = typer.Argument(..., help="Entity logical name"),
    select: Optional[str] = typer.Option(None, "--select", help="Fields to select (comma-separated)"),
    filter: Optional[str] = typer.Option(None, "--filter", help="OData filter expression"),
    order_by: Optional[str] = typer.Option(None, "--order-by", help="Order by fields (comma-separated)"),
    top: Optional[int] = typer.Option(None, "--top", help="Maximum number of records"),
    all_records: bool = typer.Option(False, "--all", help="Retrieve all records (ignore pagination)"),
) -> None:
    """List entities with optional filtering and sorting."""
    validate_config()
    
    async def list_entities():
        try:
            sdk = create_sdk()
            async with sdk:
                options = QueryOptions()
                
                if select:
                    options.select = [s.strip() for s in select.split(",")]
                if filter:
                    options.filter = filter
                if order_by:
                    options.order_by = [o.strip() for o in order_by.split(",")]
                if top:
                    options.top = top
                
                if all_records:
                    entities = await sdk.query_all(entity_type, options)
                else:
                    result = await sdk.query(entity_type, options)
                    entities = result.value
                
                if entities:
                    format_output(entities, cli_config.output_format)
                    console.print(f"\n[green]Found {len(entities)} records[/green]")
                else:
                    console.print("[yellow]No records found[/yellow]")
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(list_entities())


@entity_app.command("get")
def entity_get(
    entity_type: str = typer.Argument(..., help="Entity logical name"),
    entity_id: str = typer.Argument(..., help="Entity ID"),
    select: Optional[str] = typer.Option(None, "--select", help="Fields to select (comma-separated)"),
    expand: Optional[str] = typer.Option(None, "--expand", help="Related entities to expand (comma-separated)"),
) -> None:
    """Get a specific entity by ID."""
    validate_config()
    
    async def get_entity():
        try:
            sdk = create_sdk()
            async with sdk:
                select_fields = [s.strip() for s in select.split(",")] if select else None
                expand_fields = [e.strip() for e in expand.split(",")] if expand else None
                
                entity = await sdk.read(entity_type, entity_id, select_fields, expand_fields)
                format_output(entity, cli_config.output_format)
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(get_entity())


@entity_app.command("create")
def entity_create(
    entity_type: str = typer.Argument(..., help="Entity logical name"),
    data_file: Optional[Path] = typer.Option(None, "--file", "-f", help="JSON file with entity data"),
    return_record: bool = typer.Option(False, "--return", help="Return created record"),
) -> None:
    """Create a new entity."""
    validate_config()
    
    # Get entity data
    if data_file:
        if not data_file.exists():
            console.print(f"[red]File not found: {data_file}[/red]")
            raise typer.Exit(1)
        
        with open(data_file) as f:
            entity_data = json.load(f)
    else:
        # Interactive input
        console.print("Enter entity data (JSON format):")
        data_input = typer.prompt("Data")
        try:
            entity_data = json.loads(data_input)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON: {e}[/red]")
            raise typer.Exit(1)
    
    async def create_entity():
        try:
            sdk = create_sdk()
            async with sdk:
                result = await sdk.create(entity_type, entity_data, return_record)
                
                if return_record:
                    format_output(result, cli_config.output_format)
                else:
                    console.print(f"[green]Entity created with ID: {result}[/green]")
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(create_entity())


@entity_app.command("update")
def entity_update(
    entity_type: str = typer.Argument(..., help="Entity logical name"),
    entity_id: str = typer.Argument(..., help="Entity ID"),
    data_file: Optional[Path] = typer.Option(None, "--file", "-f", help="JSON file with update data"),
    return_record: bool = typer.Option(False, "--return", help="Return updated record"),
) -> None:
    """Update an existing entity."""
    validate_config()
    
    # Get update data
    if data_file:
        if not data_file.exists():
            console.print(f"[red]File not found: {data_file}[/red]")
            raise typer.Exit(1)
        
        with open(data_file) as f:
            update_data = json.load(f)
    else:
        # Interactive input
        console.print("Enter update data (JSON format):")
        data_input = typer.prompt("Data")
        try:
            update_data = json.loads(data_input)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON: {e}[/red]")
            raise typer.Exit(1)
    
    async def update_entity():
        try:
            sdk = create_sdk()
            async with sdk:
                result = await sdk.update(entity_type, entity_id, update_data, return_record)
                
                if return_record:
                    format_output(result, cli_config.output_format)
                else:
                    console.print("[green]Entity updated successfully[/green]")
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(update_entity())


@entity_app.command("delete")
def entity_delete(
    entity_type: str = typer.Argument(..., help="Entity logical name"),
    entity_id: str = typer.Argument(..., help="Entity ID"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Delete an entity."""
    validate_config()
    
    if not confirm:
        if not Confirm.ask(f"Are you sure you want to delete {entity_type}({entity_id})?"):
            console.print("Operation cancelled")
            return
    
    async def delete_entity():
        try:
            sdk = create_sdk()
            async with sdk:
                await sdk.delete(entity_type, entity_id)
                console.print("[green]Entity deleted successfully[/green]")
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(delete_entity())


# Bulk operations commands
bulk_app = typer.Typer(name="bulk", help="Bulk operations")
app.add_typer(bulk_app)


@bulk_app.command("create")
def bulk_create(
    entity_type: str = typer.Argument(..., help="Entity logical name"),
    data_file: Path = typer.Option(..., "--file", "-f", help="JSON file with entities data"),
    batch_size: Optional[int] = typer.Option(None, "--batch-size", help="Batch size"),
    parallel: bool = typer.Option(True, "--parallel/--sequential", help="Execute batches in parallel"),
) -> None:
    """Bulk create entities from JSON file."""
    validate_config()
    
    if not data_file.exists():
        console.print(f"[red]File not found: {data_file}[/red]")
        raise typer.Exit(1)
    
    with open(data_file) as f:
        entities_data = json.load(f)
    
    if not isinstance(entities_data, list):
        console.print("[red]Data file must contain a JSON array of entities[/red]")
        raise typer.Exit(1)
    
    async def bulk_create_entities():
        try:
            sdk = create_sdk()
            async with sdk:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task(f"Creating {len(entities_data)} entities...", total=None)
                    
                    result = await sdk.bulk_create(
                        entity_type, entities_data, batch_size, parallel
                    )
                    
                    progress.update(task, completed=True)
                
                console.print(f"[green]Bulk create completed[/green]")
                console.print(f"Total processed: {result.total_processed}")
                console.print(f"Successful: {result.successful}")
                console.print(f"Failed: {result.failed}")
                console.print(f"Success rate: {result.success_rate:.1f}%")
                
                if result.has_errors and cli_config.verbose:
                    console.print("\n[red]Errors:[/red]")
                    for error in result.errors[:5]:  # Show first 5 errors
                        console.print(f"  - {error}")
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(bulk_create_entities())


# FetchXML commands
fetchxml_app = typer.Typer(name="fetchxml", help="FetchXML operations")
app.add_typer(fetchxml_app)


@fetchxml_app.command("execute")
def fetchxml_execute(
    fetchxml_file: Path = typer.Option(..., "--file", "-f", help="FetchXML file"),
) -> None:
    """Execute FetchXML query from file."""
    validate_config()
    
    if not fetchxml_file.exists():
        console.print(f"[red]File not found: {fetchxml_file}[/red]")
        raise typer.Exit(1)
    
    with open(fetchxml_file) as f:
        fetchxml_content = f.read()
    
    async def execute_fetchxml():
        try:
            sdk = create_sdk()
            async with sdk:
                entities = await sdk.fetch_xml(fetchxml_content)
                
                if entities:
                    format_output(entities, cli_config.output_format)
                    console.print(f"\n[green]Found {len(entities)} records[/green]")
                else:
                    console.print("[yellow]No records found[/yellow]")
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(execute_fetchxml())


# Export/Import commands
data_app = typer.Typer(name="data", help="Data export/import operations")
app.add_typer(data_app)


@data_app.command("export")
def data_export(
    entity_type: str = typer.Argument(..., help="Entity logical name"),
    output_file: Path = typer.Option(..., "--output", "-o", help="Output JSON file"),
    select: Optional[str] = typer.Option(None, "--select", help="Fields to select (comma-separated)"),
    filter: Optional[str] = typer.Option(None, "--filter", help="OData filter expression"),
) -> None:
    """Export entity data to JSON file."""
    validate_config()
    
    async def export_data():
        try:
            sdk = create_sdk()
            async with sdk:
                options = QueryOptions()
                
                if select:
                    options.select = [s.strip() for s in select.split(",")]
                if filter:
                    options.filter = filter
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                ) as progress:
                    task = progress.add_task("Exporting data...", total=None)
                    
                    entities = await sdk.query_all(entity_type, options)
                    
                    progress.update(task, completed=True)
                
                with open(output_file, "w") as f:
                    json.dump(entities, f, indent=2, default=str)
                
                console.print(f"[green]Exported {len(entities)} records to {output_file}[/green]")
        
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(export_data())


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()

