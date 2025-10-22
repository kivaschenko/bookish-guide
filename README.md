# StoryForge

AI-powered video content generation platform that transforms text into comprehensive multimedia stories with voice narration, matching B-roll footage, and AI avatar integration.

## 🚀 Business Logic Overview

StoryForge operates through a sophisticated multi-stage pipeline that transforms raw text input into production-ready video content:

### Core Pipeline Workflow

1. **Input Processing** (`exponential_video.py`)
   - Accepts project configuration and input text
   - Creates organized project structure: `projects/{project-name}/{language}/`
   - Manages multi-language content generation

2. **Script Generation** (`script_and_voice/` module)
   - **Ideation**: Uses GPT-5 to analyze input and create structured ideas
   - **Outline Creation**: Generates video outline with sections, hooks, and meta information
   - **Script Writing**: Creates detailed paragraph-by-paragraph scripts with timing
   - **Output**: `outline.json`, `full_script.json` files per language

3. **Voice Synthesis** (`script_and_voice/gemini_tts.py`)
   - Extracts text from generated scripts
   - Uses Gemini TTS for high-quality voice generation
   - Creates bullet-point audio files (MP3 + WAV for debugging)
   - **Output**: Language-specific audio directory with metadata

4. **Content Matching & Assembly** (`src/` modules)
   - **Vector Matching**: Semantic similarity matching for B-roll footage
   - **HeyGen Integration**: AI avatar video generation
   - **Meta Extraction**: Video metadata analysis and processing
   - **Final Assembly**: Combines all elements into final video

### Project Organization Structure

```
projects/{project-name}/
├── {language}/                 # Language-specific content
│   ├── outline.json           # Video structure and metadata
│   ├── full_script.json       # Detailed script with paragraphs
│   └── audio/                 # Voice synthesis output
│       ├── bullet_001.mp3     # Audio segments
│       ├── bullet_001.wav     # Debug audio files
│       └── audio_bullet_metadata.json
├── metadata_{language}.json   # Generation metadata
└── ori_vid.txt                # Original input text
```

### Module Architecture (Future Structure)

The system is evolving toward a clean two-module architecture:

- **`src/`** - Core video processing and AI capabilities
  - B-roll search and semantic matching
  - HeyGen AI avatar integration  
  - Video metadata extraction and processing
  - Utility functions and core logic

- **`scripts_and_voices/`** - Isolated content generation
  - GPT-5 powered script generation
  - Multi-language voice synthesis
  - Content ideation and outline creation
  - CLI interface for standalone usage

### Key Features

- **Multi-Language Support**: French, English, German, Italian, Spanish, Dutch, Swedish, Norwegian, Danish, Finnish, Polish
- **Modular Design**: Independent script generation and voice synthesis
- **Language-Specific Organization**: Separate directories for each language's assets
- **Comprehensive Metadata**: Full tracking of generation process and timing
- **Production Ready**: High-quality audio output with debugging support

## Project Structure

### Current Structure
```
storyforge/
├── exponential_video.py       # Main pipeline orchestrator
├── src/                       # Core video processing modules
│   ├── b_roll_finder.py      # B-roll search and matching
│   ├── vector_matcher.py     # Semantic similarity matching
│   ├── tts_generator.py      # Text-to-speech functionality
│   ├── heygen_generator.py   # AI avatar generation
│   ├── meta_extractor.py     # Video metadata extraction
│   ├── paraphraser.py        # Script generation logic
│   ├── jouer_son.py          # Audio processing
│   └── utils.py              # Utility functions
├── script_and_voice/          # Isolated content generation module
│   ├── module_script_and_voice.py  # CLI interface
│   ├── paraphraser.py        # GPT-5 script generation
│   ├── gemini_tts.py         # Voice synthesis
│   └── config.yml            # Module configuration
├── projects/                  # Generated content output
│   └── {project-name}/
│       ├── {language}/        # Language-specific content
│       │   ├── outline.json
│       │   ├── full_script.json
│       │   └── audio/         # Voice synthesis files
│       └── metadata_{lang}.json
├── config.yml                # Main configuration
└── requirements.txt          # Dependencies
```

### Future Architecture (Planned)
```
storyforge/
├── src/                      # Core video processing & AI
│   ├── video/               # Video processing modules
│   ├── ai/                  # AI integration (HeyGen, etc.)
│   ├── matching/            # Content matching & search
│   └── utils/               # Shared utilities
├── scripts_and_voices/       # Content generation (renamed)
│   ├── generation/          # Script & voice generation
│   ├── languages/           # Language-specific configs
│   └── cli/                 # Command-line interfaces
└── projects/                # Output directory structure
```

## Development Installation

### Prerequisites

- Python 3.8+ (recommended: Python 3.10+)
- CUDA-compatible GPU (optional, for faster AI processing)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/kaoul/storyforge.git
   cd storyforge
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Linux/macOS:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Upgrade pip first
   pip install --upgrade pip
   
   # Install all dependencies
   pip install -r requirements.txt
   ```

4. **Configure the application**
   ```bash
   # Copy example config and customize
   cp config.yml.example config.yml  # If example exists
   # Edit config.yml with your API keys and settings
   ```

5. **Verify installation**
   ```bash
   # Test basic imports
   python -c "import torch; import transformers; import sentence_transformers; print('All dependencies installed successfully!')"
   ```

### Configuration

**Main Configuration** (`config.yml`):
```yaml
# API Configuration
api:
  openai:
    api_key: "your-openai-api-key"
    model: "gpt-4o"
  heygen:
    api_key: "your-heygen-api-key"
  gemini:
    api_key: "your-gemini-key"
    use_proxy: true
    proxy_url: "https://leader-referencement.com/gemini_tts.php"

