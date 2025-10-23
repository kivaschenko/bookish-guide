#!/usr/bin/env python3
"""
Test Module for module_script_and_voice.py
Tests file creation and placement with completely mocked dependencies
"""

import unittest
import tempfile
import shutil
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Mock all external dependencies before importing the module
sys.modules['anthropic'] = MagicMock()
sys.modules['requests'] = MagicMock()
sys.modules['yaml'] = MagicMock()

# Mock the Paraphraser and GeminiTTS classes
mock_paraphraser = MagicMock()
mock_gemini_tts = MagicMock()

sys.modules['paraphraser'] = MagicMock()
sys.modules['paraphraser'].Paraphraser = mock_paraphraser

sys.modules['gemini_tts'] = MagicMock()
sys.modules['gemini_tts'].GeminiTTS = mock_gemini_tts

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Now we can import the module
import module_script_and_voice


class TestModuleScriptAndVoiceFileCreation(unittest.TestCase):
    """Test cases for file creation and directory structure"""

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

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_ensure_project_dirs_creates_correct_structure(self):
        """Test that ensure_project_dirs creates the correct directory structure"""
        # Patch the PROJECTS_DIR constant
        with patch.object(module_script_and_voice, 'PROJECTS_DIR', self.test_projects_dir):
            project_root, language_dir, audio_dir = module_script_and_voice.ensure_project_dirs(
                "test-project", "english"
            )

            # Verify paths are constructed correctly
            expected_project_root = self.test_projects_dir / "test-project"
            expected_language_dir = expected_project_root / "english"
            expected_audio_dir = expected_language_dir / "audio"

            self.assertEqual(project_root, expected_project_root)
            self.assertEqual(language_dir, expected_language_dir)
            self.assertEqual(audio_dir, expected_audio_dir)

            # Verify directories actually exist
            self.assertTrue(project_root.exists(), f"Project root {project_root} should exist")
            self.assertTrue(language_dir.exists(), f"Language dir {language_dir} should exist")
            self.assertTrue(audio_dir.exists(), f"Audio dir {audio_dir} should exist")

    def test_ensure_project_dirs_handles_multiple_languages(self):
        """Test creating multiple language directories for same project"""
        with patch.object(module_script_and_voice, 'PROJECTS_DIR', self.test_projects_dir):
            # Create English version
            project_root_en, language_dir_en, audio_dir_en = module_script_and_voice.ensure_project_dirs(
                "multilang-project", "english"
            )
            
            # Create French version
            project_root_fr, language_dir_fr, audio_dir_fr = module_script_and_voice.ensure_project_dirs(
                "multilang-project", "french"
            )

            # Both should share the same project root
            self.assertEqual(project_root_en, project_root_fr)
            
            # But have different language directories
            self.assertNotEqual(language_dir_en, language_dir_fr)
            
            # Verify structure
            expected_structure = [
                self.test_projects_dir / "multilang-project",
                self.test_projects_dir / "multilang-project" / "english",
                self.test_projects_dir / "multilang-project" / "english" / "audio",
                self.test_projects_dir / "multilang-project" / "french", 
                self.test_projects_dir / "multilang-project" / "french" / "audio"
            ]
            
            for path in expected_structure:
                self.assertTrue(path.exists(), f"Path {path} should exist")

    def test_save_metadata_without_audio(self):
        """Test metadata creation for script-only generation"""
        # Setup test directories
        project_root = self.test_projects_dir / "test-project"
        language_dir = project_root / "german"
        audio_dir = language_dir / "audio"
        
        project_root.mkdir(parents=True, exist_ok=True)
        language_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Test metadata creation without audio
        metadata = module_script_and_voice.save_metadata(
            project_root, language_dir, audio_dir, 
            "test-project", "german", has_audio=False
        )

        # Verify metadata structure
        expected_metadata = {
            "project": "test-project",
            "language": "german",
            "generated_files": {
                "outline": str(language_dir / "outline.json"),
                "full_script": str(language_dir / "full_script.json"),
            }
        }

        self.assertEqual(metadata["project"], expected_metadata["project"])
        self.assertEqual(metadata["language"], expected_metadata["language"])
        self.assertEqual(metadata["generated_files"]["outline"], expected_metadata["generated_files"]["outline"])
        self.assertEqual(metadata["generated_files"]["full_script"], expected_metadata["generated_files"]["full_script"])
        self.assertNotIn("audio_dir", metadata["generated_files"])

        # Verify metadata file was created
        metadata_file = project_root / "metadata_german.json"
        self.assertTrue(metadata_file.exists(), "Metadata file should be created")

        # Verify file contents
        with open(metadata_file, "r", encoding="utf-8") as f:
            saved_metadata = json.load(f)
            self.assertEqual(saved_metadata["project"], "test-project")
            self.assertEqual(saved_metadata["language"], "german")

    def test_save_metadata_with_audio(self):
        """Test metadata creation for full generation with audio"""
        # Setup test directories
        project_root = self.test_projects_dir / "test-project"
        language_dir = project_root / "spanish"
        audio_dir = language_dir / "audio"
        
        project_root.mkdir(parents=True, exist_ok=True)
        language_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Create some fake audio files
        (audio_dir / "bullet_001.mp3").touch()
        (audio_dir / "bullet_002.mp3").touch()
        (audio_dir / "bullet_003.mp3").touch()
        (audio_dir / "test.wav").touch()
        (audio_dir / "recording.wav").touch()
        (audio_dir / "readme.txt").touch()  # Non-audio file

        # Test metadata creation with audio
        metadata = module_script_and_voice.save_metadata(
            project_root, language_dir, audio_dir, 
            "test-project", "spanish", has_audio=True
        )

        # Verify metadata includes audio information
        self.assertIn("audio_dir", metadata["generated_files"])
        self.assertEqual(metadata["generated_files"]["audio_dir"], str(audio_dir))
        self.assertEqual(metadata["files_count"]["audio_files"], 3)  # 3 mp3 files
        self.assertEqual(metadata["files_count"]["wav_files"], 2)    # 2 wav files

        # Verify metadata file was created
        metadata_file = project_root / "metadata_spanish.json"
        self.assertTrue(metadata_file.exists())

    def test_directory_structure_constants(self):
        """Test that the directory constants are properly defined"""
        # Verify BASE_DIR is set to parent of script_and_voice
        expected_base_dir = Path(__file__).parent.parent.parent  # tests -> script_and_voice -> storyforge
        self.assertEqual(module_script_and_voice.BASE_DIR, expected_base_dir)
        
        # Verify PROJECTS_DIR is BASE_DIR/projects
        expected_projects_dir = expected_base_dir / "projects"
        self.assertEqual(module_script_and_voice.PROJECTS_DIR, expected_projects_dir)

    def test_argument_file_path_handling(self):
        """Test input file path resolution logic"""
        with patch.object(module_script_and_voice, 'PROJECTS_DIR', self.test_projects_dir):
            # Test with explicit input file
            from argparse import Namespace
            test_args_explicit = Namespace(
                project='test-project',
                language='english', 
                input_file=str(self.input_file),
                script_only=True,
                audio_gemini=False,
                verbose=False
            )

            # This simulates the input file path logic from main()
            if test_args_explicit.input_file:
                input_path = Path(test_args_explicit.input_file)
            else:
                input_path = Path(f"{self.test_projects_dir}/{test_args_explicit.project}/input.txt")

            self.assertEqual(input_path, Path(str(self.input_file)))
            self.assertTrue(input_path.exists())

            # Test with default input file path
            test_args_default = Namespace(
                project='test-project',
                language='english',
                input_file=None,
                script_only=True,
                audio_gemini=False,
                verbose=False
            )

            if test_args_default.input_file:
                input_path_default = Path(test_args_default.input_file)
            else:
                input_path_default = Path(f"{self.test_projects_dir}/{test_args_default.project}/input.txt")

            expected_default_path = self.test_projects_dir / "test-project" / "input.txt"
            self.assertEqual(input_path_default, expected_default_path)

    def test_project_structure_with_real_paths(self):
        """Test complete project structure creation with realistic project names"""
        test_cases = [
            ("my-video-project", "english"),
            ("tutorial-series-ep1", "french"),
            ("product-demo", "german"),
            ("company-intro", "spanish")
        ]

        with patch.object(module_script_and_voice, 'PROJECTS_DIR', self.test_projects_dir):
            for project_name, language in test_cases:
                with self.subTest(project=project_name, language=language):
                    project_root, language_dir, audio_dir = module_script_and_voice.ensure_project_dirs(
                        project_name, language
                    )

                    # Verify the exact expected structure
                    expected_paths = [
                        self.test_projects_dir / project_name,
                        self.test_projects_dir / project_name / language,
                        self.test_projects_dir / project_name / language / "audio"
                    ]

                    for expected_path in expected_paths:
                        self.assertTrue(expected_path.exists(), 
                                      f"Expected path {expected_path} should exist for {project_name}/{language}")

                    # Verify returned paths match expected
                    self.assertEqual(project_root, self.test_projects_dir / project_name)
                    self.assertEqual(language_dir, self.test_projects_dir / project_name / language)
                    self.assertEqual(audio_dir, self.test_projects_dir / project_name / language / "audio")


if __name__ == "__main__":
    # Run tests with detailed output
    unittest.main(verbosity=2)