# StoryForge - Individual MVP

AI-powered video content generation platform that transforms text into comprehensive multimedia stories with voice narration and intelligent B-roll footage integration.

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys in config.yml
cp config.yml.example config.yml
# Edit config.yml with your API keys (Anthropic, OpenAI, Gemini)
```

### 2. Generate Video

```bash
# One-command video generation
python generate_video.py --input "Your content text here" --output "my-video"

# Or step by step:
# Step 1: Generate script and voice
python script_and_voice/module_script_and_voice.py --project my-project --language english --input-file input.txt

# Step 2: Select B-roll footage  
python -m b_roll.cli match-video --project-name my-project --duration 60

# Step 3: Assemble final video
python simple_video_assembler.py my-project english
```

### 3. Web Interface (Timeline Editor)

```bash
# Start editing server

```bash
# Start editing server
python editing_server/server.py

# Open browser to http://localhost:8080
# Edit B-roll timing and preview video
```

## 📦 Architecture

- **`script_and_voice/`** - Script generation and voice synthesis
- **`b_roll/`** - AI-powered B-roll video selection
- **`editing_server/`** - Web interface for timeline editing  
- **`generate_video.py`** - Main entry point for complete pipeline
- **`simple_video_assembler.py`** - Final video assembly

## 🎯 MVP Features

✅ Text to script generation (Claude API)  
✅ Multi-language voice synthesis (Gemini TTS)  
✅ AI-powered B-roll selection (OpenAI Vision)  
✅ Video assembly with MoviePy  
✅ Web timeline editor  
✅ Standalone module execution  

## 📋 Requirements

- Python 3.8+
- API Keys: Anthropic (Claude), OpenAI (GPT-4V), Gemini (TTS)
- B-roll video library in `b-roll/` directory

## 🔧 Configuration

Edit `config.yml`:

## 📚 Documentation

- **[Script & Voice Module](script_and_voice/README.md)** - Content generation
- **[B-roll Intelligence](b_roll/README.md)** - Video selection system

---

**KISS Principle**: Simple, modular architecture. Each component can run independently or as part of the web interface.