# File Paths
paths:
  broll_folder: "b-roll"
  output_folder: "output"
  audio: "audio"
  temp: "temp"

# AI Models
models:
  sentence_transformer: "all-mpnet-base-v2"
  tts_model: "your-preferred-tts-model"

# Script Generation Settings
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

**Script & Voice Module** (`script_and_voice/config.yml`):
- Independent configuration for isolated content generation
- Same API keys but module-specific settings
- Focuses on script generation and voice synthesis parameters

### Development Environment

For active development, you may want to install additional dev tools:

```bash
# Install development dependencies (optional)
pip install jupyter ipython pytest black flake8
```

### GPU Support

If you have a CUDA-compatible GPU, the PyTorch installation should automatically detect and use it. To verify GPU availability:

```bash
python -c "import torch; print('CUDA available:', torch.cuda.is_available())"
```

### Common Issues

1. **CUDA/GPU Issues**: If you encounter CUDA-related errors, install the CPU-only version of PyTorch:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```

2. **Memory Issues**: Large AI models require significant RAM. Consider using smaller models if you encounter memory issues.

3. **API Rate Limits**: Ensure your API keys have sufficient quotas for OpenAI and other services.

## Usage

### Pipeline Execution

**Main Pipeline** (Complete video generation):
```bash
# Generate complete video project with script and voice
python exponential_video.py -s my-project-name

# The pipeline automatically:
# 1. Creates project structure
# 2. Generates multi-language scripts
# 3. Synthesizes voice audio
# 4. Processes B-roll matching
# 5. Assembles final video
```

**Script and Voice Module** (Standalone content generation):
```bash
# Direct CLI usage for content generation
cd script_and_voice/

# Generate script and voice for specific language
python module_script_and_voice.py \
  --project my-project \
  --language french \
  --input-file ../projects/my-project/ori_vid.txt

# Generate script only (no voice synthesis)
python module_script_and_voice.py \
  --project my-project \
  --language english \
  --input-file input.txt \
  --script-only

# Generate voice only (requires existing script)
python module_script_and_voice.py \
  --project my-project \
  --language french \
  --input-file input.txt \
  --voice-only
```

### Supported Languages
French, English, German, Italian, Spanish, Dutch, Swedish, Norwegian, Danish, Finnish, Polish

### Command Line Options

**Main Pipeline** (`exponential_video.py`):
- `-s, --project-name`: Project name for generation

**Script & Voice Module** (`module_script_and_voice.py`):
- `--project`: Project name (required)
- `--language`: Target language (required)
- `--input-file`: Input text file path (required)
- `--script-only`: Generate script only (no voice)
- `--voice-only`: Generate voice only (script must exist)
- `--verbose`: Enable verbose logging
- `--help`: Show help message

### Output Structure

The system generates organized, language-specific content:

```
projects/my-project/
├── english/                   # English content
│   ├── outline.json          # Video structure & metadata
│   ├── full_script.json      # Detailed script with timing
│   └── audio/                # Voice synthesis (if generated)
│       ├── bullet_001.mp3    # Audio segments
│       ├── bullet_002.mp3    # ...
│       └── audio_bullet_metadata.json
├── french/                   # French content (similar structure)
├── metadata_english.json    # Generation metadata
├── metadata_french.json     # ...
└── ori_vid.txt              # Original input text
```

## Testing & Development

### Running Tests

```bash
# Test audio placement and file organization
python test_audio_placement.py

# Test voice generation format and integration
python test_voice_generation_fix.py

# Manual testing (see MANUAL_TEST_INSTRUCTIONS.md)
python exponential_video.py -s test-project
```

### Development Principles

**Modular Architecture**:
- **Isolation**: `script_and_voice/` module operates independently
- **Security**: No cross-module code access, CLI-only interfaces  
- **Scalability**: Each module can be developed and deployed separately
- **Testability**: Comprehensive test coverage for file operations and integration

**Language-Specific Organization**:
- Each language gets dedicated directory structure
- Metadata tracking per language and project
- Independent audio generation and processing
- Future-ready for additional language support

**Production Considerations**:
- High-quality audio output (MP3 + WAV for debugging)
- Comprehensive error handling and logging
- Automatic cleanup of temporary files
- Metadata preservation for video assembly pipeline

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and commit: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Submit a pull request

## Dependencies

### Main Dependencies

- **AI/ML**: `torch`, `transformers`, `sentence-transformers`, `huggingface-hub`
- **Data Science**: `numpy`, `scipy`, `scikit-learn`
- **API**: `openai`, `requests`
- **Utilities**: `pyyaml`, `tqdm`, `psutil`, `pillow`

### Development Dependencies

- `jupyter` - Interactive development
- `pytest` - Testing framework
- `black` - Code formatting
- `flake8` - Code linting

## License

[Add your license here]

## Support

For issues and questions, please open an issue on the GitHub repository.