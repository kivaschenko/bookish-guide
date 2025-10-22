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
import shutil
from pathlib import Path
import json

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from paraphraser import Paraphraser
from gemini_tts import GeminiTTS
import yaml

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_config():
    """Load configuration from config.yml"""
    config_path = Path(__file__).parent / "config.yml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        sys.exit(1)

def create_project_structure(project_name, language):
    """Create project directory structure"""
    project_root = Path("projects") / project_name
    language_dir = project_root / language
    
    # Create directories
    project_root.mkdir(parents=True, exist_ok=True)
    language_dir.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"📁 Project structure created: {project_root}")
    return project_root, language_dir

def copy_files_to_project(project_root, language_dir, language, project_name, script_only=False, voice_only=False):
    """Copy generated files to project directory"""
    script_voice_dir = Path(__file__).parent
    temp_dir = script_voice_dir / "temp"
    audio_dir = script_voice_dir / "audio"
    
    # Copy outline.json to language directory
    outline_src = temp_dir / "outline.json"
    outline_dst = language_dir / "outline.json"
    if outline_src.exists():
        shutil.copy2(outline_src, outline_dst)
        logging.info(f"📋 Outline copied: {outline_dst}")
    
    # Copy final_script.txt to language directory
    script_src = temp_dir / "final_script.txt"
    script_dst = language_dir / "final_script.txt"
    if script_src.exists():
        shutil.copy2(script_src, script_dst)
        logging.info(f"📝 Script copied: {script_dst}")
    
    # Copy full_script.json to language directory
    full_script_src = temp_dir / "full_script.json"
    full_script_dst = language_dir / "full_script.json"
    if full_script_src.exists():
        shutil.copy2(full_script_src, full_script_dst)
        logging.info(f"📋 Full script copied: {full_script_dst}")
    
    # Copy audio directory to project (if not script-only OR if voice-only)
    project_audio_dir = project_root / "audio"
    audio_files_copied = False
    if (not script_only or voice_only) and audio_dir.exists() and any(audio_dir.iterdir()):
        if project_audio_dir.exists():
            shutil.rmtree(project_audio_dir)
        shutil.copytree(audio_dir, project_audio_dir)
        logging.info(f"🎵 Audio files copied: {project_audio_dir}")
        audio_files_copied = True
    
    # Create metadata file
    metadata = {
        "project": project_name,
        "language": language,
        "generated_files": {
            "outline": str(language_dir / "outline.json"),
            "full_script": str(language_dir / "full_script.json")
        },
        "files_count": {}
    }
    
    # Add script file only if it exists
    script_file = language_dir / "final_script.txt"
    if script_file.exists():
        metadata["generated_files"]["script"] = str(script_file)
    
    # Add audio info only if audio was copied
    if audio_files_copied:
        metadata["generated_files"]["audio_dir"] = str(project_audio_dir)
        metadata["files_count"] = {
            "audio_files": len(list(project_audio_dir.glob("*.mp3"))) if project_audio_dir.exists() else 0,
            "wav_files": len(list(project_audio_dir.glob("*.wav"))) if project_audio_dir.exists() else 0
        }
    
    metadata_file = project_root / f"metadata_{language}.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
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
  python module_script_and_voice.py --project mon-projet --language french --input-file input.txt
  python module_script_and_voice.py --project video-1 --language english --input-file projects/video-1/input.txt
  python module_script_and_voice.py --project test --language german --input-file input.txt --voice-only
        """
    )
    
    parser.add_argument('--project', required=True, help='Project name')
    parser.add_argument('--language', required=True, 
                       choices=['french', 'english', 'german', 'italian', 'spanish', 
                               'dutch', 'swedish', 'norwegian', 'danish', 'finnish', 'polish'],
                       help='Language for generation')
    parser.add_argument('--input-file', help='Input text file path (optional, defaults to ../projects/{project}/input.txt)')
    parser.add_argument('--script-only', action='store_true', help='Generate script only (no voice)')
    parser.add_argument('--voice-only', action='store_true', help='Generate voice only (script must exist)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    setup_logging()
    
    # Determine input file path
    if args.input_file:
        input_path = Path(args.input_file)
    else:
        input_path = Path(f"../projects/{args.project}/input.txt")
    
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
    project_root, language_dir = create_project_structure(args.project, args.language)
    
    try:
        # Initialize components
        paraphraser = Paraphraser(config)
        gemini_tts = GeminiTTS(config)
        
        # Generate script if needed
        if not args.voice_only:
            logging.info("📝 Generating script...")
            
            # Read input text
            with open(input_path, 'r', encoding='utf-8') as f:
                input_text = f.read().strip()
            
            if not input_text:
                logging.error("❌ Input file is empty")
                sys.exit(1)
            
            # Save input text to temp for paraphraser
            temp_input = Path(__file__).parent / "input.txt"
            with open(temp_input, 'w', encoding='utf-8') as f:
                f.write(input_text)
            
            # Generate script
            result = paraphraser.process(language=args.language, input_file_path=str(input_path))
            
            if not result.get('success'):
                logging.error("❌ Script generation failed")
                sys.exit(1)
            
            # Calculate total words from full_script
            total_words = 0
            if 'full_script' in result and 'sections' in result['full_script']:
                for section in result['full_script']['sections']:
                    for micro_section in section.get('micro_sections', []):
                        total_words += micro_section.get('actual_words', 0)
            
            logging.info(f"✅ Script generated: {total_words} words")
        
        # Generate voice if needed
        if not args.script_only:
            logging.info("🎤 Generating voice...")
            
            # Check if full_script.json exists
            full_script_file = language_dir / "full_script.json"
            if not full_script_file.exists():
                logging.error("❌ full_script.json not found. Generate script first or use --script-only")
                sys.exit(1)
            
            # Extract text from full_script.json
            script_content = gemini_tts.extract_text_from_full_script_json(str(full_script_file))
            
            # Generate voice
            voice_result = gemini_tts.generate_all_audio(script_content)
            
            if not voice_result.get('success'):
                logging.error("❌ Voice generation failed")
                sys.exit(1)
            
            logging.info(f"✅ Voice generated: {voice_result['total_duration']:.2f}s total")
        
        # Copy files to project
        logging.info("📁 Copying files to project...")
        metadata = copy_files_to_project(project_root, language_dir, args.language, args.project, args.script_only, args.voice_only)
        
        # Success summary
        logging.info("=" * 50)
        if args.script_only:
            logging.info("✅ SUCCESS - Script generation completed!")
        else:
            logging.info("✅ SUCCESS - Script and Voice generation completed!")
        
        logging.info(f"📁 Project: {project_root}")
        logging.info(f"🌍 Language: {args.language}")
        logging.info(f"📋 Outline: {metadata['generated_files']['outline']}")
        logging.info(f"📋 Full script: {metadata['generated_files']['full_script']}")
        
        # Show script file only if it exists
        if 'script' in metadata['generated_files']:
            logging.info(f"📝 Script: {metadata['generated_files']['script']}")
        
        # Show audio info only if audio was generated
        if 'audio_dir' in metadata['generated_files']:
            logging.info(f"🎵 Audio: {metadata['generated_files']['audio_dir']}")
            logging.info(f"🎵 Audio files: {metadata['files_count']['audio_files']} MP3, {metadata['files_count']['wav_files']} WAV")
        
    except Exception as e:
        logging.error(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
