#!/usr/bin/env python3
"""
Script and Voice Module - CLI Interface
Standalone module for script generation and voice synthesis

Usage:
    python module_script_and_voice.py --project mon-projet --language french --input-file input.txt
    python module_script_and_voice.py --help
"""

import argparse
import sys
import logging
from pathlib import Path
import json

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from paraphraser import Paraphraser
from gemini_tts import GeminiTTS
import yaml

# Define Constant Directories
BASE_DIR = Path(__file__).parent.parent
print(f"BASE_DIR is set to: {BASE_DIR}")

PROJECTS_DIR = BASE_DIR / "projects"
print(f"PROJECTS_DIR is set to: {PROJECTS_DIR}")

# Template paths will be constructed dynamically
print(
    f"Project template structure will be: {PROJECTS_DIR}/{{project_name}}/{{language}}/audio"
)


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def load_config():
    """Load configuration from config.yml"""
    config_path = Path(__file__).parent / "config.yml"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        sys.exit(1)


def ensure_project_dirs(project_name, language):
    """Ensure all required project directories exist"""
    project_root = PROJECTS_DIR / project_name
    language_dir = project_root / language
    audio_dir = language_dir / "audio"
    
    # Create all directories at once
    project_root.mkdir(parents=True, exist_ok=True)
    language_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"📁 Project directories ready: {project_root}")
    return project_root, language_dir, audio_dir


