#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Refactored Paraphraser with Dependency Injection
This demonstrates how the Paraphraser class would look with proper dependency injection
"""

import logging
import json
import os
import re
from pathlib import Path
from functools import wraps
from ai_client_interface import AIClientInterface, create_ai_client


def deprecated(func):
    """Decorator to mark functions as deprecated."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.warning(
            f"⚠️ DEPRECATED: {func.__name__} is deprecated and will be removed in future versions."
        )
        return func(*args, **kwargs)

    return wrapper


class ParaphraserWithDI:
    """
    Handles text paraphrasing using dependency injection for AI client.
    Generates three deliverables: I1 (initial paraphrase), I2 (voice-over format), I3 (final script).
    """

    def __init__(self, ai_client: AIClientInterface, config: dict):
        """
        Initialize the paraphraser with an injected AI client.

        Args:
            ai_client (AIClientInterface): Injected AI client (Anthropic, OpenAI, Mock, etc.)
            config (dict): Configuration for script generation parameters
        """
        self.ai_client = ai_client
        self.config = config

        # Use script_and_voice/temp directory regardless of execution location
        script_dir = Path(__file__).parent
        self.temp_path = script_dir / "temp"

        # Create temp directory if it doesn't exist
        self.temp_path.mkdir(exist_ok=True)

    @classmethod
    def create_from_config(cls, config: dict) -> "ParaphraserWithDI":
        """
        Factory method to create Paraphraser with AI client from configuration.

        Args:
            config (dict): Configuration loaded from config.yml

        Returns:
            ParaphraserWithDI: Configured instance
        """
        ai_client = create_ai_client(config)
        return cls(ai_client, config)

    def read_input_text(self, project=None, input_file_path=None):
        """
        Read the input.txt file.

        Args:
            project (str): Project name (if provided, reads from ../projects/{project}/input.txt)
            input_file_path (str): Specific input file path (takes priority)

        Returns:
            str: Content of input.txt
        """
        try:
            if input_file_path:
                input_path = Path(input_file_path)
            elif project:
                input_path = Path(f"../projects/{project}/input.txt")
            else:
                input_path = Path(self.config["paths"]["input_file"])

            with open(input_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            logging.error(f"Error reading input.txt: {e}")
            raise

    def save_intermediate(self, content, filename):
        """
        Save an intermediate deliverable.

        Args:
            content (str): Content to save
            filename (str): Filename for saving
        """
        filepath = self.temp_path / filename
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logging.info(f"File {filename} saved successfully")
        except Exception as e:
            logging.error(f"Error saving {filename}: {e}")
            raise

    def create_outline_prompt(
        self, original_text, language="french", target_word_count=None
    ):
        """
        Create the prompt for outline generation.
        """
        # Implementation would be the same as original, just using self.ai_client
        pass

    def generate_outline(
        self, original_text, language="french", target_word_count=None
    ):
        """
        Generate an outline using the injected AI client.
        """
        messages = self.create_outline_prompt(
            original_text, language, target_word_count
        )

        # Use dependency-injected AI client instead of hardcoded API calls
        outline_response = self.ai_client.generate_json_response(messages)

        return outline_response

    def generate_micro_section(self, key_point_text, target_words, language="french"):
        """
        Generate a micro section using the injected AI client.
        """
        messages = self.create_micro_section_prompt(
            key_point_text, target_words, language
        )

        # Use dependency-injected AI client
        response = self.ai_client.generate_json_response(messages)

        return response

    def process(self, language="french", input_file_path=None, project=None):
        """
        Main processing method that orchestrates the entire paraphrasing workflow.

        Args:
            language (str): Target language
            input_file_path (str): Path to input file
            project (str): Project name

        Returns:
            dict: Processing results
        """
        try:
            # Read input
            original_text = self.read_input_text(project, input_file_path)

            # Generate outline using injected AI client
            outline = self.generate_outline(original_text, language)

            # Process sections using injected AI client
            # ... rest of the processing logic

            return {
                "success": True,
                "outline": outline,
                # ... other results
            }

        except Exception as e:
            logging.error(f"Processing error: {e}")
            return {"success": False, "error": str(e)}


# Example usage demonstrating the flexibility of dependency injection
def example_usage():
    """Example showing how to use the refactored Paraphraser with different AI providers"""

    # Load configuration
    import yaml

    with open("config.yml", "r") as f:
        config = yaml.safe_load(f)

    # Method 1: Use factory method (recommended for normal usage)
    paraphraser = ParaphraserWithDI.create_from_config(config)

    # Method 2: Inject specific client (useful for testing or specific scenarios)
    from ai_client_interface import AnthropicClient, MockAIClient

    # For production with Anthropic
    anthropic_client = AnthropicClient(
        api_key="your-key", model="claude-3-5-sonnet-20241022"
    )
    paraphraser_anthropic = ParaphraserWithDI(anthropic_client, config)

    # For testing with mock client
    mock_responses = [
        {"sections": [{"title": "Test Section", "key_points": ["Test point"]}]},
        {"content": "Test micro section content"},
    ]
    mock_client = MockAIClient(json_responses=mock_responses)
    paraphraser_test = ParaphraserWithDI(mock_client, config)

    # For switching between providers at runtime
    if config.get("use_fallback_provider"):
        from ai_client_interface import OpenAIClient

        openai_client = OpenAIClient(
            api_key=config["api"]["openai"]["api_key"],
            model=config["api"]["openai"]["model"],
        )
        paraphraser = ParaphraserWithDI(openai_client, config)


if __name__ == "__main__":
    example_usage()
