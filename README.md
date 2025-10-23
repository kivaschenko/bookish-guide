# StoryForge

AI-powered video content generation platform that transforms text into comprehensive multimedia stories with voice narration and B-roll footage integration.

## 🚀 Overview

StoryForge is a modular AI platform designed for automated video content generation. The system transforms raw text input into production-ready video content through a sophisticated multi-stage pipeline.

### Current Status

The project is actively being refactored into a clean, modular architecture with two main packages:

1. **✅ Script & Voice** - Content generation module (Ready)
2. **🔄 B-roll Selection** - Video matching and assembly (Future phase)

## 📦 Architecture

### Current Modules

#### 1. Script & Voice Package ✅
**Location**: `script_and_voice/`
**Status**: Production ready with comprehensive testing

Complete content generation module that handles:
- Multi-language script generation using GPT-5
- High-quality voice synthesis with Gemini TTS
- Organized project structure creation
- Direct file operations (no temporary files)

**📚 [View Script & Voice Documentation](script_and_voice/README.md)**

#### 2. B-roll Selection Package 🔄
**Location**: `src/` (Future: `b_roll_selection/`)
**Status**: Future development phase

Will handle:
- Semantic video matching
- B-roll footage search and selection
- Video metadata extraction
- Final video assembly

### Project Structure

```
storyforge/
├── script_and_voice/          # ✅ Content generation module
│   ├── module_script_and_voice.py  # CLI interface
│   ├── paraphraser.py        # Script generation
│   ├── gemini_tts.py         # Voice synthesis
│   ├── config.yml            # Module configuration
│   ├── README.md             # 📚 Complete documentation
│   └── tests/                # Comprehensive test suite
├── src/                      # 🔄 Core processing (future refactor)
│   ├── b_roll_finder.py      # B-roll search
│   ├── vector_matcher.py     # Semantic matching
│   ├── heygen_generator.py   # AI avatar generation
│   └── ...                  # Other processing modules
├── projects/                 # Generated content output
│   └── {project_name}/
│       ├── {language}/       # Language-specific content
│       │   ├── outline.json
│       │   ├── full_script.json
│       │   └── audio/        # Voice files
│       └── metadata_{lang}.json
├── config.yml               # Main configuration
└── requirements.txt         # Dependencies
```

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/kaoul/storyforge.git
cd storyforge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Edit `config.yml` and `script_and_voice/config.yml` with your API keys:

```yaml
api:
  gemini:
    api_key: "your-gemini-key"
  # Add other API configurations as needed
```

### Usage

#### Script & Voice Generation

```bash
# Generate script and voice
python script_and_voice/module_script_and_voice.py \
  --project my-video \
  --language english \
  --input-file input.txt

# Script only
python script_and_voice/module_script_and_voice.py \
  --project my-video \
  --language french \
  -s

# Audio only (requires existing script)
python script_and_voice/module_script_and_voice.py \
  --project my-video \
  --language german \
  -ag
```

**📚 [Full Usage Documentation](script_and_voice/README.md)**

#### Complete Pipeline (Legacy)

```bash
# Run full pipeline (uses script_and_voice module internally)
python exponential_video.py -s my-project
```

## 🧪 Testing

### Script & Voice Module Testing

```bash
cd script_and_voice/tests/
python3 run_tests.py
```

**Test Status**: ✅ 4/4 test suites passing

### Supported Languages

French, English, German, Italian, Spanish, Dutch, Swedish, Norwegian, Danish, Finnish, Polish

## 📂 Generated Output

The system creates organized, language-specific project structures:

```
projects/my-project/
├── english/
│   ├── outline.json           # Video structure
│   ├── full_script.json       # Complete script
│   └── audio/                 # Voice files
│       ├── bullet_001.mp3
│       └── bullet_002.mp3
├── french/                    # Additional languages
│   └── ...
└── metadata_english.json     # Generation metadata
```

## 🔄 Development Roadmap

### Phase 1: Script & Voice ✅ Complete
- [x] Modular script generation
- [x] Multi-language voice synthesis
- [x] Direct file operations
- [x] Comprehensive testing
- [x] Complete documentation

### Phase 2: B-roll Selection 🔄 In Planning
- [ ] Refactor `src/` into `b_roll_selection/` package
- [ ] Semantic video matching improvements
- [ ] Advanced B-roll search capabilities
- [ ] Video assembly and final output generation
- [ ] Integration testing with Script & Voice module

### Phase 3: Platform Integration 📋 Future
- [ ] Web dashboard interface
- [ ] API endpoints for external integration
- [ ] Batch processing capabilities
- [ ] Advanced AI avatar integration

## 📚 Documentation

- **[Script & Voice Module](script_and_voice/README.md)** - Complete usage and testing guide
- **[Manual Testing Guide](MANUAL_TEST_INSTRUCTIONS.md)** - Manual testing procedures
- **[Configuration Guide](config.yml)** - System configuration options

## 🛠 Development

### Core Principles

- **Modular Design**: Independent packages with clear interfaces
- **KISS Principle**: Keep it simple and maintainable
- **Comprehensive Testing**: All modules include test suites
- **Documentation First**: Clear documentation for all components

### Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Implement changes with tests
4. Update documentation
5. Submit pull request

## 📋 Dependencies

### Core Dependencies
- `anthropic>=0.34.0` - Script generation
- `requests>=2.32.0` - API communications
- `pyyaml>=6.0.1` - Configuration management
- `torch>=2.0.0` - AI model support
- `transformers>=4.30.0` - Language models

### Development Dependencies
- Testing frameworks and development tools

See `requirements.txt` for complete dependency list.

## 🔧 Support

- **Issues**: Open GitHub issues for bugs and feature requests
- **Documentation**: Check module-specific README files
- **Testing**: Run test suites to validate functionality

## 📄 License

[Add your license here]

---

**Note**: This project is actively being refactored for improved modularity and maintainability. The Script & Voice module is production-ready, while B-roll Selection is planned for future development.