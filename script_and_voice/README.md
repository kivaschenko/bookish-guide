# Script and Voice Module - CLI Interface

Standalone module for script generation and voice synthesis using command-line interface.

## Overview

This module provides script generation and voice synthesis capabilities through a simple CLI interface. It's designed to be called by the main pipeline system.

## Usage

### From Main Pipeline

The module is automatically called by the main pipeline when using the `-s` (script) option:

```bash
python exponential_video.py -s project-name
```

### Direct CLI Usage

You can also use the module directly:

```bash
# Generate script and voice
python module_script_and_voice.py --project mon-projet --language french --input-file input.txt

# Generate script only
python module_script_and_voice.py --project mon-projet --language english --input-file input.txt --script-only

# Generate voice only (script must exist)
python module_script_and_voice.py --project mon-projet --language french --input-file input.txt --voice-only
```

## Command Line Arguments

- `--project`: Project name (required)
- `--language`: Language for generation (required)
  - Options: french, english, german, italian, spanish, dutch, swedish, norwegian, danish, finnish, polish
- `--input-file`: Input text file path (required)
- `--script-only`: Generate script only (no voice)
- `--voice-only`: Generate voice only (script must exist)
- `--verbose`: Verbose logging
- `--help`: Show help message

## Output Structure

The module creates the following structure in the project directory:

```
../projects/
└── project-name/
    ├── fr/                    # Language-specific folder
    │   ├── outline.json       # Video outline
    │   └── final_script.txt   # Final script
    ├── audio/                 # Audio files
    │   ├── bullet_001.mp3     # Audio files
    │   ├── bullet_001.wav     # WAV files (for debugging)
    │   └── ...
    └── metadata_fr.json       # Generation metadata
```

## Configuration

Configuration is managed through `config.yml`:

```yaml
# API Configuration
api:
  openai:
    api_key: "your-openai-key"
    model: "gpt-5"
  gemini:
    api_key: "your-gemini-key"
    use_proxy: true
    proxy_url: "https://leader-referencement.com/gemini_tts.php"

# Script Generation
script:
  paragraphs: 50
  words_per_paragraph: 50
  total_words: 2900

# Audio Configuration
audio:
  gemini_tts:
    granularity: "bullet"
    voice_settings:
      speed: 1.0
      pitch: 0.0
```

## Files

- `paraphraser.py`: Script generation using GPT-5
- `gemini_tts.py`: Voice synthesis using Gemini TTS
- `config.yml`: Configuration file
- `input.txt.example`: Example input file

## Integration

This module is designed to be called by the main pipeline system. The main pipeline:

1. Saves input text to `../projects/{project}/ori_vid.txt`
2. Calls `module_script_and_voice.py` with appropriate parameters
3. Receives generated files in the project directory

## Security

The module is completely isolated from the main system:
- No access to main pipeline code
- No access to dashboard or other modules
- Simple CLI interface only
- All files contained within the module directory
