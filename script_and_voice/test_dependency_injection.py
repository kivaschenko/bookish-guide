#!/usr/bin/env python3
"""
Unit Tests demonstrating the benefits of Dependency Injection
"""

import unittest
from unittest.mock import Mock
import sys
from pathlib import Path

# Add the script_and_voice directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from ai_client_interface import AIClientInterface, MockAIClient
from paraphraser_with_di import ParaphraserWithDI


class TestParaphraserWithDI(unittest.TestCase):
    """Test cases showing how dependency injection improves testability"""

    def setUp(self):
        """Set up test configuration"""
        self.config = {
            "paths": {"input_file": "input.txt"},
            "script": {"paragraphs": 5, "words_per_paragraph": 50, "total_words": 250},
        }

    def test_with_mock_ai_client(self):
        """Test that we can easily inject a mock client for testing"""

        # Create mock responses
        mock_outline = {
            "sections": [
                {"title": "Test Section 1", "key_points": ["Point 1", "Point 2"]}
            ]
        }

        # Create mock client with predefined responses
        mock_client = MockAIClient(
            json_responses=[mock_outline], text_responses=["Mock text response"]
        )

        # Inject the mock client
        paraphraser = ParaphraserWithDI(mock_client, self.config)

        # Test that the paraphraser uses our mock client
        result = paraphraser.generate_outline("Test input", "english")

        self.assertEqual(result, mock_outline)
        self.assertEqual(mock_client.json_call_count, 1)

    def test_client_switching(self):
        """Test that we can easily switch between different AI providers"""

        # Mock Anthropic client
        anthropic_mock = Mock(spec=AIClientInterface)
        anthropic_mock.generate_json_response.return_value = {"provider": "anthropic"}

        # Mock OpenAI client
        openai_mock = Mock(spec=AIClientInterface)
        openai_mock.generate_json_response.return_value = {"provider": "openai"}

        # Test with Anthropic
        paraphraser_anthropic = ParaphraserWithDI(anthropic_mock, self.config)
        result_anthropic = paraphraser_anthropic.generate_outline("test", "english")
        self.assertEqual(result_anthropic["provider"], "anthropic")

        # Test with OpenAI (same class, different client!)
        paraphraser_openai = ParaphraserWithDI(openai_mock, self.config)
        result_openai = paraphraser_openai.generate_outline("test", "english")
        self.assertEqual(result_openai["provider"], "openai")

    def test_error_handling_isolation(self):
        """Test that AI client errors are properly isolated"""

        # Create a mock client that throws errors
        error_client = Mock(spec=AIClientInterface)
        error_client.generate_json_response.side_effect = Exception("API Error")

        paraphraser = ParaphraserWithDI(error_client, self.config)

        # The paraphraser should handle client errors gracefully
        with self.assertRaises(Exception) as context:
            paraphraser.generate_outline("test", "english")

        self.assertIn("API Error", str(context.exception))

    def test_configuration_independence(self):
        """Test that the paraphraser doesn't need to know about API configuration"""

        # The paraphraser only needs script configuration, not API details
        minimal_config = {
            "paths": {"input_file": "input.txt"},
            "script": {"total_words": 100},
        }

        mock_client = MockAIClient()

        # This should work fine - no API configuration needed in the paraphraser
        paraphraser = ParaphraserWithDI(mock_client, minimal_config)
        self.assertIsInstance(paraphraser.ai_client, MockAIClient)


class TestBenefitsDemo(unittest.TestCase):
    """Demonstrate the benefits of dependency injection vs tight coupling"""

    def test_benefits_comparison(self):
        """Show the key benefits of dependency injection"""

        print("\n🔄 DEPENDENCY INJECTION BENEFITS:")
        print("1. ✅ TESTABILITY: Easy to inject mock clients for unit testing")
        print(
            "2. ✅ FLEXIBILITY: Can switch between OpenAI, Anthropic, or other providers"
        )
        print(
            "3. ✅ SEPARATION OF CONCERNS: Paraphraser focuses on logic, not API management"
        )
        print("4. ✅ CONFIGURATION INDEPENDENCE: Class doesn't need API keys/secrets")
        print("5. ✅ SINGLE RESPONSIBILITY: Each class has one clear purpose")

        print("\n❌ PROBLEMS WITH CURRENT TIGHT COUPLING:")
        print("1. ❌ Hard to test: Cannot mock the API client easily")
        print("2. ❌ Inflexible: Locked into one AI provider (Anthropic)")
        print(
            "3. ❌ Mixed concerns: Class handles both paraphrasing AND API client management"
        )
        print(
            "4. ❌ Configuration dependency: Must know about API keys and config structure"
        )
        print("5. ❌ Violation of SOLID principles: Depends on concrete implementation")

        # This test always passes - it's just for demonstration
        self.assertTrue(True)


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)
