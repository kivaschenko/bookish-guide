# Timeline Editing Server

Visual interface for editing B-roll timelines in StoryForge projects with enhanced productivity features.

## Features

### Core Functionality
- **Visual timeline editor** - Intuitive interface for B-roll selection
- **Multiple B-roll alternatives** - Choose between up to 3 B-roll options per segment
- **Image overlay support** - Drag-and-drop custom images to replace B-rolls
- **Live audio preview** - Play through your timeline with synchronized audio
- **Auto-save** - Changes saved automatically to `broll_timing.json`
- **Thumbnail zoom** - Click to enlarge B-roll previews for better inspection

### Enhanced Features (New)
- **📊 Statistics Dashboard** - Real-time stats showing:
  - Total bullets/segments
  - Alternative B-rolls usage count
  - Image overlays count
  - Duplicate B-roll warnings
  
- **⚠️ Smart Duplicate Detection**:
  - Visual badges showing "Used Nx" on duplicated B-rolls
  - Clickable badges to see WHERE duplicates are used
  - Jump to any duplicate location with one click
  - Confirmation dialog when selecting already-used B-rolls
  - Red overlay warning on unselected duplicates

- **⌨️ Keyboard Shortcuts**:
  - `Space` - Play/pause audio preview
  - `1/2/3` - Select B-roll alternatives (1st/2nd/3rd)
  - `↑/↓` - Navigate between bullet groups
  
- **✓ Visual Feedback**:
  - Save status indicator with timestamp
  - Success/error notifications
  - Auto-fade after 5 seconds

- **🔍 Data Validation**:
  - Automatic validation on timeline load
  - Checks for required fields, time validity, alternatives
  - Detailed statistics logged to console

### Security
- HTTP Basic Authentication (optional, configured in `config.yml`)

## Quick Start

### 1. Prepare Your Data

Your project should have a `broll_timing.json` file with this structure:

```json
[
  {
    "rush": "audio/bullet_001.mp3",
    "broll": "b-roll/video-1.mp4",
    "broll2": "b-roll/video-2.mp4",
    "broll3": "b-roll/video-3.mp4",
    "phrase": "Your narration text here",
    "start_time": 0.0,
    "end_time": 5.5,
    "image": "optional-overlay.png"
  }
]
```

**File locations:**
```bash
# Option A: Project-specific (recommended)
projects/YOUR_PROJECT/temp/broll_timing.json
projects/YOUR_PROJECT/audio/bullet_*.mp3

# Option B: Language-specific projects
projects/YOUR_PROJECT/LANGUAGE/temp/broll_timing.json
projects/YOUR_PROJECT/LANGUAGE/audio/bullet_*.mp3

# Option C: Root temp directory
temp/broll_timing.json
audio/bullet_*.mp3
```

### 2. Start the Server

```bash
# Using a specific project (recommended)
python editing_server/server.py --project my-project-06

# Using a custom temp directory path
python editing_server/server.py --temp projects/my-project-06/temp

# Using default temp directory (temp/)
python editing_server/server.py

# Custom port
python editing_server/server.py --project my-project-06 --port 8080
```

### 3. Access the Interface

Open your browser and navigate to:
```
http://localhost:47393
```

The interface loads automatically with:
- ✅ Timeline data validation
- ✅ Statistics dashboard populated
- ✅ Duplicate detection active
- ✅ Keyboard shortcuts enabled

## Using the Interface

### Selecting B-rolls

**Method 1: Radio Buttons**
- Click on the radio button below each B-roll thumbnail
- Selection is saved automatically
- Duplicate warning appears if B-roll is already used elsewhere

**Method 2: Keyboard Shortcuts**
1. Click anywhere in a bullet's container
2. Press `1`, `2`, or `3` to select first/second/third alternative

### Viewing Duplicates

When a B-roll is used multiple times:
1. **Badge appears** - "Used Nx" in red on the thumbnail
2. **Click the badge** - Opens modal showing all usage locations
3. **Jump to location** - Click any bullet in the modal to scroll to it
4. **Red overlay** - Shows on unselected duplicate alternatives as a warning

### Audio Preview

1. Click **"🎵 Preview audio"** button to start playback
2. Current bullet group is highlighted in blue
3. Press `Space` to pause/resume
4. Use `↑/↓` arrows to navigate between bullets

### Image Overlays

