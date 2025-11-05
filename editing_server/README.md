# Timeline Editing Server

Visual interface for editing B-roll timelines in StoryForge projects.

## Features

- Visual timeline editor with drag-and-drop B-roll selection
- Image upload functionality for custom overlays  
- Live audio preview with timeline synchronization
- Auto-save to `broll_timing.json`
- Thumbnail zoom for better B-roll inspection
- HTTP Basic Authentication (optional)

## Usage

### Start the server:
```bash
cd editing_server/
python server.py
```

### Access the interface:
- Open http://localhost:47393 in your browser
- Edit timelines for projects in `temp/broll_timing.json`
- Upload custom images to `b-roll/ressources/`

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

- Python 3.8+
- PyYAML (for configuration)
- Standard library only (no external dependencies)

## Port

Default port: 47393 (can be changed in server startup)