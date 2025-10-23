#!/usr/bin/env python3
"""
Demo script showing the project directory structure creation
This demonstrates how the improved module_script_and_voice.py creates files
"""

import sys
from pathlib import Path
import tempfile
import shutil
import json

# Mock dependencies
from unittest.mock import MagicMock
mock_anthropic = MagicMock()
mock_requests = MagicMock()
mock_yaml = MagicMock()
mock_paraphraser = MagicMock()
mock_gemini_tts = MagicMock()

sys.modules['anthropic'] = mock_anthropic
sys.modules['requests'] = mock_requests
sys.modules['yaml'] = mock_yaml
sys.modules['paraphraser'] = mock_paraphraser
sys.modules['gemini_tts'] = mock_gemini_tts

# Add Paraphraser and GeminiTTS classes to the mocked modules
mock_paraphraser.Paraphraser = MagicMock()
mock_gemini_tts.GeminiTTS = MagicMock()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import module_script_and_voice


def demo_project_structure_creation():
    """Demonstrate the project structure creation"""
    print("🎬 StoryForge Project Structure Demo")
    print("=" * 50)

    # Create temporary directory for demo
    demo_dir = tempfile.mkdtemp()
    demo_projects_dir = Path(demo_dir) / "projects"
    demo_projects_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Patch the PROJECTS_DIR for this demo
        original_projects_dir = module_script_and_voice.PROJECTS_DIR
        module_script_and_voice.PROJECTS_DIR = demo_projects_dir

        print(f"📁 Demo projects directory: {demo_projects_dir}")
        print()

        # Demo 1: Create a simple project
        print("🔨 Creating project: 'product-demo' in English...")
        project_root, language_dir, audio_dir = module_script_and_voice.ensure_project_dirs(
            "product-demo", "english"
        )

        print(f"  ✅ Project root: {project_root}")
        print(f"  ✅ Language dir: {language_dir}")
        print(f"  ✅ Audio dir: {audio_dir}")
        print()

        # Demo 2: Add French version to same project
        print("🔨 Adding French version to same project...")
        project_root_fr, language_dir_fr, audio_dir_fr = module_script_and_voice.ensure_project_dirs(
            "product-demo", "french"
        )

        print(f"  ✅ French language dir: {language_dir_fr}")
        print(f"  ✅ French audio dir: {audio_dir_fr}")
        print()

        # Demo 3: Create script files
        print("📝 Creating mock script files...")
        
        # English version
        english_outline = {
            "title": "Product Demo Video",
            "language": "english",
            "sections": [
                {"title": "Introduction", "duration": "30s"},
                {"title": "Features", "duration": "90s"},
                {"title": "Call to Action", "duration": "20s"}
            ]
        }

        english_script = {
            "title": "Product Demo Video Script",
            "language": "english",
            "sections": [
                {
                    "title": "Introduction",
                    "micro_sections": [
                        {"text": "Welcome to our amazing product demo.", "actual_words": 7},
                        {"text": "Today we'll show you incredible features.", "actual_words": 7}
                    ]
                },
                {
                    "title": "Features",
                    "micro_sections": [
                        {"text": "Our first feature saves you time.", "actual_words": 7},
                        {"text": "The second feature boosts productivity.", "actual_words": 6}
                    ]
                }
            ]
        }

        # Save English files
        with open(language_dir / "outline.json", "w", encoding="utf-8") as f:
            json.dump(english_outline, f, indent=2, ensure_ascii=False)

        with open(language_dir / "full_script.json", "w", encoding="utf-8") as f:
            json.dump(english_script, f, indent=2, ensure_ascii=False)

        print(f"  ✅ English outline saved: {language_dir / 'outline.json'}")
        print(f"  ✅ English script saved: {language_dir / 'full_script.json'}")

        # French version
        french_outline = {
            "title": "Démonstration Produit Vidéo",
            "language": "french",
            "sections": [
                {"title": "Introduction", "duration": "30s"},
                {"title": "Fonctionnalités", "duration": "90s"},
                {"title": "Appel à l'action", "duration": "20s"}
            ]
        }

        with open(language_dir_fr / "outline.json", "w", encoding="utf-8") as f:
            json.dump(french_outline, f, indent=2, ensure_ascii=False)

        print(f"  ✅ French outline saved: {language_dir_fr / 'outline.json'}")
        print()

        # Demo 4: Create mock audio files
        print("🎵 Creating mock audio files...")
        
        audio_files = [
            "bullet_001.mp3",
            "bullet_002.mp3",
            "bullet_003.mp3",
            "bullet_004.mp3"
        ]

        for audio_file in audio_files:
            (audio_dir / audio_file).touch()
            (audio_dir_fr / audio_file).touch()

        print(f"  ✅ Created {len(audio_files)} English audio files in {audio_dir}")
        print(f"  ✅ Created {len(audio_files)} French audio files in {audio_dir_fr}")
        print()

        # Demo 5: Create metadata
        print("📊 Creating metadata files...")
        
        english_metadata = module_script_and_voice.save_metadata(
            project_root, language_dir, audio_dir,
            "product-demo", "english", has_audio=True
        )

        french_metadata = module_script_and_voice.save_metadata(
            project_root, language_dir_fr, audio_dir_fr,
            "product-demo", "french", has_audio=True
        )

        print(f"  ✅ English metadata: {project_root / 'metadata_english.json'}")
        print(f"  ✅ French metadata: {project_root / 'metadata_french.json'}")
        print()

        # Demo 6: Show final structure
        print("📂 Final Project Structure:")
        print("=" * 30)
        
        def print_tree(directory, prefix="", max_depth=3, current_depth=0):
            """Print directory tree structure"""
            if current_depth >= max_depth:
                return
                
            items = sorted(directory.iterdir())
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                print(f"{prefix}{current_prefix}{item.name}")
                
                if item.is_dir() and current_depth < max_depth - 1:
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    print_tree(item, next_prefix, max_depth, current_depth + 1)

        print_tree(demo_projects_dir)
        print()

        # Demo 7: Show metadata content
        print("📊 Metadata Content Sample:")
        print("=" * 30)
        print("English metadata:")
        print(json.dumps(english_metadata, indent=2)[:300] + "...")
        print()

        # Demo 8: Verify file counts
        print("📈 File Statistics:")
        print("=" * 20)
        
        total_files = sum(1 for _ in demo_projects_dir.rglob("*") if _.is_file())
        json_files = len(list(demo_projects_dir.rglob("*.json")))
        mp3_files = len(list(demo_projects_dir.rglob("*.mp3")))
        
        print(f"  📁 Total files created: {total_files}")
        print(f"  📄 JSON files: {json_files}")
        print(f"  🎵 Audio files: {mp3_files}")
        print()

        print("✅ Demo completed successfully!")
        print(f"📁 Demo files created in: {demo_dir}")
        print("🧹 Cleaning up temporary files...")

    finally:
        # Restore original PROJECTS_DIR
        module_script_and_voice.PROJECTS_DIR = original_projects_dir
        # Clean up demo directory
        shutil.rmtree(demo_dir, ignore_errors=True)

    print()
    print("🎯 Summary of what the improved script does:")
    print("=" * 50)
    print("1. ✅ Creates correct project directory structure")
    print("2. ✅ Handles multiple languages per project")
    print("3. ✅ Saves files directly to final destinations (no temp copies)")
    print("4. ✅ Creates proper metadata with file counts")
    print("5. ✅ Uses consistent path constants throughout")
    print("6. ✅ Follows KISS principle - simple and direct")


if __name__ == "__main__":
    demo_project_structure_creation()