def save_metadata(project_root, language_dir, audio_dir, project_name, language, has_audio=False):
    """Save project metadata"""
    metadata = {
        "project": project_name,
        "language": language,
        "generated_files": {
            "outline": str(language_dir / "outline.json"),
            "full_script": str(language_dir / "full_script.json"),
        },
    }
    
    if has_audio:
        metadata["generated_files"]["audio_dir"] = str(audio_dir)
        metadata["files_count"] = {
            "audio_files": len(list(audio_dir.glob("*.mp3"))),
            "wav_files": len(list(audio_dir.glob("*.wav"))),
        }
    
    metadata_file = project_root / f"metadata_{language}.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logging.info(f"📊 Metadata saved: {metadata_file}")
    return metadata


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Script and Voice Module - Generate scripts and voice from text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python module_script_and_voice.py --project mon-projet --language french -s
  python module_script_and_voice.py --project video-1 --language english -ag
  python module_script_and_voice.py --project test --language german
        """,
    )

    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument(
        "--language",
        required=True,
        choices=[
            "french",
            "english",
            "german",
            "italian",
            "spanish",
            "dutch",
            "swedish",
            "norwegian",
            "danish",
            "finnish",
            "polish",
        ],
        help="Language for generation",
    )
    parser.add_argument(
        "--input-file",
        help="Input text file path (optional, defaults to projects/{project_name}/input.txt)",
    )
    parser.add_argument(
        "-s",
        "--script-only",
        action="store_true",
        help="Generate script only (no voice)",
    )
    parser.add_argument(
        "-ag",
        "--audio-gemini",
        action="store_true",
        help="Generate TTS audio only (Google Gemini)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    setup_logging()

    # Determine input file path
    if args.input_file:
        input_path = Path(args.input_file)
    else:
        input_path = Path(f"{PROJECTS_DIR}/{args.project}/input.txt")

    logging.info("🚀 Script and Voice Module - CLI")
    logging.info("=" * 50)
    logging.info(f"📁 Project: {args.project}")
    logging.info(f"🌍 Language: {args.language}")
    logging.info(f"📄 Input file: {input_path}")

    if not input_path.exists():
        logging.error(f"❌ Input file not found: {input_path}")
        sys.exit(1)

    # Load configuration
    config = load_config()

    # Create project structure
    project_root, language_dir, audio_dir = ensure_project_dirs(args.project, args.language)

    try:
        # Read input text
        with open(input_path, "r", encoding="utf-8") as f:
            input_text = f.read().strip()

        if not input_text:
            logging.error("❌ Input file is empty")
            sys.exit(1)

        # Handle script generation (-s flag)
        if args.script_only:
            logging.info("📝 Generating script only...")
            
            paraphraser = Paraphraser(config)
            result = paraphraser.process(language=args.language, input_file_path=str(input_path))

            if not result.get("success"):
                logging.error("❌ Script generation failed")
                sys.exit(1)

            # Save script files directly to project directory
            if "outline" in result:
                outline_file = language_dir / "outline.json"
                with open(outline_file, "w", encoding="utf-8") as f:
                    json.dump(result["outline"], f, indent=2, ensure_ascii=False)
                logging.info(f"📋 Outline saved: {outline_file}")

            if "full_script" in result:
                full_script_file = language_dir / "full_script.json"
                with open(full_script_file, "w", encoding="utf-8") as f:
                    json.dump(result["full_script"], f, indent=2, ensure_ascii=False)
                logging.info(f"📋 Full script saved: {full_script_file}")

            # Calculate total words
            total_words = 0
            if "full_script" in result and "sections" in result["full_script"]:
                for section in result["full_script"]["sections"]:
                    for micro_section in section.get("micro_sections", []):
                        total_words += micro_section.get("actual_words", 0)

            logging.info(f"✅ Script generated: {total_words} words")
            save_metadata(project_root, language_dir, audio_dir, args.project, args.language, has_audio=False)

        # Handle audio generation (-ag flag)
        elif args.audio_gemini:
            logging.info("🎤 Generating audio with Gemini...")
            
            # Check if full_script.json exists
            full_script_file = language_dir / "full_script.json"
            if not full_script_file.exists():
                logging.error("❌ full_script.json not found. Generate script first with -s")
                sys.exit(1)

            gemini_tts = GeminiTTS(config)
            # Override the audio output path to project audio dir
            gemini_tts.audio_path = audio_dir
            
            # Extract text and generate audio
            script_content = gemini_tts.extract_text_from_full_script_json(str(full_script_file))
            voice_result = gemini_tts.generate_all_audio(script_content)

            if not voice_result.get("success"):
                logging.error("❌ Voice generation failed")
                sys.exit(1)

            logging.info(f"✅ Voice generated: {voice_result['total_duration']:.2f}s total")
            save_metadata(project_root, language_dir, audio_dir, args.project, args.language, has_audio=True)

        # Handle both script and audio (default behavior)
        else:
            logging.info("📝🎤 Generating script and audio...")
            
            # Generate script first
            paraphraser = Paraphraser(config)
            result = paraphraser.process(language=args.language, input_file_path=str(input_path))

            if not result.get("success"):
                logging.error("❌ Script generation failed")
                sys.exit(1)

            # Save script files directly to project directory
            if "outline" in result:
                outline_file = language_dir / "outline.json"
                with open(outline_file, "w", encoding="utf-8") as f:
                    json.dump(result["outline"], f, indent=2, ensure_ascii=False)
                logging.info(f"📋 Outline saved: {outline_file}")

            if "full_script" in result:
                full_script_file = language_dir / "full_script.json"
                with open(full_script_file, "w", encoding="utf-8") as f:
                    json.dump(result["full_script"], f, indent=2, ensure_ascii=False)
                logging.info(f"📋 Full script saved: {full_script_file}")

            # Generate audio
            gemini_tts = GeminiTTS(config)
            gemini_tts.audio_path = audio_dir
            
            script_content = gemini_tts.extract_text_from_full_script_json(str(full_script_file))
            voice_result = gemini_tts.generate_all_audio(script_content)

            if not voice_result.get("success"):
                logging.error("❌ Voice generation failed")
                sys.exit(1)

            logging.info(f"✅ Script and Voice generated: {voice_result['total_duration']:.2f}s total")
            save_metadata(project_root, language_dir, audio_dir, args.project, args.language, has_audio=True)

        # Success summary
        logging.info("=" * 50)
        logging.info("✅ SUCCESS - Generation completed!")
        logging.info(f"📁 Project: {project_root}")
        logging.info(f"🌍 Language: {args.language}")
        
        if (language_dir / "outline.json").exists():
            logging.info(f"📋 Outline: {language_dir / 'outline.json'}")
        if (language_dir / "full_script.json").exists():
            logging.info(f"� Full script: {language_dir / 'full_script.json'}")
        if audio_dir.exists() and any(audio_dir.glob("*.mp3")):
            audio_count = len(list(audio_dir.glob("*.mp3")))
            logging.info(f"🎵 Audio files: {audio_count} MP3 files in {audio_dir}")

    except Exception as e:
        logging.error(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
