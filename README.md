# StoryForge

AI-assisted pipeline that turns raw ideas into publish-ready videos: script, voice, smart B-roll timing, and final assembly.

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-007808?logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-Vision-412991?logo=openai&logoColor=white)](https://platform.openai.com/)
[![Anthropic](https://img.shields.io/badge/Anthropic-Claude-191919)](https://www.anthropic.com/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Why This Project

StoryForge is built for creators and teams that need faster content production without sacrificing quality.

- Convert text ideas into structured scripts
- Generate multilingual AI narration
- Match B-roll clips semantically to script segments
- Fine-tune timing in a lightweight web editor
- Export final videos ready for publishing

## Tech Stack

- Core: Python, FFmpeg, YAML config-driven workflows
- AI/LLM: Anthropic (script generation), OpenAI Vision + embeddings (B-roll intelligence), Gemini TTS (voice)
- ML/NLP: sentence-transformers, torch
- Interfaces: CLI-first automation + local web timeline editor

## Architecture At A Glance

1. Script & Voice (`script_and_voice/`)
2. B-roll Intelligence (`b_roll/`)
3. Timeline Editor Server (`editing_server/`)

Each module can run independently or as part of the full pipeline.

## Quick Start

### 1. Setup

```bash
python3 setup.py
# Then create config.yml from config.yml.example and add API keys.
```

### 2. Generate A Full Video

```bash
python generate_video.py --input "Today I'll share 3 tips for better sleep" --output "sleep-tips"
```

### 3. Optional: Visual Timeline Editing

```bash
python editing_server/server.py
# Opens local editor for timeline and B-roll adjustments.
```

## Key Commands

```bash
# Script + voice module
python script_and_voice/module_script_and_voice.py --project my-video --language english

# B-roll preparation
python -m b_roll.cli prepare-vectors

# Video assembly
python simple_video_assembler.py --project my-video
```

## Project Structure

```text
.
├── generate_video.py
├── simple_video_assembler.py
├── setup.py
├── config.yml.example
├── script_and_voice/
├── b_roll/
├── editing_server/
├── b-roll/          # Your media library
└── projects/        # Generated outputs
```

## Portfolio Notes

- Demonstrates end-to-end AI media automation
- Combines NLP, semantic retrieval, and media processing
- Includes both backend orchestration and frontend editing workflow
- Built for real production usage, not only proof-of-concept demos

## Documentation

- [Script & Voice Module](script_and_voice/README.md)
- [B-roll Intelligence Module](b_roll/README.md)
- [Timeline Editing Server](editing_server/README.md)
- [Configuration Example](config.yml.example)

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
