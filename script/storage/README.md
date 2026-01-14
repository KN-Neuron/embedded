# Storage CLI - Measurement Data Sync Tool

A lightweight Python CLI tool for synchronizing `.xml` measurement files to Cloudflare R2 (S3-compatible storage) using the `minio` library.

## Features

- 🔄 **Auto-sync**: Watch a local folder and automatically upload new XML files
- ☁️ **Cloud Storage**: Sync to Cloudflare R2 (S3-compatible)
- 📁 **Organized Structure**: Files are stored as `embedded/{user}/{year}/{month}/{filename}`
- 🔍 **File Stability**: Ensures files are completely written before uploading
- 📊 **List & Filter**: View all files with filtering by user
- ⬇️ **Pull**: Download missing files from storage
- 🎨 **Rich UI**: Beautiful terminal output with colors and tables

## Installation

1. Navigate to the script directory:
```bash
cd /home/denis/Code/Neuron/embedded/script
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Initialize Configuration

Run the initialization command to set up your credentials:

```bash
python -m storage.main init
```

You'll be prompted to enter:
- Bucket name
- Endpoint URL (e.g., `accountid.r2.cloudflarestorage.com`)
- Access key
- Secret key
- Local watch folder path (default: `~/measurements`)
- User identifier

The configuration is saved to `~/.storage/config.yaml`.

### 2. Start Watching for New Files

To automatically upload new XML files as they're created:

```bash
python -m storage.main watch
```

This will:
- Monitor your local watch folder
- Detect new `.xml` files
- Wait for files to finish writing (stability check)
- Automatically upload to R2 storage
- Organize files by user/year/month

Press `Ctrl+C` to stop watching.

### 3. Manual Upload

To upload a specific file:

```bash
python -m storage.main push /path/to/file.xml
```

### 4. List Files in Storage

View all files in storage:

```bash
python -m storage.main list
```

Filter by user:

```bash
python -m storage.main list --user john_doe
```

### 5. Download Files

Download all missing files:

```bash
python -m storage.main pull --all
```

Download files for a specific user:

```bash
python -m storage.main pull --user john_doe
```

Files are downloaded to `{local_watch_folder}/downloaded/`.

## Commands Reference

| Command | Description | Options |
|---------|-------------|---------|
| `init` | Initialize configuration | None |
| `watch` | Start auto-sync daemon | None |
| `push <file>` | Upload a specific file | None |
| `pull` | Download missing files | `--user <username>`, `--all` |
| `list` | List files in storage | `--user <username>` |

## Architecture

```
script/storage/
├── __init__.py           # Package init
├── main.py              # Entry point
├── commands.py          # CLI commands (Typer)
├── config.py            # Configuration manager (Pydantic)
├── watcher.py           # File system watcher (Watchdog)
├── utils.py             # Helper functions
└── adapters/            # Storage abstraction layer
    ├── __init__.py
    ├── base.py          # Abstract base class
    └── minio.py         # Minio/R2 implementation
```

### Design Principles

- **Lightweight**: No complex DI frameworks, just simple function arguments
- **Clean Abstraction**: Storage backend is abstracted but not over-engineered
- **Type Safe**: Full type hinting with Python's typing module
- **Error Handling**: Graceful error handling with informative messages
- **Rich UI**: Colored output for better UX

## Storage Structure

Files are organized in R2 as:

```
embedded/
  {user_identifier}/
    {year}/
      {month}/
        measurement_001.xml
        measurement_002.xml
```

Example:
```
embedded/john_doe/2026/01/experiment_20260107.xml
```

## Configuration File

The configuration is stored at `~/.storage/config.yaml`:

```yaml
access_key: YOUR_ACCESS_KEY
bucket_name: measurements
endpoint_url: accountid.r2.cloudflarestorage.com
local_watch_folder: /home/user/measurements
secret_key: YOUR_SECRET_KEY
secure: true
user_identifier: john_doe
```

## File Stability Check

The watcher implements a smart stability check:
- Monitors file size over 1-second intervals
- Only uploads when size is stable (file write complete)
- Prevents uploading partially written files
- Maximum 5 checks before assuming stable

## Troubleshooting

### Connection Failed

If `init` fails to validate connection:
1. Check your endpoint URL format
2. Verify access key and secret key
3. Ensure the endpoint is reachable
4. Check if bucket name contains valid characters

### Files Not Auto-Uploading

1. Ensure `watch` command is running
2. Check that files are `.xml` format
3. Verify the watch folder path is correct
4. Check terminal output for error messages

### Permission Errors

Ensure you have:
- Read access to the watch folder
- Write access to `~/.storage/`
- Network access to R2 endpoint

## Requirements

- Python 3.10+
- Dependencies:
  - `typer[all]>=0.9.0` - CLI framework
  - `rich>=13.0.0` - Terminal formatting
  - `minio>=7.2.0` - S3 client
  - `watchdog>=3.0.0` - File system monitoring
  - `pydantic>=2.0.0` - Configuration validation
  - `pyyaml>=6.0.0` - YAML parsing

## License

Internal tool for KN-Neuron embedded team.

## Support

For issues or questions, contact the embedded team.
