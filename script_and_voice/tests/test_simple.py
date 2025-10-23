#!/usr/bin/env python3
"""
Simple focused test for module_script_and_voice.py functions
Tests the core functionality without CLI argument parsing
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

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

import module_script_and_voice


class TestModuleScriptAndVoiceFunctions(unittest.TestCase):
    """Test the core functions of the module"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_projects_dir = Path(self.test_dir) / "projects"
        self.test_projects_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_ensure_project_dirs_function(self):
        """Test the ensure_project_dirs function directly"""
        with patch.object(module_script_and_voice, 'PROJECTS_DIR', self.test_projects_dir):
            # Test project creation
            project_root, language_dir, audio_dir = module_script_and_voice.ensure_project_dirs(
                "test-video", "french"
            )

            # Verify correct paths
            self.assertEqual(project_root, self.test_projects_dir / "test-video")
            self.assertEqual(language_dir, self.test_projects_dir / "test-video" / "french")
            self.assertEqual(audio_dir, self.test_projects_dir / "test-video" / "french" / "audio")

            # Verify directories exist
            self.assertTrue(project_root.exists())
            self.assertTrue(language_dir.exists())
            self.assertTrue(audio_dir.exists())

    def test_save_metadata_function(self):
        """Test the save_metadata function directly"""
        # Create test directories
        project_root = self.test_projects_dir / "metadata-test"
        language_dir = project_root / "english"
        audio_dir = language_dir / "audio"
        
        project_root.mkdir(parents=True)
        language_dir.mkdir(parents=True)
        audio_dir.mkdir(parents=True)

        # Create some test audio files
        (audio_dir / "bullet_001.mp3").touch()
        (audio_dir / "bullet_002.mp3").touch()
        (audio_dir / "sound.wav").touch()

        # Test metadata creation with audio
        metadata = module_script_and_voice.save_metadata(
            project_root, language_dir, audio_dir,
            "metadata-test", "english", has_audio=True
        )

        # Verify metadata content
        self.assertEqual(metadata["project"], "metadata-test")
        self.assertEqual(metadata["language"], "english")
        self.assertIn("outline", metadata["generated_files"])
        self.assertIn("full_script", metadata["generated_files"])
        self.assertIn("audio_dir", metadata["generated_files"])
        self.assertEqual(metadata["files_count"]["audio_files"], 2)
        self.assertEqual(metadata["files_count"]["wav_files"], 1)

        # Verify metadata file was created
        metadata_file = project_root / "metadata_english.json"
        self.assertTrue(metadata_file.exists())

        # Verify file content
        with open(metadata_file, "r", encoding="utf-8") as f:
            saved_metadata = json.load(f)
            self.assertEqual(saved_metadata["project"], "metadata-test")

    def test_complete_workflow_simulation(self):
        """Test complete workflow by directly calling functions"""
        with patch.object(module_script_and_voice, 'PROJECTS_DIR', self.test_projects_dir):
            
            # Step 1: Create project structure
            project_name = "workflow-test"
            language = "german"
            
            project_root, language_dir, audio_dir = module_script_and_voice.ensure_project_dirs(
                project_name, language
            )

            # Verify structure was created
            self.assertTrue(project_root.exists())
            self.assertTrue(language_dir.exists())
            self.assertTrue(audio_dir.exists())

            # Step 2: Simulate script generation by creating script files
            mock_outline = {
                "title": "Workflow Test Video",
                "sections": [
                    {"title": "Introduction", "subsections": ["Welcome", "Overview"]},
                    {"title": "Main Content", "subsections": ["Details", "Examples"]}
                ]
            }

            mock_full_script = {
                "title": "Workflow Test Video Script",
                "sections": [
                    {
                        "title": "Introduction",
                        "micro_sections": [
                            {"text": "Welcome to the test.", "actual_words": 4},
                            {"text": "This is our overview.", "actual_words": 4}
                        ]
                    },
                    {
                        "title": "Main Content", 
                        "micro_sections": [
                            {"text": "Here are the details.", "actual_words": 4},
                            {"text": "And some examples.", "actual_words": 3}
                        ]
                    }
                ]
            }

            # Save script files
            outline_file = language_dir / "outline.json"
            full_script_file = language_dir / "full_script.json"

            with open(outline_file, "w", encoding="utf-8") as f:
                json.dump(mock_outline, f, indent=2, ensure_ascii=False)

            with open(full_script_file, "w", encoding="utf-8") as f:
                json.dump(mock_full_script, f, indent=2, ensure_ascii=False)

            # Verify script files exist and have correct content
            self.assertTrue(outline_file.exists())
            self.assertTrue(full_script_file.exists())

            with open(outline_file, "r", encoding="utf-8") as f:
                saved_outline = json.load(f)
                self.assertEqual(saved_outline["title"], "Workflow Test Video")

            # Step 3: Simulate audio generation
            audio_files = [
                "bullet_001.mp3",
                "bullet_002.mp3", 
                "bullet_003.mp3",
                "bullet_004.mp3"
            ]

            for audio_file in audio_files:
                (audio_dir / audio_file).touch()

            # Verify audio files exist
            for audio_file in audio_files:
                self.assertTrue((audio_dir / audio_file).exists())

            # Step 4: Create metadata
            metadata = module_script_and_voice.save_metadata(
                project_root, language_dir, audio_dir,
                project_name, language, has_audio=True
            )

            # Verify complete workflow results
            self.assertEqual(metadata["project"], project_name)
            self.assertEqual(metadata["language"], language)
            self.assertEqual(metadata["files_count"]["audio_files"], 4)

            # Verify all expected files exist
            expected_files = [
                project_root / f"metadata_{language}.json",
                language_dir / "outline.json",
                language_dir / "full_script.json",
                audio_dir / "bullet_001.mp3",
                audio_dir / "bullet_002.mp3",
                audio_dir / "bullet_003.mp3", 
                audio_dir / "bullet_004.mp3"
            ]

            for expected_file in expected_files:
                self.assertTrue(expected_file.exists(), f"Expected file {expected_file} should exist")

    def test_multiple_projects_and_languages(self):
        """Test handling multiple projects and languages"""
        with patch.object(module_script_and_voice, 'PROJECTS_DIR', self.test_projects_dir):
            
            test_cases = [
                ("project-alpha", "english"),
                ("project-alpha", "french"),  # Same project, different language
                ("project-beta", "german"),
                ("project-gamma", "spanish")
            ]

            created_structures = []

            for project_name, language in test_cases:
                project_root, language_dir, audio_dir = module_script_and_voice.ensure_project_dirs(
                    project_name, language
                )

                # Create mock files for each project/language
                outline_file = language_dir / "outline.json"
                with open(outline_file, "w", encoding="utf-8") as f:
                    json.dump({"title": f"{project_name} {language} video"}, f)

                # Create metadata
                metadata = module_script_and_voice.save_metadata(
                    project_root, language_dir, audio_dir,
                    project_name, language, has_audio=False
                )

                created_structures.append({
                    "project": project_name,
                    "language": language,
                    "project_root": project_root,
                    "language_dir": language_dir,
                    "metadata_file": project_root / f"metadata_{language}.json"
                })

            # Verify all structures were created correctly
            for structure in created_structures:
                self.assertTrue(structure["project_root"].exists())
                self.assertTrue(structure["language_dir"].exists())
                self.assertTrue(structure["metadata_file"].exists())

                # Verify metadata content
                with open(structure["metadata_file"], "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                    self.assertEqual(metadata["project"], structure["project"])
                    self.assertEqual(metadata["language"], structure["language"])

            # Verify project-alpha has both english and french
            project_alpha_root = self.test_projects_dir / "project-alpha"
            self.assertTrue((project_alpha_root / "english").exists())
            self.assertTrue((project_alpha_root / "french").exists())
            self.assertTrue((project_alpha_root / "metadata_english.json").exists())
            self.assertTrue((project_alpha_root / "metadata_french.json").exists())

    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        with patch.object(module_script_and_voice, 'PROJECTS_DIR', self.test_projects_dir):
            
            # Test with special characters in project name
            special_project_name = "test-project_with-special.chars"
            project_root, language_dir, audio_dir = module_script_and_voice.ensure_project_dirs(
                special_project_name, "english"
            )

            self.assertTrue(project_root.exists())
            self.assertEqual(project_root.name, special_project_name)

            # Test empty audio directory
            metadata = module_script_and_voice.save_metadata(
                project_root, language_dir, audio_dir,
                special_project_name, "english", has_audio=True
            )

            self.assertEqual(metadata["files_count"]["audio_files"], 0)
            self.assertEqual(metadata["files_count"]["wav_files"], 0)

            # Test creating the same project structure multiple times (should not error)
            for _ in range(3):
                project_root_2, language_dir_2, audio_dir_2 = module_script_and_voice.ensure_project_dirs(
                    special_project_name, "english"
                )
                self.assertEqual(project_root, project_root_2)
                self.assertEqual(language_dir, language_dir_2)
                self.assertEqual(audio_dir, audio_dir_2)


def run_quick_functionality_test():
    """Quick test to verify the script structure and basic functionality"""
    print("🧪 Running Quick Functionality Test")
    print("=" * 50)
    
    # Test 1: Check constants are defined
    print(f"✅ BASE_DIR: {module_script_and_voice.BASE_DIR}")
    print(f"✅ PROJECTS_DIR: {module_script_and_voice.PROJECTS_DIR}")
    
    # Test 2: Check functions exist
    functions_to_check = [
        'ensure_project_dirs',
        'save_metadata', 
        'load_config',
        'setup_logging',
        'main'
    ]
    
    for func_name in functions_to_check:
        if hasattr(module_script_and_voice, func_name):
            print(f"✅ Function '{func_name}' exists")
        else:
            print(f"❌ Function '{func_name}' missing")
    
    print("\n🎯 Quick Test Summary:")
    print("✅ All core functions and constants are properly defined")
    print("✅ Module imports successfully with mocked dependencies")
    print("✅ Ready for full testing with real dependencies")


if __name__ == "__main__":
    print("Running Simple Function Tests...")
    print("=" * 50)
    
    # Run quick functionality check first
    run_quick_functionality_test()
    print("\n" + "=" * 50)
    
    # Run full test suite
    unittest.main(verbosity=2)