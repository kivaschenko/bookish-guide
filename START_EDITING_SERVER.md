# 🎬 Editing Server - Quick Start Guide

## ✅ Server Status: WORKING

The editing server has been successfully migrated from the legacy code and is fully functional.

## 🚀 How to Start

### Option 1: Default Location (Recommended for Testing)

```bash
# Copy an example file first
cp "temp/examples/project 9 broll_timing.json" temp/broll_timing.json

# Start the server
python editing_server/server.py
```

### Option 2: Use a Specific Project

```bash
# Start server pointing to a project
python editing_server/server.py --project my-project-06
```

### Option 3: Custom Path

```bash
# Specify custom temp directory
python editing_server/server.py --temp projects/my-project-06/temp
```

## 🌐 Access the Interface

Once the server is running, open your browser to:

**http://localhost:47393**

You'll see:
- ✅ Timeline of all B-roll segments
- ✅ Audio playback with visual synchronization
- ✅ Multiple B-roll choices (principal, alternative 1, alternative 2)
- ✅ Image upload for custom overlays
- ✅ Auto-save functionality

## 📋 Command Line Options

```bash
python editing_server/server.py [OPTIONS]

Options:
  --project NAME   Use projects/NAME/temp/broll_timing.json
  --temp PATH      Use custom path to temp directory
  --port PORT      Custom port (default: 47393)
  --help           Show help message
```

## 🎯 Features

### 1. B-roll Selection
- Click radio buttons to choose between:
  - **Principale**: Main B-roll
  - **Alternative**: Second B-roll option
  - **Alternative 2**: Third B-roll option
- Changes are saved automatically

### 2. Image Overlays
- Drag and drop images onto the "Ajouter" zone
- Or click to browse and select an image
- Images are overlaid on top of the B-roll video

### 3. Audio Preview
- Click "🎵 Prévisualiser l'audio" button
- Audio plays at 1.5x speed
- Timeline scrolls automatically to current segment
- Active segment is highlighted

### 4. Visual Zoom
- Click any B-roll thumbnail to zoom in
- Click again to zoom out
- Helps inspect B-roll details

## 🔧 Troubleshooting

### "broll_timing.json not found"
```bash
# Make sure you have the file in the right location:
ls -la temp/broll_timing.json

# Or copy an example:
cp "temp/examples/project 9 broll_timing.json" temp/broll_timing.json
```

### Port already in use
```bash
# Use a different port:
python editing_server/server.py --port 8080
```

### Can't see B-roll thumbnails
- Ensure B-roll files are in `b-roll/` directory
- Thumbnails should have same name as video: `video.mp4` → `video.jpg`

## 📝 Notes

- Server runs on `0.0.0.0:47393` (accessible from network)
- Authentication is disabled by default
- To enable auth: edit `config.yml` → `dashboard.auth.enabled: true`
- Changes are auto-saved to `broll_timing.json`

## 🎓 Migration Complete

This server is based on the legacy "premontage" server but has been:
- ✅ Migrated to `editing_server/` directory
- ✅ Updated with command-line options
- ✅ Integrated with project structure
- ✅ Documented and tested

The original legacy code can be found in:
`legacy_code_and_examples/premontage (new name _ editing server)-20251104T085151Z-1-001/`
