#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Client Interface and Implementations
Provides a common interface for different AI providers (OpenAI, Anthropic, etc.)
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union
import logging
import json
import time
from anthropic import Anthropic
from openai import OpenAI


class AIClientInterface(ABC):
    """Abstract interface for AI clients"""

    @abstractmethod
    def generate_json_response(
        self, messages: List[Dict[str, str]], max_retries: int = 3
    ) -> Dict[str, Any]:
        """Generate a JSON response from the AI model"""
        pass

    @abstractmethod
    def generate_text_response(
        self, messages: List[Dict[str, str]], max_retries: int = 3
    ) -> str:
        """Generate a text response from the AI model"""
        pass


class AnthropicClient(AIClientInterface):
    """Anthropic Claude API client implementation"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4096,
    ):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def _prepare_messages(
        self, messages: List[Dict[str, str]]
    ) -> tuple[str, List[Dict[str, str]]]:
        """Prepare messages for Anthropic API format"""
        system_message = None
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)

        return system_message, user_messages

    def generate_json_response(
        self, messages: List[Dict[str, str]], max_retries: int = 3
    ) -> Dict[str, Any]:
        """Generate a JSON response from Claude"""
        for attempt in range(max_retries):
            try:
                system_message, user_messages = self._prepare_messages(messages)

                if system_message:
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        system=system_message,
                        messages=user_messages,
                    )
                else:
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        messages=user_messages,
                    )

                content = response.content[0].text
                parsed_content = json.loads(content)

                logging.info("=== Claude JSON Response ===")
                logging.info(content)
                logging.info("=== End Response ===")

                return parsed_content

            except Exception as e:
                logging.error(
                    f"❌ Claude error (attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    logging.info("🔄 Retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                else:
                    raise

    def generate_text_response(
        self, messages: List[Dict[str, str]], max_retries: int = 3
    ) -> str:
        """Generate a text response from Claude"""
        for attempt in range(max_retries):
            try:
                system_message, user_messages = self._prepare_messages(messages)

                if system_message:
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        system=system_message,
                        messages=user_messages,
                    )
                else:
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=self.max_tokens,
                        messages=user_messages,
                    )

                content = response.content[0].text

                logging.info("=== Claude Text Response ===")
                logging.info(content)
                logging.info("=== End Text Response ===")

                return content

            except Exception as e:
                logging.error(
                    f"❌ Claude text error (attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    logging.info("🔄 Retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                else:
                    raise


class OpenAIClient(AIClientInterface):
    """OpenAI GPT API client implementation"""

    def __init__(self, api_key: str, model: str = "gpt-4", max_tokens: int = 4096):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens

    def generate_json_response(
        self, messages: List[Dict[str, str]], max_retries: int = 3
    ) -> Dict[str, Any]:
        """Generate a JSON response from OpenAI"""
        for attempt in range(max_retries):
            try:
                # Check if using GPT-5 with responses API
                if self.model == "gpt-5":
                    # Convert messages to input string for GPT-5 responses API
                    input_text = ""
                    for msg in messages:
                        if msg["role"] == "system":
                            input_text += f"SYSTEM: {msg['content']}\n\n"
                        elif msg["role"] == "user":
                            input_text += f"USER: {msg['content']}\n\n"  
                        elif msg["role"] == "assistant":
                            input_text += f"ASSISTANT: {msg['content']}\n\n"

                    response = self.client.responses.create(
                        model="gpt-5",
                        input=input_text.strip(),
                        reasoning={"effort": "low"},
                        text={"verbosity": "low", "format": {"type": "json_object"}},
                    )
                    
                    # Parse the JSON response from GPT-5
                    content = response.output_text
                    parsed_content = json.loads(content)
                else:
                    # Use standard chat completions API for other models
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=self.max_tokens,
                        response_format={"type": "json_object"},
                    )
                    
                    content = response.choices[0].message.content
                    parsed_content = json.loads(content)

                logging.info("=== OpenAI JSON Response ===")
                logging.info(content)
                logging.info("=== End Response ===")

                return parsed_content

            except Exception as e:
                logging.error(
                    f"❌ OpenAI error (attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    logging.info("🔄 Retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                else:
                    raise

    def generate_text_response(
        self, messages: List[Dict[str, str]], max_retries: int = 3
    ) -> str:
        """Generate a text response from OpenAI"""
        for attempt in range(max_retries):
            try:
                # Check if using GPT-5 with responses API
                if self.model == "gpt-5":
                    # Convert messages to input string for GPT-5 responses API
                    input_text = ""
                    for msg in messages:
                        if msg["role"] == "system":
                            input_text += f"SYSTEM: {msg['content']}\n\n"
                        elif msg["role"] == "user":
                            input_text += f"USER: {msg['content']}\n\n"
                        elif msg["role"] == "assistant":
                            input_text += f"ASSISTANT: {msg['content']}\n\n"

                    response = self.client.responses.create(
                        model="gpt-5",
                        input=input_text.strip(),
                        reasoning={"effort": "low"},
                        text={"verbosity": "low"},
                    )
                    
                    content = response.output_text
                else:
                    # Use standard chat completions API for other models
                    response = self.client.chat.completions.create(
                        model=self.model, messages=messages, max_tokens=self.max_tokens
                    )

                    content = response.choices[0].message.content

                logging.info("=== OpenAI Text Response ===")
                logging.info(content)
                logging.info("=== End Text Response ===")

                return content

            except Exception as e:
                logging.error(
                    f"❌ OpenAI text error (attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                if attempt < max_retries - 1:
                    logging.info("🔄 Retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                else:
                    raise


class MockAIClient(AIClientInterface):
    """Mock AI client for testing purposes"""

    def __init__(
        self,
        json_responses: List[Dict[str, Any]] = None,
        text_responses: List[str] = None,
    ):
        self.json_responses = json_responses or [{"mock": "response"}]
        self.text_responses = text_responses or ["Mock text response"]
        self.json_call_count = 0
        self.text_call_count = 0

    def generate_json_response(
        self, messages: List[Dict[str, str]], max_retries: int = 3
    ) -> Dict[str, Any]:
        """Return a mock JSON response"""
        response = self.json_responses[self.json_call_count % len(self.json_responses)]
        self.json_call_count += 1
        logging.info(f"=== Mock JSON Response #{self.json_call_count} ===")
        logging.info(response)
        return response

    def generate_text_response(
        self, messages: List[Dict[str, str]], max_retries: int = 3
    ) -> str:
        """Return a mock text response"""
        response = self.text_responses[self.text_call_count % len(self.text_responses)]
        self.text_call_count += 1
        logging.info(f"=== Mock Text Response #{self.text_call_count} ===")
        logging.info(response)
        return response


def create_ai_client(config: Dict[str, Any]) -> AIClientInterface:
    """Factory function to create AI client based on configuration"""
    provider = config.get("api", {}).get("provider", "openai").lower()

    if provider == "anthropic":
        return AnthropicClient(
            api_key=config["api"]["anthropic"]["api_key"],
            model=config["api"]["anthropic"]["model"],
            max_tokens=config["api"]["anthropic"].get("max_tokens", 4096),
        )
    elif provider == "openai":
        return OpenAIClient(
            api_key=config["api"]["openai"]["api_key"],
            model=config["api"]["openai"]["model"],
            max_tokens=config["api"]["openai"].get("max_tokens", 4096),
        )
    elif provider == "mock":
        return MockAIClient()
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")
