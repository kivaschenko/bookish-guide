# Script and Voice Module - CLI Interface

Standalone module for script generation and voice synthesis using command-line interface.

## Overview

This module provides script generation and voice synthesis capabilities through a simple CLI interface. It's designed to be called by the main pipeline system or used independently.

**Key Features:**
- ✅ Generates scripts and audio files directly to project directories
- ✅ Supports multiple languages
- ✅ Simple KISS-principle architecture
- ✅ Comprehensive test coverage
- ✅ Direct file operations (no temporary files)

## Usage

### Direct CLI Usage

```bash
# Generate script only
python module_script_and_voice.py --project my-video --language english --input-file input.txt -s

# Generate audio only (requires existing script)
python module_script_and_voice.py --project my-video --language english -ag

# Generate both script and audio (default)
python module_script_and_voice.py --project my-video --language french --input-file input.txt

# Show help
python module_script_and_voice.py --help
```

### From Main Pipeline

The module is automatically called by the main pipeline when using the `-s` (script) option:

```bash
python exponential_video.py -s project-name
```

## Command Line Arguments

### Required Arguments
- `--project`: Project name (required)
- `--language`: Language for generation (required)
  - Options: `french`, `english`, `german`, `italian`, `spanish`, `dutch`, `swedish`, `norwegian`, `danish`, `finnish`, `polish`

### Optional Arguments
- `--input-file`: Input text file path (optional, defaults to `projects/{project}/input.txt`)
- `-s, --script-only`: Generate script only (no voice)
- `-ag, --audio-gemini`: Generate TTS audio only (Google Gemini)
- `--verbose, -v`: Verbose logging
- `--help`: Show help message

## Project Structure Created

The module creates the following structure in the projects directory:

```
projects/
└── {project_name}/
    ├── {language}/
    │   ├── outline.json           # Video outline
    │   ├── full_script.json       # Complete script with timing
    │   └── audio/                 # Audio files directory
    │       ├── bullet_001.mp3     # Generated audio segments
    │       ├── bullet_002.mp3
    │       └── ...
    └── metadata_{language}.json   # Generation metadata with file counts
```

### Example for Multi-language Project

```
projects/
└── product-demo/
    ├── english/
    │   ├── outline.json
    │   ├── full_script.json
    │   └── audio/
    │       ├── bullet_001.mp3
    │       └── bullet_002.mp3
    ├── french/
    │   ├── outline.json
    │   ├── full_script.json
    │   └── audio/
    │       ├── bullet_001.mp3
    │       └── bullet_002.mp3
    ├── metadata_english.json
    └── metadata_french.json
```

## Configuration

Configuration is managed through `config.yml`:

```yaml
# API Configuration
api:
  gemini:
    api_key: "your-gemini-key"
    base_url: "https://api.gemini.com"

# Audio Configuration
audio:
  gemini_tts:
    granularity: "bullet"
    voice: "en-US-Standard-A"

# Paths
paths:
  audio: "audio"
  temp: "temp"
```

## Files and Components

### Core Files
- `module_script_and_voice.py`: Main CLI interface
- `paraphraser.py`: Script generation component
- `gemini_tts.py`: Voice synthesis component
- `config.yml`: Configuration file

### Test Suite
All tests are organized in the `tests/` directory:

```
tests/
├── __init__.py                 # Tests package
├── run_tests.py               # Test runner script
├── test_file_creation.py      # File and directory creation tests
├── test_simple.py             # Core function tests
├── test_integration.py        # Integration workflow tests
├── test_cli.py               # CLI argument tests
├── test_summary.py           # Comprehensive test runner
├── demo_structure.py         # Structure demonstration
└── TEST_RESULTS.md           # Detailed test results
```

## Running Tests

### Run All Tests
```bash
cd tests/
python3 run_tests.py
```

### Run Individual Test Suites
```bash
cd tests/
python3 -m unittest test_file_creation.py -v
python3 -m unittest test_simple.py -v
python3 demo_structure.py
```

### Test Coverage
- ✅ Directory structure creation
- ✅ File operations and path handling
- ✅ Metadata generation
- ✅ Multi-language support
- ✅ Error handling and edge cases
- ✅ CLI argument validation
- ✅ Complete workflow simulation

## Integration

This module is designed to be called by the main pipeline system. The main pipeline:

1. Saves input text to `projects/{project}/input.txt`
2. Calls `module_script_and_voice.py` with appropriate parameters
3. Receives generated files in the project directory structure

## Architecture Improvements

The module follows the **KISS (Keep It Simple, Stupid) principle**:

### Before (Complex)
```
temp_file → process → copy_to_project → cleanup
```

### After (Simple)
```
create_dirs → generate_files → save_directly
```

### Key Improvements
- ✅ **Direct File Operations**: No temporary files or complex copying
- ✅ **Consistent Path Handling**: Uses `BASE_DIR` and `PROJECTS_DIR` constants
- ✅ **Simplified Logic**: Clear separation of script (`-s`) and audio (`-ag`) generation
- ✅ **Better Error Handling**: Improved validation and logging
- ✅ **Maintainable Code**: Removed unnecessary complexity

## Security

The module is completely isolated from the main system:
- ✅ No access to main pipeline code
- ✅ No access to dashboard or other modules
- ✅ Simple CLI interface only
- ✅ All files contained within the module and projects directories
- ✅ Comprehensive test coverage ensures reliability

## Dependencies

Install required dependencies:
```bash
pip install -r ../requirements.txt
```

Main dependencies:
- `anthropic>=0.34.0` - For script generation
- `requests>=2.32.0` - For API calls
- `pyyaml>=6.0.1` - For configuration

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Install requirements with `pip install -r ../requirements.txt`
2. **Path Issues**: Ensure you're running from the correct directory
3. **API Keys**: Check your `config.yml` file has valid API keys
4. **Input File**: Ensure input file exists and is not empty

### Test Validation

Run the test suite to validate functionality:
```bash
cd tests/
python3 run_tests.py
```

Expected output: `4/4 test suites passed` 🎉
