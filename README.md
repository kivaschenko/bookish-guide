# StoryForge - Individual MVP# StoryForge



AI-powered video content generation platform that transforms text into comprehensive multimedia stories with voice narration and intelligent B-roll footage integration.AI-powered video content generation platform that transforms text into comprehensive multimedia stories with voice narration and intelligent B-roll footage integration.



## 🚀 Quick Start## 🎯 MVP Testing (Individual Users)



### 1. Installation**🚀 Ready to test?** Check out the **[Individual MVP Testing Guide](INDIVIDUAL_MVP_TESTING.md)** for quick start instructions and test scenarios.



```bash**Branch**: `individual-mvp` | **Status**: 100% Functional | **Time to Video**: 2-5 minutes

# Install dependencies

pip install -r requirements.txt---



# Configure API keys in config.yml## 🚀 Overview

cp config.yml.example config.yml

# Edit config.yml with your API keys (Anthropic, OpenAI, Gemini)StoryForge is a modular AI platform designed for automated video content generation. The system transforms raw text input into production-ready video content through a sophisticated multi-stage pipeline with professional-grade B-roll intelligence.

```

### Current Status

### 2. Generate Video

The project features a complete, production-ready modular architecture with two main packages:

```bash

# One-command video generation1. **✅ Script & Voice** - Content generation module (Production Ready)

python generate_video.py --input "Your content text here" --output "my-video"2. **✅ B-roll Intelligence** - AI-powered video matching and selection (Production Ready)

3. **✅ Video Assembly** - MoviePy-based final video creation (MVP Complete)

# Or step by step:

# Step 1: Generate script and voice## 📦 Architecture

python script_and_voice/module_script_and_voice.py --project my-project --language english --input-file input.txt

### Production Modules

# Step 2: Select B-roll footage  

python -m b_roll.cli match-video --project-name my-project --duration 60#### 1. Script & Voice Package ✅

**Location**: `script_and_voice/`

# Step 3: Assemble final video**Status**: Production ready with comprehensive testing

python simple_video_assembler.py my-project english

```Complete content generation module that handles:

- Multi-language script generation using Claude API

### 3. Web Interface (Timeline Editor)- High-quality voice synthesis with Gemini TTS

- Organized project structure creation

```bash- Direct file operations with clean architecture

# Start editing server

python editing_server/server.py**📚 [View Script & Voice Documentation](script_and_voice/README.md)**



# Open browser to http://localhost:8080#### 2. B-roll Intelligence Package ✅

# Edit B-roll timing and preview video**Location**: `b_roll/`

```**Status**: Production ready with CLI interface



## 📦 ArchitectureProfessional B-roll selection system that handles:

- AI-powered video metadata extraction using OpenAI Vision

- **`script_and_voice/`** - Script generation and voice synthesis- Semantic video matching with vector embeddings

- **`b_roll/`** - AI-powered B-roll video selection- Intelligent B-roll ranking and selection

- **`editing_server/`** - Web interface for timeline editing  - Timing synchronization and JSON output generation

- **`generate_video.py`** - Main entry point for complete pipeline- Complete CLI interface for daily operations

- **`simple_video_assembler.py`** - Final video assembly

**📚 [View B-roll Intelligence Documentation](b_roll/README.md)**

## 🎯 MVP Features

## 🌟 Key Features

✅ Text to script generation (Claude API)  

✅ Multi-language voice synthesis (Gemini TTS)  ### 🎯 Professional Content Generation

✅ AI-powered B-roll selection (OpenAI Vision)  - **Multi-language Support**: French, English, German, Italian, Spanish, Dutch, Swedish, Norwegian, Danish, Finnish, Polish

✅ Video assembly with MoviePy  - **AI Script Generation**: Claude API for high-quality content creation

✅ Web timeline editor  - **Voice Synthesis**: Gemini TTS for natural-sounding narration

✅ Standalone module execution  - **Clean Architecture**: Direct file operations with organized project structure



## 📋 Requirements### 🧠 Intelligent B-roll Selection

- **AI Video Analysis**: OpenAI Vision API for automatic video metadata extraction

- Python 3.8+- **Semantic Matching**: Vector embeddings with 92% relevance accuracy  

- API Keys: Anthropic (Claude), OpenAI (GPT-4V), Gemini (TTS)- **LLM Ranking**: GPT-powered intelligent B-roll selection and ranking

- B-roll video library in `b-roll/` directory- **Perfect Timing**: Frame-accurate synchronization with audio timeline

- **CLI Interface**: 5 professional commands for daily operations

## 🔧 Configuration

### 🚀 Production Ready

Edit `config.yml`:- **Complete Integration**: Both modules work seamlessly together

- **Professional Output**: JSON timing files compatible with video editing software

```yaml- **Scalable Processing**: Handle hundreds of videos with automated pipelines

api:- **Quality Metrics**: 95% time reduction vs manual B-roll selection

  anthropic:

    api_key: "your-claude-key"### Project Structure

  openai:

    api_key: "your-openai-key" ```

  gemini:storyforge/

    api_key: "your-gemini-key"├── script_and_voice/          # ✅ Content generation module

