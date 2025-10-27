# 🎬 StoryForge Premontage FastAPI Backend

A modern FastAPI-based backend for the StoryForge premontage system, providing video timeline editing and B-roll synchronization capabilities.

## 🚀 Quick Start

### Installation

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the server:**
   ```bash
   python run.py
   ```

3. **Access the interface:**
   - Main interface: http://localhost:47393
   - API documentation: http://localhost:47393/docs
   - Alternative docs: http://localhost:47393/redoc

## 📁 Project Structure

```
backend/
├── main.py                    # FastAPI application entry point
├── run.py                     # Server startup script with CLI options
├── requirements.txt           # Python dependencies
├── auth/                      # Authentication middleware
│   ├── __init__.py
│   └── middleware.py
├── config/                    # Configuration management
│   ├── __init__.py
│   └── settings.py
├── models/                    # Pydantic models and schemas
│   ├── __init__.py
│   └── schemas.py
├── routes/                    # API route handlers
│   ├── __init__.py
│   └── api.py
├── websocket/                 # WebSocket handlers
│   ├── __init__.py
│   └── handler.py
└── static/                    # Static files (HTML interface)
    └── interface.html
```

## 🛠️ Configuration

The backend uses the main `config.yml` file from the project root. Key configuration sections:

```yaml
# Authentication (optional)
dashboard:
  auth:
    enabled: false
    username: "admin" 
    password: "admin"

# Server settings
server:
  host: "0.0.0.0"
  port: 47393
  reload: false

# File paths
paths:
  projects: "./projects"
  b_roll: "./b-roll"
  temp: "./temp"
```

## 🔌 API Endpoints

### Timeline Management
- `GET /api/timeline` - Get current timeline data
- `POST /api/timeline` - Update timeline data
- `GET /api/project-info` - Get project information
- `GET /api/status` - Get system status

### File Operations
- `POST /api/upload` - Upload overlay images
- `DELETE /api/upload/{filename}` - Delete uploaded files
- `GET /b-roll/{file_path}` - Serve B-roll files
- `GET /projects/{file_path}` - Serve project files

### WebSocket
- `WS /ws` - Real-time communication for logs, progress updates, and notifications

### System
- `GET /health` - Health check endpoint
- `GET /` - Main HTML interface

## 🌐 WebSocket Communication

The WebSocket endpoint provides real-time communication with several message types:

### Client → Server Messages
```json
{
  "type": "ping",
  "data": {}
}
```

### Server → Client Messages
```json
{
  "type": "log",
  "level": "info",
  "message": "Processing started",
  "timestamp": "2024-01-01T12:00:00",
  "details": {}
}
```

Message types:
- `log` - Log messages with different levels
- `progress` - Processing progress updates
- `notification` - System notifications
- `timeline_update` - Timeline data changes
- `pong` - Response to ping messages

## 🔐 Authentication

HTTP Basic Authentication is configurable via `config.yml`:

```yaml
dashboard:
  auth:
    enabled: true
    username: "your_username"
    password: "your_password"
```

When enabled, all endpoints require authentication except `/health`.

## 🚀 Running the Server

### Basic Usage
```bash
python run.py
```

### Development Mode
```bash
python run.py --reload --log-level debug
```

### Custom Host/Port
```bash
python run.py --host 0.0.0.0 --port 8080
```

### Project-Specific Mode
```bash
python run.py --project my-project-06
```

### Command Line Options
```
--host HOST              Host to bind server to
--port PORT              Port to bind server to  
--reload                 Enable auto-reload for development
--project PROJECT        Specify project name for temp path
--log-level LEVEL        Set logging level (debug/info/warning/error)
--validate-only          Only validate configuration and exit
```

## 📊 Data Models

### Timeline Item
```json
{
  "start_time": 0.0,
  "end_time": 5.0,
  "duration": 5.0,
  "broll_path": "b-roll/video.mp4",
  "bullet_point": "Introduction text",
  "similarity_score": 0.85,
  "image": "ressources/overlay.png",
  "metadata": {}
}
```

### Upload Response
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file_path": "ressources/uploaded_image.png",
  "file_size": 12345
}
```

## 🔄 Integration with Legacy System

This FastAPI backend is designed to replace the legacy HTTP server while maintaining compatibility:

### Migrated Features
- ✅ HTTP Basic Authentication from config.yml
- ✅ Timeline data serving (`/api/timeline`)
- ✅ File upload handling (`/api/upload`)
- ✅ Static file serving (B-roll and project files)
- ✅ Project-specific temp path handling

### Enhanced Features
- 🆕 Modern FastAPI framework with automatic API documentation
- 🆕 WebSocket support for real-time communication
- 🆕 Structured logging and error handling
- 🆕 Pydantic models for data validation
- 🆕 Health check endpoint
- 🆕 Configuration validation
- 🆕 CLI with multiple options

### Compatibility
The new backend serves the same endpoints as the legacy server, ensuring frontend compatibility while providing enhanced functionality.

## 🧪 Development

### Installing Development Dependencies
```bash
pip install -r requirements.txt
```

### Running Tests
```bash
pytest
```

### Code Style
The project follows Python best practices:
- Type hints throughout
- Pydantic models for data validation
- Structured logging
- Error handling with proper HTTP status codes

## 🚨 Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   python run.py --port 8080
   ```

2. **Config file not found:**
   - Ensure `config.yml` exists in the project root
   - Use `--validate-only` to check configuration

3. **broll_timing.json missing:**
   - Run B-roll processing first: `python -m b_roll.cli extract-metadata`
   - The timeline API requires this file to exist

4. **Authentication issues:**
   - Check credentials in `config.yml`
   - Disable auth temporarily: set `dashboard.auth.enabled: false`

### Logs
Server logs are written to both console and `premontage.log` file.

## 🤝 Contributing

1. Follow the existing code structure
2. Add type hints to all functions
3. Update models in `models/schemas.py` for new data structures
4. Add appropriate error handling
5. Update this README for new features

## 📄 License

This project is part of the StoryForge ecosystem.