**Adding an overlay:**
- Drag and drop an image onto the drop zone (right side)
- Or click the drop zone to browse for an image

**Removing an overlay:**
- Click the **"❌ Remove"** button on the overlay thumbnail

### Statistics Dashboard

Located at the top of the page, showing:
- **📝 Total Bullets** - Number of timeline segments
- **🎬 Using Alternatives** - Count using broll2 or broll3
- **🖼️ Image Overlays** - Count of custom overlays
- **⚠️ Duplicate B-rolls** - Number of B-rolls used multiple times

Updates automatically as you make changes.

## Configuration

Edit `config.yml` to configure authentication:

```yaml
dashboard:
  auth:
    enabled: false  # Set to true to require login
    username: admin
    password: your_password_here
```

## File Structure

```
editing_server/
├── server.py           # HTTP server with validation and file serving
├── interface.html      # Web UI with enhanced features
├── __init__.py        # Package initialization
└── ROADMAP.md         # Development roadmap and future features
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve the timeline editing interface |
| `/api/timeline` | GET | Get timeline data with validation |
| `/api/update_timeline` | POST | Save timeline changes |
| `/api/upload` | POST | Upload custom images for overlays |
| `/b-roll/*` | GET | Serve B-roll files (videos and thumbnails) |
| `/projects/*` | GET | Serve project files (audio, images) |
| `/audio/*` | GET | Serve audio files |

### Validation on Load

When `/api/timeline` is called:
- ✅ Validates all required fields (rush, broll, phrase, times)
- ✅ Checks time ranges (start < end, no negatives)
- ✅ Counts alternatives and image overlays
- ✅ Logs statistics: "📊 Timeline Stats: X entries, Y with alternatives, Z with images"

### Placeholder Images

If a B-roll thumbnail is missing:
- Server automatically generates an SVG placeholder
- Shows "B-roll not found" message
- Prevents 404 errors in browser console

## Dependencies

- **Python 3.8+** (Python 3.13+ compatible)
- **PyYAML** - Configuration file parsing
- **Standard library only** - No external web frameworks required

### Python 3.13+ Compatibility

✅ Fully compatible with Python 3.13+
- Removed deprecated `cgi` module
- Custom multipart form parsing implementation
- Uses only non-deprecated standard library modules

## Keyboard Shortcuts Reference

| Key | Action |
|-----|--------|
| `Space` | Play/pause audio preview |
| `1` | Select first B-roll alternative |
| `2` | Select second B-roll alternative |
| `3` | Select third B-roll alternative |
| `↑` | Navigate to previous bullet group |
| `↓` | Navigate to next bullet group |

*Note: Shortcuts are disabled when typing in input fields*

## Logging

Server logs are written to `/tmp/editor_server.log`:
- **DEBUG**: File requests, B-roll serving, placeholder generation
- **INFO**: Validation results, statistics, timeline changes
- **WARNING**: Missing files, validation errors

Example log output:
```
📊 Timeline Stats: 100 entries, 100 with alternatives, 7 with images
📁 Project: my-project-06, Language: N/A
📹 Requested B-roll file: real-estate-home-keys-close-up.jpg
📦 Serving placeholder for missing B-roll
```

## Troubleshooting

**Issue: B-roll thumbnails not showing**
- Check that `.jpg` files exist in `b-roll/` directory
- Placeholder SVGs will be served automatically for missing files

**Issue: Audio not playing**
- Verify audio files exist in `audio/` subdirectory of project
- Check that `rush` field in JSON matches actual audio filename

**Issue: Duplicate warnings for every B-roll**
- This is expected if the same B-roll is intentionally used multiple times
- Use confirmation dialog to proceed with duplicate selection

**Issue: Statistics not updating**
- Refresh the page to reload timeline data
- Check browser console for JavaScript errors

## Default Settings

- **Port**: 47393 (customizable with `--port`)
- **Host**: 0.0.0.0 (accessible from network)
- **Authentication**: Disabled by default
- **Log file**: `/tmp/editor_server.log`
- **Log level**: DEBUG

## Integration

The server can be integrated with the main StoryForge dashboard:

```python
from editing_server import start_editor_for_project

# Start editor for a specific project
start_editor_for_project(config={'paths': {'temp': 'projects/my-project-06/temp'}})
```

See `ROADMAP.md` for planned dashboard integration features.