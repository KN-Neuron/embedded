"""File system watcher for automatic synchronization."""

import time
from datetime import datetime
from pathlib import Path

from rich.console import Console
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .adapters.base import StorageBackend
from .config import config_manager
from .utils import check_file_stability, generate_remote_path, is_xml_file

console = Console()


class XMLFileHandler(FileSystemEventHandler):
    """Handler for XML file creation events."""
    
    def __init__(self, storage_backend: StorageBackend, user_identifier: str):
        """
        Initialize handler.
        
        Args:
            storage_backend: Storage backend to use for uploads
            user_identifier: User identifier for remote path generation
        """
        super().__init__()
        self.storage_backend = storage_backend
        self.user_identifier = user_identifier
        self.processed_files = set()  # Track processed files to avoid duplicates
    
    def on_created(self, event):
        """Handle file creation events."""
        if event.is_directory:
            return
        
        filepath = event.src_path
        
        # Only process XML files
        if not is_xml_file(filepath):
            return
        
        # Avoid processing the same file multiple times
        if filepath in self.processed_files:
            return
        
        console.print(f"[yellow]Detected new file: {Path(filepath).name}[/yellow]")
        
        # Wait for file to be completely written
        console.print("[dim]Waiting for file to stabilize...[/dim]")
        if not check_file_stability(filepath):
            console.print(f"[red]File {filepath} is unstable or was removed. Skipping.[/red]")
            return
        
        # Mark as processed
        self.processed_files.add(filepath)
        
        # Generate remote path
        filename = Path(filepath).name
        remote_path = generate_remote_path(filename, self.user_identifier)
        
        # Upload file
        console.print(f"[cyan]Uploading to: {remote_path}[/cyan]")
        if self.storage_backend.upload(filepath, remote_path):
            console.print(f"[green]✓ Successfully uploaded: {filename}[/green]")
        else:
            console.print(f"[red]✗ Failed to upload: {filename}[/red]")
            # Remove from processed files so it can be retried
            self.processed_files.discard(filepath)


class FileWatcher:
    """File system watcher for XML files."""
    
    def __init__(self, storage_backend: StorageBackend, watch_folder: str, user_identifier: str):
        """
        Initialize file watcher.
        
        Args:
            storage_backend: Storage backend to use for uploads
            watch_folder: Folder to watch for new files
            user_identifier: User identifier for remote path generation
        """
        self.storage_backend = storage_backend
        self.watch_folder = watch_folder
        self.user_identifier = user_identifier
        self.observer = Observer()
    
    def start(self):
        """Start watching for file changes."""
        # Ensure watch folder exists
        Path(self.watch_folder).mkdir(parents=True, exist_ok=True)
        
        # Create event handler
        event_handler = XMLFileHandler(self.storage_backend, self.user_identifier)
        
        # Schedule observer
        self.observer.schedule(event_handler, self.watch_folder, recursive=True)
        self.observer.start()
        
        console.print(f"[green]Started watching folder: {self.watch_folder}[/green]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop watching for file changes."""
        self.observer.stop()
        self.observer.join()
        console.print("[yellow]Stopped watching[/yellow]")


def start_watcher():
    """Start the file watcher with configuration from config manager."""
    config = config_manager.get()
    if config is None:
        console.print("[red]Configuration not found. Run 'storage init' first.[/red]")
        return
    
    from .utils import get_storage
    
    storage = get_storage()
    if storage is None:
        return
    
    watcher = FileWatcher(
        storage_backend=storage,
        watch_folder=config.local_watch_folder,
        user_identifier=config.user_identifier
    )
    
    watcher.start()
