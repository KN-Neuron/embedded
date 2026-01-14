"""CLI commands for storage tool."""

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from .config import StorageConfig, config_manager
from .utils import format_size, generate_remote_path, get_storage, is_xml_file
from .watcher import start_watcher

console = Console()
app = typer.Typer()


@app.command()
def init():
    """Initialize storage configuration interactively."""
    console.print("[bold cyan]Storage CLI Configuration[/bold cyan]\n")
    
    # Gather configuration from user
    bucket_name = Prompt.ask("Enter bucket name")
    endpoint_url = Prompt.ask("Enter endpoint URL (e.g., accountid.r2.cloudflarestorage.com)")
    access_key = Prompt.ask("Enter access key")
    secret_key = Prompt.ask("Enter secret key", password=True)
    local_watch_folder = Prompt.ask("Enter local watch folder path", default=str(Path.home() / "measurements"))
    user_identifier = Prompt.ask("Enter user identifier")
    
    # Expand user path
    local_watch_folder = os.path.expanduser(local_watch_folder)
    
    # Create configuration object
    config = StorageConfig(
        bucket_name=bucket_name,
        endpoint_url=endpoint_url,
        access_key=access_key,
        secret_key=secret_key,
        local_watch_folder=local_watch_folder,
        user_identifier=user_identifier
    )
    
    # Save configuration
    if config_manager.save(config):
        console.print(f"\n[green]✓ Configuration saved to {config_manager.config_path}[/green]")
    else:
        console.print("\n[red]✗ Failed to save configuration[/red]")
        raise typer.Exit(1)
    
    # Validate connection
    console.print("\n[cyan]Validating connection...[/cyan]")
    from .adapters.minio import MinioBackend
    
    backend = MinioBackend(
        endpoint_url=config.endpoint_url,
        access_key=config.access_key,
        secret_key=config.secret_key,
        bucket_name=config.bucket_name,
        secure=config.secure
    )
    
    if backend.validate_connection():
        console.print("[green]✓ Connection validated successfully![/green]")
    else:
        console.print("[red]✗ Connection validation failed. Please check your credentials.[/red]")
        raise typer.Exit(1)


@app.command()
def push(file_path: str):
    """Upload a specific file to storage."""
    storage = get_storage()
    if storage is None:
        raise typer.Exit(1)
    
    config = config_manager.get()
    if not os.path.exists(file_path):
        console.print(f"[red]File not found: {file_path}[/red]")
        raise typer.Exit(1)
    
    if not is_xml_file(file_path):
        console.print("[red]Only XML files are supported[/red]")
        raise typer.Exit(1)
    
    filename = Path(file_path).name
    remote_path = generate_remote_path(filename, config.user_identifier)
    
    console.print(f"[cyan]Uploading {filename} to {remote_path}...[/cyan]")
    
    if storage.upload(file_path, remote_path):
        console.print(f"[green]✓ Successfully uploaded: {filename}[/green]")
    else:
        console.print(f"[red]✗ Failed to upload: {filename}[/red]")
        raise typer.Exit(1)


@app.command()
def pull(
    user: Optional[str] = typer.Option(None, help="Filter by user identifier"),
    all: bool = typer.Option(False, "--all", help="Sync all missing files")
):
    """Download files from storage."""
    storage = get_storage()
    if storage is None:
        raise typer.Exit(1)
    
    config = config_manager.get()
    
    # Determine prefix
    prefix = "embedded/"
    if user:
        prefix += f"{user}/"
    
    console.print(f"[cyan]Fetching file list from storage...[/cyan]")
    files = storage.list_files(prefix)
    
    if not files:
        console.print("[yellow]No files found in storage[/yellow]")
        return
    
    # Filter for missing files
    download_folder = Path(config.local_watch_folder) / "downloaded"
    download_folder.mkdir(parents=True, exist_ok=True)
    
    to_download = []
    for file_meta in files:
        local_path = download_folder / Path(file_meta.name).name
        if not local_path.exists():
            to_download.append(file_meta)
    
    if not to_download:
        console.print("[green]All files are already downloaded[/green]")
        return
    
    console.print(f"[yellow]Found {len(to_download)} missing file(s)[/yellow]")
    
    if not all:
        # Ask for confirmation
        if not typer.confirm(f"Download {len(to_download)} file(s)?"):
            console.print("[yellow]Download cancelled[/yellow]")
            return
    
    # Download files
    success_count = 0
    for file_meta in to_download:
        local_path = download_folder / Path(file_meta.name).name
        console.print(f"[cyan]Downloading {Path(file_meta.name).name}...[/cyan]")
        
        if storage.download(file_meta.name, str(local_path)):
            console.print(f"[green]✓ Downloaded: {Path(file_meta.name).name}[/green]")
            success_count += 1
        else:
            console.print(f"[red]✗ Failed: {Path(file_meta.name).name}[/red]")
    
    console.print(f"\n[green]Downloaded {success_count}/{len(to_download)} file(s)[/green]")


@app.command()
def list(
    user: Optional[str] = typer.Option(None, help="Filter by user identifier")
):
    """List files in storage."""
    storage = get_storage()
    if storage is None:
        raise typer.Exit(1)
    
    # Determine prefix
    prefix = "embedded/"
    if user:
        prefix += f"{user}/"
    
    console.print(f"[cyan]Fetching file list from storage...[/cyan]")
    files = storage.list_files(prefix)
    
    if not files:
        console.print("[yellow]No files found in storage[/yellow]")
        return
    
    # Create table
    table = Table(title=f"Files in Storage ({len(files)} total)")
    table.add_column("Filename", style="cyan", no_wrap=True)
    table.add_column("User", style="magenta")
    table.add_column("Date", style="green")
    table.add_column("Size", style="yellow", justify="right")
    
    for file_meta in files:
        table.add_row(
            Path(file_meta.name).name,
            file_meta.user_identifier,
            file_meta.year_month,
            format_size(file_meta.size)
        )
    
    console.print(table)


@app.command()
def watch():
    """Start watching local folder for new files and auto-upload."""
    if not config_manager.exists():
        console.print("[red]Configuration not found. Run 'storage init' first.[/red]")
        raise typer.Exit(1)
    
    start_watcher()


if __name__ == "__main__":
    app()
