# StoryForge

AI-powered video content generation tool that creates stories with voice narration and matching B-roll footage.

## Features

- **Script Generation**: AI-powered script creation and paraphrasing
- **Voice Synthesis**: Text-to-speech generation with multiple voice options
- **B-roll Matching**: Semantic vector matching to find relevant video footage
- **HeyGen Integration**: AI avatar video generation
- **Meta Extraction**: Video metadata analysis and processing

## Project Structure

```
storyforge/
├── src/                    # Main source code
│   ├── b_roll_finder.py   # B-roll search and matching
│   ├── vector_matcher.py  # Semantic similarity matching
│   ├── tts_generator.py   # Text-to-speech functionality
│   ├── heygen_generator.py # AI avatar generation
│   ├── meta_extractor.py  # Video metadata extraction
│   └── utils.py           # Utility functions
├── script_and_voice/       # Script and voice processing
│   ├── module_script_and_voice.py
│   ├── gemini_tts.py
│   └── paraphraser.py
├── config.yml             # Main configuration file
└── requirements.txt       # Python dependencies
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

Create or edit `config.yml` with your API keys and settings:

```yaml
api:
  openai:
    api_key: "your-openai-api-key"
    model: "gpt-4o"
  heygen:
    api_key: "your-heygen-api-key"

paths:
  broll_folder: "b-roll"
  output_folder: "output"

models:
  sentence_transformer: "all-mpnet-base-v2"
  tts_model: "your-preferred-tts-model"
```

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

### Basic Usage

```bash
# Example usage (adjust based on your actual entry points)
python src/vector_matcher.py
python script_and_voice/module_script_and_voice.py
```

### Running Tests

```bash
# Run tests (if available)
python -m pytest tests/
```

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