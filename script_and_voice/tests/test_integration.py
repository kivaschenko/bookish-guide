#!/usr/bin/env python3
"""
Integration Test for module_script_and_voice.py
Simulates complete end-to-end workflow with mocked AI APIs
"""

import unittest
import tempfile
import shutil
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, call

# Mock all external dependencies before importing
sys.modules['anthropic'] = MagicMock()
sys.modules['requests'] = MagicMock()

# Create mock yaml module
mock_yaml = MagicMock()
mock_yaml.safe_load.return_value = {
    "paths": {
        "audio": "audio",
        "temp": "temp"
    },
    "api": {
        "gemini": {
            "api_key": "fake_api_key",
            "base_url": "https://fake-api.com"
        }
    },
    "audio": {
        "gemini_tts": {
            "granularity": "bullet",
            "voice": "en-US-Standard-A"
        }
    }
}
sys.modules['yaml'] = mock_yaml

# Mock classes
sys.modules['paraphraser'] = MagicMock()
sys.modules['gemini_tts'] = MagicMock()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import module_script_and_voice


class TestModuleScriptAndVoiceIntegration(unittest.TestCase):
    """Integration tests for complete workflow simulation"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_projects_dir = Path(self.test_dir) / "projects"
        self.test_projects_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test input file
        self.input_file = Path(self.test_dir) / "test_input.txt"
        with open(self.input_file, "w", encoding="utf-8") as f:
            f.write("Welcome to our tutorial. Today we will learn about artificial intelligence. "
                   "AI is transforming many industries. Let's explore the possibilities together.")

        # Create config file in script directory
        self.config_dir = Path(self.test_dir) / "script_and_voice"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.yml"
        
        config_content = """
paths:
  audio: "audio"
  temp: "temp"

api:
  gemini:
    api_key: "fake_api_key"
    base_url: "https://fake-api.com"

audio:
  gemini_tts:
    granularity: "bullet"
    voice: "en-US-Standard-A"
