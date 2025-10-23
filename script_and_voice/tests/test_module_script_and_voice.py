#!/usr/bin/env python3
"""
Test Module for module_script_and_voice.py
Tests file creation and placement with mocked AI APIs
"""

import unittest
import tempfile
import shutil
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import module_script_and_voice


class TestModuleScriptAndVoice(unittest.TestCase):
    """Test cases for module_script_and_voice.py functionality"""

    def setUp(self):
        """Set up test environment with temporary directories"""
        # Create temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.test_projects_dir = Path(self.test_dir) / "projects"
        self.test_projects_dir.mkdir(parents=True, exist_ok=True)
        
        # Create temporary input file
        self.input_file = Path(self.test_dir) / "test_input.txt"
        with open(self.input_file, "w", encoding="utf-8") as f:
            f.write("This is a test input for script generation.")
        
        # Mock config data
        self.mock_config = {
            "paths": {
                "audio": "audio",
                "temp": "temp"
            },
            "api": {
                "gemini": {
                    "api_key": "fake_key",
                    "base_url": "fake_url"
                }
            },
            "audio": {
                "gemini_tts": {
                    "granularity": "bullet",
                    "voice": "en-US-Standard-A"
                }
            }
        }

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_mock_paraphraser_result(self):
        """Create mock result from Paraphraser.process()"""
        return {
            "success": True,
            "outline": {
                "title": "Test Video",
                "sections": [
                    {
                        "title": "Introduction",
                        "subsections": ["Overview", "Goals"]
                    }
                ]
            },
            "full_script": {
                "title": "Test Video Script",
                "sections": [
                    {
                        "title": "Introduction",
                        "micro_sections": [
                            {
                                "text": "Welcome to our test video.",
                                "actual_words": 5
                            },
                            {
                                "text": "Today we will explore testing.",
                                "actual_words": 6
                            }
                        ]
                    }
                ]
            }
        }

    def create_mock_gemini_tts_result(self):
        """Create mock result from GeminiTTS.generate_all_audio()"""
        return {
            "success": True,
            "total_duration": 15.5,
            "granularity": "bullet",
            "total_bullets": 2,
            "bullets": [
                {
                    "index": 1,
                    "text": "Welcome to our test video.",
                    "filename": "bullet_001.mp3",
                    "duration": 7.2,
                    "start_time": 0.0,
                    "end_time": 7.2
                },
                {
                    "index": 2,
                    "text": "Today we will explore testing.",
                    "filename": "bullet_002.mp3",
                    "duration": 8.3,
                    "start_time": 7.2,
                    "end_time": 15.5
                }
            ]
        }

    @patch('module_script_and_voice.PROJECTS_DIR')
    @patch('module_script_and_voice.load_config')
    @patch('module_script_and_voice.Paraphraser')
    def test_script_only_generation(self, mock_paraphraser_class, mock_load_config, mock_projects_dir):
        """Test script-only generation (-s flag)"""
        # Setup mocks
        mock_projects_dir.return_value = self.test_projects_dir
        mock_load_config.return_value = self.mock_config
        mock_paraphraser = MagicMock()
        mock_paraphraser.process.return_value = self.create_mock_paraphraser_result()
        mock_paraphraser_class.return_value = mock_paraphraser
        
        # Override PROJECTS_DIR constant
        module_script_and_voice.PROJECTS_DIR = self.test_projects_dir

        # Test arguments
        test_args = [
            "module_script_and_voice.py",
            "--project", "test-project",
            "--language", "english",
            "--input-file", str(self.input_file),
            "-s"
        ]

        with patch('sys.argv', test_args):
            try:
                module_script_and_voice.main()
            except SystemExit as e:
                # main() calls sys.exit(1) on errors, sys.exit(0) on success
                # We expect success (no exit) or exit(0)
                if e.code != 0:
                    self.fail(f"Script exited with error code: {e.code}")

        # Verify project structure was created
        project_root = self.test_projects_dir / "test-project"
        language_dir = project_root / "english"
        audio_dir = language_dir / "audio"
        
        self.assertTrue(project_root.exists(), "Project root directory should exist")
        self.assertTrue(language_dir.exists(), "Language directory should exist")
        self.assertTrue(audio_dir.exists(), "Audio directory should exist")

        # Verify script files were created
        outline_file = language_dir / "outline.json"
        full_script_file = language_dir / "full_script.json"
        metadata_file = project_root / "metadata_english.json"

        self.assertTrue(outline_file.exists(), "outline.json should exist")
        self.assertTrue(full_script_file.exists(), "full_script.json should exist")
        self.assertTrue(metadata_file.exists(), "metadata file should exist")

        # Verify file contents
        with open(outline_file, "r", encoding="utf-8") as f:
            outline_data = json.load(f)
            self.assertEqual(outline_data["title"], "Test Video")

        with open(full_script_file, "r", encoding="utf-8") as f:
            script_data = json.load(f)
            self.assertEqual(script_data["title"], "Test Video Script")

        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            self.assertEqual(metadata["project"], "test-project")
            self.assertEqual(metadata["language"], "english")
            self.assertIn("outline", metadata["generated_files"])
            self.assertIn("full_script", metadata["generated_files"])

        # Verify paraphraser was called correctly
        mock_paraphraser.process.assert_called_once_with(
            language="english",
            input_file_path=str(self.input_file)
        )

    @patch('module_script_and_voice.PROJECTS_DIR')
    @patch('module_script_and_voice.load_config')
    @patch('module_script_and_voice.GeminiTTS')
    def test_audio_only_generation(self, mock_gemini_tts_class, mock_load_config, mock_projects_dir):
        """Test audio-only generation (-ag flag)"""
        # Setup mocks
        mock_projects_dir.return_value = self.test_projects_dir
        mock_load_config.return_value = self.mock_config
        mock_gemini_tts = MagicMock()
        mock_gemini_tts.extract_text_from_full_script_json.return_value = "Welcome to our test video. Today we will explore testing."
        mock_gemini_tts.generate_all_audio.return_value = self.create_mock_gemini_tts_result()
        mock_gemini_tts_class.return_value = mock_gemini_tts
        
        # Override PROJECTS_DIR constant
        module_script_and_voice.PROJECTS_DIR = self.test_projects_dir

        # Create pre-existing script files (required for audio generation)
        project_root = self.test_projects_dir / "test-project"
        language_dir = project_root / "english"
        language_dir.mkdir(parents=True, exist_ok=True)
        
        full_script_data = self.create_mock_paraphraser_result()["full_script"]
        with open(language_dir / "full_script.json", "w", encoding="utf-8") as f:
            json.dump(full_script_data, f, indent=2, ensure_ascii=False)

        # Create fake audio files that would be generated
        audio_dir = language_dir / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Simulate audio file creation
        def mock_generate_audio(*args, **kwargs):
            # Create fake audio files
            (audio_dir / "bullet_001.mp3").touch()
            (audio_dir / "bullet_002.mp3").touch()
            return self.create_mock_gemini_tts_result()
        
        mock_gemini_tts.generate_all_audio.side_effect = mock_generate_audio

        # Test arguments
        test_args = [
            "module_script_and_voice.py",
            "--project", "test-project",
            "--language", "english",
            "--input-file", str(self.input_file),
            "-ag"
        ]

        with patch('sys.argv', test_args):
            try:
                module_script_and_voice.main()
            except SystemExit as e:
                if e.code != 0:
                    self.fail(f"Script exited with error code: {e.code}")

        # Verify audio files were created
        self.assertTrue((audio_dir / "bullet_001.mp3").exists(), "bullet_001.mp3 should exist")
        self.assertTrue((audio_dir / "bullet_002.mp3").exists(), "bullet_002.mp3 should exist")

        # Verify metadata includes audio information
        metadata_file = project_root / "metadata_english.json"
        self.assertTrue(metadata_file.exists(), "metadata file should exist")
        
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            self.assertIn("audio_dir", metadata["generated_files"])
            self.assertEqual(metadata["files_count"]["audio_files"], 2)

        # Verify audio_path was set correctly
        self.assertEqual(mock_gemini_tts.audio_path, audio_dir)

    @patch('module_script_and_voice.PROJECTS_DIR')
    @patch('module_script_and_voice.load_config')
    @patch('module_script_and_voice.Paraphraser')
    @patch('module_script_and_voice.GeminiTTS')
    def test_full_generation(self, mock_gemini_tts_class, mock_paraphraser_class, mock_load_config, mock_projects_dir):
        """Test full generation (both script and audio)"""
        # Setup mocks
        mock_projects_dir.return_value = self.test_projects_dir
        mock_load_config.return_value = self.mock_config
        
        mock_paraphraser = MagicMock()
        mock_paraphraser.process.return_value = self.create_mock_paraphraser_result()
        mock_paraphraser_class.return_value = mock_paraphraser
        
        mock_gemini_tts = MagicMock()
        mock_gemini_tts.extract_text_from_full_script_json.return_value = "Welcome to our test video. Today we will explore testing."
        mock_gemini_tts.generate_all_audio.return_value = self.create_mock_gemini_tts_result()
        mock_gemini_tts_class.return_value = mock_gemini_tts
        
        # Override PROJECTS_DIR constant
        module_script_and_voice.PROJECTS_DIR = self.test_projects_dir

        # Test arguments (no flags = full generation)
        test_args = [
            "module_script_and_voice.py",
            "--project", "test-project",
            "--language", "french",
            "--input-file", str(self.input_file)
        ]

        with patch('sys.argv', test_args):
            try:
                module_script_and_voice.main()
            except SystemExit as e:
                if e.code != 0:
                    self.fail(f"Script exited with error code: {e.code}")

        # Verify complete project structure
        project_root = self.test_projects_dir / "test-project"
        language_dir = project_root / "french"
        audio_dir = language_dir / "audio"
        
        self.assertTrue(project_root.exists())
        self.assertTrue(language_dir.exists())
        self.assertTrue(audio_dir.exists())

        # Verify all files were created
        self.assertTrue((language_dir / "outline.json").exists())
        self.assertTrue((language_dir / "full_script.json").exists())
        self.assertTrue((project_root / "metadata_french.json").exists())

        # Verify both components were called
        mock_paraphraser.process.assert_called_once()
        mock_gemini_tts.generate_all_audio.assert_called_once()

    def test_ensure_project_dirs(self):
        """Test ensure_project_dirs function creates correct structure"""
        # Override PROJECTS_DIR for this test
        module_script_and_voice.PROJECTS_DIR = self.test_projects_dir
        
        project_root, language_dir, audio_dir = module_script_and_voice.ensure_project_dirs(
            "my-test-project", "spanish"
        )

        # Verify paths are correct
        expected_project_root = self.test_projects_dir / "my-test-project"
        expected_language_dir = expected_project_root / "spanish"
        expected_audio_dir = expected_language_dir / "audio"

        self.assertEqual(project_root, expected_project_root)
        self.assertEqual(language_dir, expected_language_dir)
        self.assertEqual(audio_dir, expected_audio_dir)

        # Verify directories were created
        self.assertTrue(project_root.exists())
        self.assertTrue(language_dir.exists())
        self.assertTrue(audio_dir.exists())

    def test_save_metadata(self):
        """Test save_metadata function creates correct metadata file"""
        # Setup test directories
        project_root = self.test_projects_dir / "test-project"
        language_dir = project_root / "german"
        audio_dir = language_dir / "audio"
        
        project_root.mkdir(parents=True, exist_ok=True)
        language_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Create some fake audio files
        (audio_dir / "bullet_001.mp3").touch()
        (audio_dir / "bullet_002.mp3").touch()
        (audio_dir / "test.wav").touch()

        # Test metadata creation with audio
        metadata = module_script_and_voice.save_metadata(
            project_root, language_dir, audio_dir, 
            "test-project", "german", has_audio=True
        )

        # Verify metadata structure
        self.assertEqual(metadata["project"], "test-project")
        self.assertEqual(metadata["language"], "german")
        self.assertIn("outline", metadata["generated_files"])
        self.assertIn("full_script", metadata["generated_files"])
        self.assertIn("audio_dir", metadata["generated_files"])
        self.assertEqual(metadata["files_count"]["audio_files"], 2)
        self.assertEqual(metadata["files_count"]["wav_files"], 1)

        # Verify metadata file was created
        metadata_file = project_root / "metadata_german.json"
        self.assertTrue(metadata_file.exists())

        # Verify file contents
        with open(metadata_file, "r", encoding="utf-8") as f:
            saved_metadata = json.load(f)
            self.assertEqual(saved_metadata, metadata)


if __name__ == "__main__":
    unittest.main()