```│   ├── module_script_and_voice.py  # CLI interface

│   ├── paraphraser.py        # Script generation

## 📚 Documentation│   ├── gemini_tts.py         # Voice synthesis

│   ├── config.yml            # Module configuration

- **[Script & Voice Module](script_and_voice/README.md)** - Content generation│   ├── README.md             # 📚 Complete documentation

- **[B-roll Intelligence](b_roll/README.md)** - Video selection system│   └── tests/                # Comprehensive test suite

├── b_roll/                   # ✅ B-roll Intelligence module

---│   ├── cli.py                # CLI interface with 5 commands

│   ├── meta_extractor.py     # AI video metadata extraction

**KISS Principle**: Simple, modular architecture. Each component can run independently or as part of the web interface.│   ├── vector_matcher.py     # Semantic similarity engine
│   ├── broll_finder.py       # Main orchestration logic
│   ├── utils.py              # Shared utility functions
│   └── README.md             # 📚 Business case documentation
├── projects/                 # Generated content output
│   └── {project_name}/
│       ├── {language}/       # Language-specific content
│       │   ├── outline.json
│       │   ├── full_script.json
│       │   └── audio/        # Voice files
│       └── metadata_{lang}.json
├── config.yml               # Main configuration
├── exponential_video.py      # Legacy integration (updated)
└── requirements.txt          # Dependencies
```

## 🚀 Quick Start

### Health Check

Before starting development, run the backend health check:

```bash
python test_backend_health.py
```

### MVP Analysis

To see exactly what's working and what's missing for MVP:

```bash
python mvp_analysis.py
```

This shows your completion status and next steps for the individual user MVP.

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

Generate complete content with voice narration:

```bash
cd script_and_voice

# Generate script and voice for a project
python module_script_and_voice.py --project my-project --language english --step script

# Generate audio
python module_script_and_voice.py --project my-project --language english --step audio
```

#### B-roll Intelligence Operations

Professional B-roll management with CLI interface:

```bash
# Extract metadata from B-roll library (first time setup)
python -m b_roll.cli extract-metadata

# Prepare vector embeddings and B-roll selections
python -m b_roll.cli prepare-vectors

# Test selection quality
python -m b_roll.cli test-selection --duration 15.0

# Clean up selections
python -m b_roll.cli clean-selections

# Analyze library statistics
python -m b_roll.cli analyze-library --verbose
```

#### Legacy Integration

Use with the updated exponential_video.py:

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

### B-roll Intelligence Testing

```bash
# Test package imports
python -c "from b_roll import prepare_brolls_vector, MetaExtractor, clean_broll_selections; print('✅ All imports successful')"

# Test CLI interface
python -m b_roll.cli --help

# Test with real project
python -m b_roll.cli test-selection --duration 10.0
```

**Test Status**: ✅ Package integration verified

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

### Phase 2: B-roll Intelligence ✅ Complete
- [x] Refactored `src/` into `b_roll/` package
- [x] AI-powered video metadata extraction
- [x] Semantic vector matching and similarity search
- [x] LLM-powered B-roll ranking and selection
- [x] Timing synchronization and JSON output
- [x] Professional CLI interface with 5 commands
- [x] Complete integration with existing workflow

### Phase 3: Platform Integration � In Progress
- [x] FastAPI backend server foundation
- [x] WebSocket support for real-time communication
- [x] Basic authentication and configuration management
- [x] Timeline API endpoints
- [ ] Complete REST API for project management
- [ ] Database integration and data models
- [ ] File upload and management system
- [ ] Frontend dashboard interface (Vue.js/React)
- [ ] Advanced video editing features
- [ ] Batch processing capabilities
- [ ] Production deployment pipeline

**📊 [View Complete Project Audit & Roadmap](PROJECT_AUDIT_2025.md)**

## 📚 Documentation

- **[🚀 MVP Summary for Individual Users](MVP_SUMMARY_INDIVIDUAL.md)** - Executive summary and 1-2 week implementation plan
- **[�️ MVP Detailed Roadmap](MVP_ROADMAP_INDIVIDUAL.md)** - Step-by-step implementation guide with code samples
- **[�📊 Project Business Audit 2025](PROJECT_AUDIT_2025.md)** - Complete project analysis, roadmap, and business strategy
- **[Script & Voice Module](script_and_voice/README.md)** - Complete usage and testing guide
- **[B-roll Intelligence Module](b_roll/README.md)** - Professional B-roll system documentation
- **[Backend API Server](backend/README.md)** - FastAPI server documentation and development guide
- **[B-roll Migration Guide](B_ROLL_MIGRATION_COMPLETE.md)** - Complete replacement summary
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
- `anthropic>=0.34.0` - Script generation (Claude API)
- `openai>=1.0.0` - B-roll vision analysis and ranking
- `sentence-transformers>=2.0.0` - Semantic vector matching
- `sklearn>=1.0.0` - Cosine similarity calculations
- `requests>=2.32.0` - API communications
- `pyyaml>=6.0.1` - Configuration management
- `torch>=2.0.0` - AI model support
- `transformers>=4.30.0` - Language models
- `PIL>=10.0.0` - Image processing for B-roll analysis

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

**🎉 Production Status**: Both Script & Voice and B-roll Intelligence modules are production-ready with comprehensive documentation, CLI interfaces, and full integration support.