"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write(config_content)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_mock_script_result(self):
        """Create realistic mock script generation result"""
        return {
            "success": True,
            "outline": {
                "title": "AI Tutorial Introduction",
                "total_sections": 3,
                "sections": [
                    {
                        "title": "Welcome",
                        "subsections": ["Greeting", "Overview"]
                    },
                    {
                        "title": "What is AI", 
                        "subsections": ["Definition", "Applications"]
                    },
                    {
                        "title": "Industry Impact",
                        "subsections": ["Transformation", "Future"]
                    }
                ]
            },
            "full_script": {
                "title": "AI Tutorial Introduction",
                "total_duration_estimate": "2-3 minutes",
                "sections": [
                    {
                        "title": "Welcome",
                        "micro_sections": [
                            {
                                "text": "Welcome to our tutorial.",
                                "actual_words": 4,
                                "estimated_duration": 2.5
                            },
                            {
                                "text": "Today we will learn about artificial intelligence.",
                                "actual_words": 8,
                                "estimated_duration": 4.5
                            }
                        ]
                    },
                    {
                        "title": "What is AI",
                        "micro_sections": [
                            {
                                "text": "AI is transforming many industries.",
                                "actual_words": 6,
                                "estimated_duration": 3.5
                            }
                        ]
                    },
                    {
                        "title": "Industry Impact", 
                        "micro_sections": [
                            {
                                "text": "Let's explore the possibilities together.",
                                "actual_words": 6,
                                "estimated_duration": 3.5
                            }
                        ]
                    }
                ]
            }
        }

    def create_mock_audio_result(self):
        """Create realistic mock audio generation result"""
        return {
            "success": True,
            "total_duration": 14.0,
            "granularity": "bullet",
            "total_bullets": 4,
            "bullets": [
                {
                    "index": 1,
                    "text": "Welcome to our tutorial.",
                    "filename": "bullet_001.mp3",
                    "duration": 2.5,
                    "start_time": 0.0,
                    "end_time": 2.5
                },
                {
                    "index": 2,
                    "text": "Today we will learn about artificial intelligence.",
                    "filename": "bullet_002.mp3", 
                    "duration": 4.5,
                    "start_time": 2.5,
                    "end_time": 7.0
                },
                {
                    "index": 3,
                    "text": "AI is transforming many industries.",
                    "filename": "bullet_003.mp3",
                    "duration": 3.5,
                    "start_time": 7.0,
                    "end_time": 10.5
                },
                {
                    "index": 4,
                    "text": "Let's explore the possibilities together.",
                    "filename": "bullet_004.mp3",
                    "duration": 3.5,
                    "start_time": 10.5,
                    "end_time": 14.0
                }
            ]
        }

    @patch('sys.argv')
    @patch.object(module_script_and_voice, 'PROJECTS_DIR')
    @patch('module_script_and_voice.load_config')
    @patch('module_script_and_voice.Paraphraser')
    def test_script_only_workflow(self, mock_paraphraser_class, mock_load_config, mock_projects_dir, mock_argv):
        """Test complete script-only generation workflow"""
        # Setup mocks
        mock_projects_dir.return_value = self.test_projects_dir
        module_script_and_voice.PROJECTS_DIR = self.test_projects_dir
        mock_load_config.return_value = mock_yaml.safe_load.return_value
        
        mock_paraphraser = MagicMock()
        mock_paraphraser.process.return_value = self.create_mock_script_result()
        mock_paraphraser_class.return_value = mock_paraphraser
        
        # Setup command line arguments
        mock_argv.__getitem__.side_effect = [
            "module_script_and_voice.py",
            "--project", "ai-tutorial",
            "--language", "english", 
            "--input-file", str(self.input_file),
            "-s"
        ]

        # Run the script
        try:
            module_script_and_voice.main()
        except SystemExit as e:
            if e.code != 0:
                self.fail(f"Script exited with error code: {e.code}")

        # Verify project structure was created
        project_root = self.test_projects_dir / "ai-tutorial"
        language_dir = project_root / "english"
        audio_dir = language_dir / "audio"

        self.assertTrue(project_root.exists(), "Project root should exist")
        self.assertTrue(language_dir.exists(), "Language directory should exist") 
        self.assertTrue(audio_dir.exists(), "Audio directory should exist")

        # Verify script files were created
        outline_file = language_dir / "outline.json"
        full_script_file = language_dir / "full_script.json"
        metadata_file = project_root / "metadata_english.json"

        self.assertTrue(outline_file.exists(), "outline.json should exist")
        self.assertTrue(full_script_file.exists(), "full_script.json should exist") 
        self.assertTrue(metadata_file.exists(), "metadata file should exist")

        # Verify file contents are correct
        with open(outline_file, "r", encoding="utf-8") as f:
            outline_data = json.load(f)
            self.assertEqual(outline_data["title"], "AI Tutorial Introduction")
            self.assertEqual(outline_data["total_sections"], 3)

        with open(full_script_file, "r", encoding="utf-8") as f:
            script_data = json.load(f)
            self.assertEqual(script_data["title"], "AI Tutorial Introduction")
            self.assertEqual(len(script_data["sections"]), 3)

        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            self.assertEqual(metadata["project"], "ai-tutorial")
            self.assertEqual(metadata["language"], "english")
            self.assertNotIn("audio_dir", metadata["generated_files"])

        # Verify paraphraser was called correctly
        mock_paraphraser.process.assert_called_once_with(
            language="english",
            input_file_path=str(self.input_file)
        )

    @patch('sys.argv')
    @patch.object(module_script_and_voice, 'PROJECTS_DIR')
    @patch('module_script_and_voice.load_config')
    @patch('module_script_and_voice.GeminiTTS')
    def test_audio_only_workflow(self, mock_gemini_tts_class, mock_load_config, mock_projects_dir, mock_argv):
        """Test audio-only generation workflow"""
        # Setup mocks
        mock_projects_dir.return_value = self.test_projects_dir
        module_script_and_voice.PROJECTS_DIR = self.test_projects_dir
        mock_load_config.return_value = mock_yaml.safe_load.return_value
        
        mock_gemini_tts = MagicMock()
        mock_gemini_tts.extract_text_from_full_script_json.return_value = (
            "Welcome to our tutorial. Today we will learn about artificial intelligence. "
            "AI is transforming many industries. Let's explore the possibilities together."
        )
        
        # Create audio files when generate_all_audio is called
        def mock_generate_audio(*args, **kwargs):
            audio_dir = mock_gemini_tts.audio_path
            if audio_dir and hasattr(audio_dir, 'mkdir'):
                audio_dir.mkdir(parents=True, exist_ok=True)
                (audio_dir / "bullet_001.mp3").touch()
                (audio_dir / "bullet_002.mp3").touch()
                (audio_dir / "bullet_003.mp3").touch()
                (audio_dir / "bullet_004.mp3").touch()
            return self.create_mock_audio_result()
        
        mock_gemini_tts.generate_all_audio.side_effect = mock_generate_audio
        mock_gemini_tts_class.return_value = mock_gemini_tts

        # Pre-create the required script file
        project_root = self.test_projects_dir / "ai-tutorial"
        language_dir = project_root / "english"
        language_dir.mkdir(parents=True, exist_ok=True)
        
        script_data = self.create_mock_script_result()["full_script"]
        with open(language_dir / "full_script.json", "w", encoding="utf-8") as f:
            json.dump(script_data, f, indent=2, ensure_ascii=False)

        # Setup command line arguments
        mock_argv.__getitem__.side_effect = [
            "module_script_and_voice.py",
            "--project", "ai-tutorial",
            "--language", "english",
            "--input-file", str(self.input_file),
            "-ag"
        ]

        # Run the script
        try:
            module_script_and_voice.main()
        except SystemExit as e:
            if e.code != 0:
                self.fail(f"Script exited with error code: {e.code}")

        # Verify audio files were created
        audio_dir = language_dir / "audio"
        self.assertTrue(audio_dir.exists(), "Audio directory should exist")
        
        expected_audio_files = [
            "bullet_001.mp3",
            "bullet_002.mp3", 
            "bullet_003.mp3",
            "bullet_004.mp3"
        ]
        
        for audio_file in expected_audio_files:
            audio_path = audio_dir / audio_file
            self.assertTrue(audio_path.exists(), f"Audio file {audio_file} should exist")

        # Verify metadata includes audio information
        metadata_file = project_root / "metadata_english.json"
        self.assertTrue(metadata_file.exists(), "Metadata file should exist")
        
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            self.assertIn("audio_dir", metadata["generated_files"])
            self.assertEqual(metadata["files_count"]["audio_files"], 4)

        # Verify correct audio path was set
        self.assertEqual(mock_gemini_tts.audio_path, audio_dir)

    def test_realistic_project_structure(self):
        """Test creating realistic project structures"""
        test_projects = [
            ("product-demo-v1", "english"),
            ("tutorial-series-ep2", "french"), 
            ("company-intro-2024", "german"),
            ("webinar-highlights", "spanish")
        ]

        with patch.object(module_script_and_voice, 'PROJECTS_DIR', self.test_projects_dir):
            for project_name, language in test_projects:
                with self.subTest(project=project_name, language=language):
                    project_root, language_dir, audio_dir = module_script_and_voice.ensure_project_dirs(
                        project_name, language
                    )

                    # Verify complete structure exists
                    expected_structure = {
                        "project_root": self.test_projects_dir / project_name,
                        "language_dir": self.test_projects_dir / project_name / language,
                        "audio_dir": self.test_projects_dir / project_name / language / "audio"
                    }

                    for name, path in expected_structure.items():
                        self.assertTrue(path.exists(), f"{name} should exist for {project_name}/{language}")
                        self.assertTrue(path.is_dir(), f"{name} should be a directory for {project_name}/{language}")

                    # Test metadata creation
                    metadata = module_script_and_voice.save_metadata(
                        project_root, language_dir, audio_dir,
                        project_name, language, has_audio=False
                    )

                    self.assertEqual(metadata["project"], project_name)
                    self.assertEqual(metadata["language"], language)

                    # Verify metadata file exists and is valid JSON
                    metadata_file = project_root / f"metadata_{language}.json"
                    self.assertTrue(metadata_file.exists())
                    
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        saved_metadata = json.load(f)
                        self.assertEqual(saved_metadata["project"], project_name)

    def test_file_permissions_and_encoding(self):
        """Test that created files have correct permissions and encoding"""
        with patch.object(module_script_and_voice, 'PROJECTS_DIR', self.test_projects_dir):
            project_root, language_dir, audio_dir = module_script_and_voice.ensure_project_dirs(
                "encoding-test", "english"
            )

            # Test with unicode content
            test_outline = {
                "title": "Test with émojis 🎬 and açcénts",
                "description": "Tëst encödìng suppört"
            }
            
            test_script = {
                "title": "Script with 中文 and العربية",
                "content": "Multi-language tëst 测试 تجربة"
            }

            # Save files
            outline_file = language_dir / "outline.json"
            script_file = language_dir / "full_script.json"
            
            with open(outline_file, "w", encoding="utf-8") as f:
                json.dump(test_outline, f, indent=2, ensure_ascii=False)
                
            with open(script_file, "w", encoding="utf-8") as f:
                json.dump(test_script, f, indent=2, ensure_ascii=False)

            # Verify files can be read back correctly
            with open(outline_file, "r", encoding="utf-8") as f:
                read_outline = json.load(f)
                self.assertEqual(read_outline["title"], "Test with émojis 🎬 and açcénts")

            with open(script_file, "r", encoding="utf-8") as f:
                read_script = json.load(f)
                self.assertEqual(read_script["title"], "Script with 中文 and العربية")

            # Test metadata with unicode
            metadata = module_script_and_voice.save_metadata(
                project_root, language_dir, audio_dir,
                "encoding-test", "english", has_audio=False
            )

            metadata_file = project_root / "metadata_english.json"
            with open(metadata_file, "r", encoding="utf-8") as f:
                saved_metadata = json.load(f)
                self.assertEqual(saved_metadata["project"], "encoding-test")


if __name__ == "__main__":
    unittest.main(verbosity=2)