# Timeline Editing Server

Visual interface for editing B-roll timelines in StoryForge projects.

## Features

- Visual timeline editor with drag-and-drop B-roll selection
- Choose between multiple B-roll alternatives for each segment
- Image upload functionality for custom overlays  
- Live audio preview with timeline synchronization
- Auto-save to `broll_timing.json`
- Thumbnail zoom for better B-roll inspection
- HTTP Basic Authentication (optional)

## Quick Start

### 1. Prepare Your Data

```bash
# Option A: Use an example for testing
cp "temp/examples/project 9 broll_timing.json" temp/broll_timing.json

# Option B: Use a specific project
# Ensure your project has: projects/YOUR_PROJECT/temp/broll_timing.json
```

### 2. Start the Server

```bash
# Using default temp directory (temp/broll_timing.json)
python editing_server/server.py

# Using a specific project
python editing_server/server.py --project my-project-06

# Using a custom temp directory path
python editing_server/server.py --temp projects/my-project-06/temp

# Custom port
python editing_server/server.py --port 8080
```

### 3. Access the Interface

Open your browser and navigate to:
```
http://localhost:47393
```

The interface will load your B-roll timeline automatically.

## Configuration

Authentication can be configured in `config.yml`:

```yaml
dashboard:
  auth:
    enabled: false  # Set to true to enable auth
    username: admin
    password: admin
```

## Files Structure

- `server.py` - Main HTTP server
- `interface.html` - Web interface for timeline editing
- `__init__.py` - Package initialization

## API Endpoints

- `GET /` - Serve the timeline editing interface
- `GET /api/timeline` - Get timeline data (broll_timing.json)
- `POST /api/update_timeline` - Save timeline changes
- `POST /api/upload` - Upload custom images
- `GET /b-roll/*` - Serve B-roll files for preview
- `GET /projects/*` - Serve project files

## Dependencies

- Python 3.8+ (Python 3.13+ compatible)
- PyYAML (for configuration)
- Standard library only (no external dependencies)

### Python 3.13+ Compatibility

The server has been updated to remove the deprecated `cgi` module, which is slated for removal in Python 3.13. Multipart form data parsing is now handled using a custom implementation that relies only on non-deprecated standard library modules.

## Port

Default port: 47393 (can be changed in server startup)