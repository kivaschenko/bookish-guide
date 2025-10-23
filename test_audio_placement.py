#!/usr/bin/env python3
"""
Test script for audio file placement functionality
Creates mock audio files and tests the directory creation and file copying logic
"""

import sys
import shutil
import json
import logging
from pathlib import Path

# Add script_and_voice directory to path
sys.path.insert(0, str(Path(__file__).parent / "script_and_voice"))

from module_script_and_voice import copy_files_to_project, create_project_structure


def setup_logging():
    """Setup logging for test"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def create_mock_audio_files(audio_dir, num_files=6):
    """Create mock audio files for testing"""
    audio_dir = Path(audio_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Create mock MP3 files
    for i in range(1, num_files + 1):
        mp3_file = audio_dir / f"bullet_{i:03d}.mp3"
        wav_file = audio_dir / f"bullet_{i:03d}.wav"

        # Create mock files with some content
        with open(mp3_file, "wb") as f:
            f.write(b"MOCK MP3 DATA " * 100)  # Simulate some audio data

        with open(wav_file, "wb") as f:
            f.write(b"MOCK WAV DATA " * 200)  # Simulate some audio data

    # Create mock metadata file
    metadata = {"granularity": "bullet", "total_bullets": num_files, "bullets": []}

    cumulative_time = 0.0
    for i in range(1, num_files + 1):
        duration = 30.0 + i * 5  # Mock duration
        bullet_metadata = {
            "bullet_number": i,
            "text": f"Mock bullet text {i}",
            "audio_file": f"bullet_{i:03d}.mp3",
            "start_time": cumulative_time,
            "duration": duration,
            "end_time": cumulative_time + duration,
        }
        metadata["bullets"].append(bullet_metadata)
        cumulative_time += duration

    metadata_file = audio_dir / "audio_bullet_metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logging.info(f"✅ Created {num_files} mock audio files in {audio_dir}")
    return metadata


def create_mock_script_files(language_dir):
    """Create mock script files for testing"""
    language_dir = Path(language_dir)
    language_dir.mkdir(parents=True, exist_ok=True)

    # Create mock outline.json
    outline = {
        "video_meta": {
            "title_variants": ["Test Video Title"],
            "tone_style": "test tone",
            "target_audience": "test audience",
            "estimated_words_count": 200,
        },
        "hook": {"text": "Test hook text", "curiosity_loop": "Test curiosity loop"},
        "sections": [
            {"id": 1, "title": "Test Section 1", "core_idea": "Test core idea 1"},
            {"id": 2, "title": "Test Section 2", "core_idea": "Test core idea 2"},
        ],
    }

    outline_file = language_dir / "outline.json"
    with open(outline_file, "w", encoding="utf-8") as f:
        json.dump(outline, f, indent=2, ensure_ascii=False)

    # Create mock full_script.json
    full_script = {
        "sections": [
            {
                "micro_sections": [
                    {"title": "Test 1", "paragraph": "Test paragraph 1"},
                    {"title": "Test 2", "paragraph": "Test paragraph 2"},
                    {"title": "Test 3", "paragraph": "Test paragraph 3"},
                ]
            },
            {
                "micro_sections": [
                    {"title": "Test 4", "paragraph": "Test paragraph 4"},
                    {"title": "Test 5", "paragraph": "Test paragraph 5"},
                    {"title": "Test 6", "paragraph": "Test paragraph 6"},
                ]
            },
        ]
    }

    full_script_file = language_dir / "full_script.json"
    with open(full_script_file, "w", encoding="utf-8") as f:
        json.dump(full_script, f, indent=2, ensure_ascii=False)

    logging.info(f"✅ Created mock script files in {language_dir}")


def test_audio_placement():
    """Test the complete audio placement workflow"""
    setup_logging()

    logging.info("🧪 Starting audio placement test")
    logging.info("=" * 50)

    # Test configuration
    test_project = "test-audio-project"
    test_language = "french"

    # Setup test directories
    script_voice_dir = Path(__file__).parent / "script_and_voice"
    test_audio_dir = script_voice_dir / "audio"

    # Clean up any existing test data
    test_projects_dir = Path("projects") / test_project
    if test_projects_dir.exists():
        shutil.rmtree(test_projects_dir)
        logging.info(f"🧹 Cleaned up existing test project: {test_projects_dir}")

    if test_audio_dir.exists():
        shutil.rmtree(test_audio_dir)
        logging.info(f"🧹 Cleaned up existing audio directory: {test_audio_dir}")

    try:
        # Step 1: Create project structure
        logging.info("📁 Step 1: Creating project structure")
        project_root, language_dir = create_project_structure(
            test_project, test_language
        )

        # Step 2: Create mock script files
        logging.info("📝 Step 2: Creating mock script files")
        create_mock_script_files(language_dir)

        # Step 3: Create mock audio files
        logging.info("🎵 Step 3: Creating mock audio files")
        create_mock_audio_files(test_audio_dir, num_files=6)

        # Step 4: Test file copying
        logging.info("📂 Step 4: Testing file copying")
        copy_files_to_project(
            project_root=project_root,
            language_dir=language_dir,
            language=test_language,
            project_name=test_project,
            script_only=False,
            voice_only=False,
        )

        # Step 5: Verify results
        logging.info("✅ Step 5: Verifying results")

        # Check if language audio directory was created
        language_audio_dir = language_dir / "audio"
        if not language_audio_dir.exists():
            raise AssertionError(
                f"Language audio directory not created: {language_audio_dir}"
            )
        logging.info(f"✅ Language audio directory exists: {language_audio_dir}")

        # Check if audio files were copied
        mp3_files = list(language_audio_dir.glob("*.mp3"))
        wav_files = list(language_audio_dir.glob("*.wav"))
        metadata_files = list(language_audio_dir.glob("*.json"))

        if len(mp3_files) != 6:
            raise AssertionError(f"Expected 6 MP3 files, found {len(mp3_files)}")
        logging.info(f"✅ Found {len(mp3_files)} MP3 files")

        if len(wav_files) != 6:
            raise AssertionError(f"Expected 6 WAV files, found {len(wav_files)}")
        logging.info(f"✅ Found {len(wav_files)} WAV files")

        if len(metadata_files) != 1:
            raise AssertionError(
                f"Expected 1 metadata file, found {len(metadata_files)}"
            )
        logging.info(f"✅ Found {len(metadata_files)} metadata file")

        # Check if source audio directory was cleaned
        if test_audio_dir.exists() and any(test_audio_dir.iterdir()):
            raise AssertionError(
                f"Source audio directory not cleaned: {test_audio_dir}"
            )
        logging.info(f"✅ Source audio directory cleaned: {test_audio_dir}")

        # Check metadata file
        metadata_file = project_root / f"metadata_{test_language}.json"
        if not metadata_file.exists():
            raise AssertionError(f"Metadata file not created: {metadata_file}")

        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Verify metadata content
        if metadata["project"] != test_project:
            raise AssertionError(f"Wrong project in metadata: {metadata['project']}")

        if metadata["language"] != test_language:
            raise AssertionError(f"Wrong language in metadata: {metadata['language']}")

        if "audio_dir" not in metadata["generated_files"]:
            raise AssertionError("Audio directory not in metadata")

        if metadata["files_count"]["audio_files"] != 6:
            raise AssertionError(
                f"Wrong MP3 count in metadata: {metadata['files_count']['audio_files']}"
            )

        if metadata["files_count"]["wav_files"] != 6:
            raise AssertionError(
                f"Wrong WAV count in metadata: {metadata['files_count']['wav_files']}"
            )

        logging.info("✅ Metadata validation passed")

        # Step 6: Test script-only mode
        logging.info("📝 Step 6: Testing script-only mode")

        # Create new test project for script-only
        script_only_project = "test-script-only"
        script_only_root, script_only_lang_dir = create_project_structure(
            script_only_project, test_language
        )
        create_mock_script_files(script_only_lang_dir)
        create_mock_audio_files(test_audio_dir, num_files=3)  # Create some audio files

        script_only_metadata = copy_files_to_project(
            project_root=script_only_root,
            language_dir=script_only_lang_dir,
            language=test_language,
            project_name=script_only_project,
            script_only=True,
            voice_only=False,
        )

        # Audio should NOT be copied in script-only mode
        script_only_audio_dir = script_only_lang_dir / "audio"
        if script_only_audio_dir.exists():
            raise AssertionError(
                f"Audio directory should not exist in script-only mode: {script_only_audio_dir}"
            )

        if "audio_dir" in script_only_metadata["generated_files"]:
            raise AssertionError(
                "Audio directory should not be in metadata for script-only mode"
            )

        logging.info("✅ Script-only mode test passed")

        # Final success message
        logging.info("=" * 50)
        logging.info("🎉 ALL TESTS PASSED!")
        logging.info(f"📁 Test project created at: {project_root}")
        logging.info(f"🎵 Audio files placed in: {language_audio_dir}")
        logging.info(f"📊 Metadata saved at: {metadata_file}")

        return True

    except Exception as e:
        logging.error(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Clean up test data
        logging.info("🧹 Cleaning up test data...")
        if test_projects_dir.exists():
            shutil.rmtree(test_projects_dir)

        script_only_projects_dir = Path("projects") / "test-script-only"
        if script_only_projects_dir.exists():
            shutil.rmtree(script_only_projects_dir)

        if test_audio_dir.exists():
            shutil.rmtree(test_audio_dir)

        logging.info("✅ Cleanup completed")


if __name__ == "__main__":
    success = test_audio_placement()
    sys.exit(0 if success else 1)
