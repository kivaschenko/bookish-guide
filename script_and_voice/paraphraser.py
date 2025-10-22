#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script Paraphraser Module
This module handles the transformation of original text into structured scripts (I1, I2, I3)
using Claude API with JSON-formatted responses.
"""

import logging
import json
import os
import re
from pathlib import Path
from anthropic import Anthropic
from functools import wraps


def deprecated(func):
    """Decorator to mark functions as deprecated."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.warning(
            f"⚠️ DEPRECATED: {func.__name__} is deprecated and will be removed in future versions."
        )
        return func(*args, **kwargs)

    return wrapper


class Paraphraser:
    """
    Handles text paraphrasing using Claude API.
    Generates three deliverables: I1 (initial paraphrase), I2 (voice-over format), I3 (final script).
    """

    def __init__(self, config):
        """
        Initialize the paraphraser with configuration.

        Args:
            config (dict): Configuration loaded from config.yml
        """
        self.client = Anthropic(
            api_key=config["api"]["anthropic"]["api_key"],
            max_retries=config["api"]["anthropic"].get("max_retries", 1),
        )
        self.config = config
        # Use script_and_voice/temp directory regardless of execution location
        script_dir = Path(__file__).parent
        self.temp_path = script_dir / "temp"
        self.model = config["api"]["anthropic"]["model"]
        self.max_retries = config["api"]["anthropic"]["max_retries"]
        self.max_tokens = config["api"]["anthropic"].get("max_tokens", 4096)

        # Create temp directory if it doesn't exist
        self.temp_path.mkdir(exist_ok=True)

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
                # Use the specific input file path provided
                input_path = Path(input_file_path)
            elif project:
                # Read from project directory
                input_path = Path(f"../projects/{project}/input.txt")
            else:
                # Read from local input.txt
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

        Args:
            original_text (str): Original text to create outline from
            language (str): Language for the outline ("french" or "english")
            target_word_count (int): Target word count for the final script

        Returns:
            list: Messages formatted for OpenAI API
        """
        language_instruction = (
            "Generate the outline in FRENCH language."
            if language.lower() == "french"
            else "Generate the outline in ENGLISH language."
        )

        # Get configuration values first
        word_coefficient = self.config.get("script", {}).get("word_coefficient", 0.8)
        max_target_words = self.config.get("script", {}).get("max_target_words", 3000)
        words_per_key_point = self.config.get("script", {}).get(
            "words_per_keypoint", 80
        )
        max_keypoints_per_section = self.config.get("script", {}).get(
            "max_keypoints_per_section", 3
        )
        tone_style = self.config.get("script", {}).get(
            "tone_style", "pédagogique, rythmé, incisif, conversation orale"
        )
        target_audience = self.config.get("script", {}).get(
            "target_audience",
            "investisseurs particuliers, curieux en économie, 30–60 ans",
        )

        # Calculate target word count from input if not provided
        if target_word_count is None:
            target_word_count = len(original_text.split())

        # Calculate target word count with coefficient and max limit
        raw_target_words = int(target_word_count * word_coefficient)
        final_target_words = min(raw_target_words, max_target_words)

        # Calculate number of key_points needed
        num_key_points = max(
            3, final_target_words // words_per_key_point
        )  # Minimum 3 key_points

        # Calculate number of sections needed
        num_sections = max(
            1,
            (num_key_points + max_keypoints_per_section - 1)
            // max_keypoints_per_section,
        )

        logging.info(
            f"Word calculation: {target_word_count} → {raw_target_words} → {final_target_words} (capped at 3000)"
        )
        logging.info(
            f"Key points: {num_key_points} (target: {final_target_words} words)"
        )
        logging.info(
            f"Sections needed: {num_sections} (max {max_keypoints_per_section} keypoints per section)"
        )

        prompt = [
            {
                "role": "system",
                "content": f"""You are an expert in YouTube storytelling and high-retention video scripting.
             Create an OUTLINE for a new video optimized for retention, following the exact JSON format provided.

             LANGUAGE REQUIREMENT: {language_instruction}

             OBJECTIVE:
             - Improve retention and clarity
             - Add curiosity loops
             - Prepare for automated script generation
             - Create exactly {num_sections} sections
             - Each section should have 2-{max_keypoints_per_section} key_points
             - Total key_points should be approximately {num_key_points}

             RULES:
             - Do not copy the original text
             - Respect the JSON structure and fields strictly
             - Stay concise and actionable
             - Use oral and engaging language
             - ALL content must be in {language.upper()} language

             CONSTRAINTS:
             - JSON must be valid and ready to parse
             - Every field must be filled, even with empty string if not relevant
             - "curiosity_loop" = promise or teaser to come
             - "rhetorical_question" = thought-provoking question to make audience reflect and stay engaged
             - Each key_point should be concise (5-10 words) - just the main idea

             EXPECTED RESULT:
             Generate only the JSON, without comment or explanation.""",
            },
            {
                "role": "user",
                "content": f"""TRANSCRIPT_SOURCE:
        {original_text}

        FORMAT DE SORTIE (JSON STRICT):
        {{
          "video_meta": {{
            "title_variants": ["", "", ""],
            "tone_style": "{tone_style}",
            "target_audience": "{target_audience}",
            "estimated_words_count": {final_target_words}
          }},
          "hook": {{
            "text": "",
            "curiosity_loop": "",
            "visual_suggestion": ""
          }},
          "sections": [
            {{
              "id": 1,
              "title": "",
              "core_idea": "",
              "key_points": [
                {{"text": ""}},
                {{"text": ""}},
                {{"text": "", "target_words": {words_per_key_point}}}
              ],
              "micro_curiosity_loop": "",
              "rhetorical_question": "",
              "visual_suggestion": ""
            }},
            {{
              "id": 2,
              "title": "",
              "core_idea": "",
              "key_points": [
                {{"text": ""}},
                {{"text": ""}},
                {{"text": "", "target_words": {words_per_key_point}}}
              ],
              "micro_curiosity_loop": "",
              "rhetorical_question": "",
              "visual_suggestion": ""
            }}
          ],
          "conclusion": {{
            "summary": "",
            "final_message": "",
            "final_cta": "",
            "visual_suggestion": ""
          }},
          "global_visuals": {{
            "b_rolls": ["", ""],
            "animations": ["", ""],
            "on_screen_texts": ["", ""]
          }},
          "notes_for_writer": {{
            "pacing": "",
            "tone_tips": "",
            "emotion_curve": "",
            "storytelling_hooks": ""
          }}
        }}""",
            },
        ]

        return prompt

    def create_full_script_json(self, outline_data, language="french"):
        """
        Create full_script.json by converting key_points to micro_sections with generated content.

        Args:
            outline_data (dict): The outline data from outline.json
            language (str): Language for generation

        Returns:
            dict: Full script JSON with micro_sections
        """
        logging.info("Creating full_script.json from outline...")

        full_script = {
            "video_meta": outline_data.get("video_meta", {}),
            "hook": outline_data.get("hook", {}),
            "sections": [],
            "conclusion": outline_data.get("conclusion", {}),
            "global_visuals": outline_data.get("global_visuals", {}),
            "notes_for_writer": outline_data.get("notes_for_writer", {}),
        }

        # Process each section
        sections = outline_data.get("sections", [])
        total_sections = len(sections)

        for section_idx, section in enumerate(sections, 1):
            section_title = section.get("title", "Untitled")
            logging.info(
                f"📝 Processing section {section_idx}/{total_sections}: {section_title}"
            )

            section_data = {
                "id": section.get("id"),
                "title": section_title,
                "core_idea": section.get("core_idea"),
                "micro_curiosity_loop": section.get("micro_curiosity_loop"),
                "rhetorical_question": section.get("rhetorical_question"),
                "visual_suggestion": section.get("visual_suggestion"),
                "micro_sections": [],
            }

            # Convert each key_point to a micro_section
            key_points = section.get("key_points", [])
            total_key_points = len(key_points)

            for i, key_point in enumerate(key_points, 1):
                logging.info(
                    f"  🔹 Key point {i}/{total_key_points} in section '{section_title}'"
                )
                if isinstance(key_point, dict):
                    key_point_text = key_point.get("text", "")
                else:
                    key_point_text = str(key_point)

                # Get target_words from config (same for all key_points)
                target_words = self.config.get("script", {}).get("words_per_keypoint")
                if target_words is None:
                    raise ValueError(
                        "words_per_keypoint not found in script configuration"
                    )

                # Generate detailed paragraph for this key_point
                micro_section_prompt = self.create_micro_section_prompt(
                    key_point_text, target_words, language
                )

                # Try to generate micro_section with retry logic
                paragraph = None
                title = None

                for attempt in range(2):  # 2 attempts maximum
                    try:
                        logging.info(f"  🔄 Attempt {attempt + 1}/2 for key point {i}")
                        response = self.call_claude(micro_section_prompt)

                        if (
                            isinstance(response, dict)
                            and "paragraph" in response
                            and "title" in response
                        ):
                            paragraph = response["paragraph"]
                            title = response["title"]
                            logging.info(f"  ✅ Success on attempt {attempt + 1}")
                            break
                        else:
                            logging.warning(
                                f"  ⚠️ Invalid response format on attempt {attempt + 1}"
                            )
                            if attempt == 1:  # Last attempt
                                raise ValueError("Invalid response format from GPT-5")

                    except Exception as e:
                        logging.warning(f"  ❌ Error on attempt {attempt + 1}: {e}")
                        if attempt == 1:  # Last attempt
                            logging.error(
                                f"❌ Failed to generate micro_section {i} after 2 attempts"
                            )
                            raise Exception(
                                f"Failed to generate micro_section {i} after 2 attempts: {e}"
                            )

                if paragraph is None or title is None:
                    raise Exception(
                        f"Failed to generate micro_section {i}: No valid response received"
                    )

                micro_section = {
                    "id": i,
                    "title": title,
                    "paragraph": paragraph,
                    "target_words": target_words,
                    "actual_words": len(paragraph.split()),
                }

                section_data["micro_sections"].append(micro_section)

            full_script["sections"].append(section_data)

        return full_script

    def create_micro_section_prompt(
        self, key_point_text, target_words, language="french"
    ):
        """
        Create prompt for generating a micro_section paragraph from a key_point.

        Args:
            key_point_text (str): The key point text
            target_words (int): Target word count
            language (str): Language for generation

        Returns:
            list: Messages formatted for OpenAI API
        """
        language_styles = {
            "french": """

             - SVO, active voice, present tense, 12-18 words per sentence
             - No lists or colons and concrete first without too much comas.
             - End each block with a consequence or action
             - Address the audience in formal "vous" """,
            "english": """- Use engaging, conversational English
             - SVO, active voice, present tense, 12-18 words per sentence
             - No lists or colons, concrete first
             - End each block with a consequence or action
             - Address the audience directly""",
        }

        writing_style = language_styles.get(
            language.lower(), language_styles["english"]
        )

        prompt = [
            {
                "role": "system",
                "content": f"""
You are an expert YouTube voice-over writer. Write a clear, engaging script from a key point.

LANGUAGE: {language.upper()}

STYLE:
{writing_style}

RULES:
- Around {target_words} words
- Sound natural, like someone explaining a simple idea to a friend.
- One main idea, max two examples
- Avoid abstract, metaphors or poetic expressions
- Reply ONLY in valid JSON
- Use simple, everyday words so anyone can understand. Avoid jargon, or technical terms.
- All content in {language.upper()}
- Speak as an external and neutral observer, international perspective as a global advisor, avoid national pronouns. Use third person perspective for all countries and entities.

FORMAT: {{"title": "short descriptive title (5 words max)", "paragraph": "your generated voice-over script here"}}
""",
            },
            {
                "role": "user",
                "content": f"""KEY POINT:
{key_point_text}

Generate a short, intelligible voice-over script based on this key point.""",
            },
        ]

        return prompt

    def create_ideas_prompt(self, original_text, language="french"):
        """
        Create prompt to generate structured ideas in markdown format.

        Args:
            original_text (str): Original input text
            language (str): Language for generation

        Returns:
            list: Messages formatted for OpenAI API
        """
        # Get style configuration
        tone_style = self.config.get("script", {}).get(
            "tone_style", "pédagogique, rythmé, incisif, conversation orale"
        )
        target_audience = self.config.get("script", {}).get(
            "target_audience",
            "investisseurs particuliers, curieux en économie, 30–60 ans",
        )

        language_instructions = {
            "french": "en français",
            "english": "in English",
            "german": "auf Deutsch",
            "italian": "in italiano",
            "spanish": "en español",
            "dutch": "in het Nederlands",
            "swedish": "på svenska",
            "norwegian": "på norsk",
            "danish": "på dansk",
            "finnish": "suomeksi",
            "polish": "po polsku",
        }

        lang_instruction = language_instructions.get(language.lower(), "en français")

        prompt = [
            {
                "role": "system",
                "content": f"""You are an expert content analyst. Transform raw text into structured ideas using markdown format.

TASK: Convert the input text into a well-organized markdown document with:
- Clear sections and subsections
- Bullet points for each idea
- Logical hierarchy and flow
- All content in {lang_instruction}

STYLE REQUIREMENTS:
- Tone: {tone_style}
- Target audience: {target_audience}
- Transform the original style to match our brand voice
- Make it engaging and accessible for our audience
- Avoid copying the original author's style or phrasing

FORMAT REQUIREMENTS:
- Use # for main sections
- Use ## for subsections  
- Use ### for sub-subsections
- Use bullet points (-) for individual ideas
- Keep ideas concise but complete
- Maintain logical flow and connections
- Preserve all important information
- Make it easy to scan and understand

STRUCTURE EXAMPLE:
# Main Topic
## Key Theme 1
### Important Point A
- Specific idea 1
- Specific idea 2
### Important Point B
- Specific idea 3
- Specific idea 4

## Key Theme 2
### Important Point C
- Specific idea 5
- Specific idea 6

RESPOND ONLY WITH THE MARKDOWN CONTENT, NO ADDITIONAL TEXT.""",
            },
            {
                "role": "user",
                "content": f"""INPUT TEXT TO STRUCTURE:
{original_text}

Convert this text into structured markdown format with clear sections, subsections, and bullet points. Make it easy to understand and follow the logical flow of ideas.""",
            },
        ]

        return prompt

    @deprecated
    def create_i2_prompt(self, i1_content):
        """
        Create the prompt for I2 deliverable.

        DEPRECATED: This function is no longer used with the new outline-based system.
        Use create_outline_prompt() and create_full_script_json() instead.

        Args:
            i1_content (str): Content of I1 deliverable

        Returns:
            list: Messages formatted for OpenAI API
        """
        # DEPRECATED: This function is no longer used
        # return [
        #     {"role": "system", "content": "Transform all direct dialogue into narrative voice-over. Respond in JSON format."},
        #     {"role": "user", "content": f"""Convert this script to narrative voice-over:
        #      {i1_content}
        #
        #      Writing style:
        #      Rewrite the following text in SVO, active voice, present tense, 12-18 words per sentence, max 1 comma,
        #      no lists or colons, concrete first, 1 rhetorical question every ~100 words, short transitions
        #      (Except that. But here's the thing. And there, everything changes.), and end each block with a
        #      consequence or action. Address the audience in formal "you". Correct jargon and nominalizations.
        #      Provide only the final text.
        #
        #      Rules:
        #      1. Replace direct dialogues with "According to [name], ..." or "[name] explains that ..." and especially
        #         keep specific, educational or factual information. Remove all personal references to the YouTuber
        #         (e.g.: "like me", "I invite you", "I did", etc.), any mention of their experience, successes or training,
        #         as well as any mention of sponsors, promotions, links, calls to action, success testimonials or authority
        #         figures related to the creator or their services. The final text must be neutral, informative and
        #         without self-promotion.
        #      2. Keep the structure of {self.config['script']['paragraphs'] + 2} paragraphs, if paragraphs are missing,
        #         create new ones - DO NOT REPEAT ANY CONTENT
        #      3. For each paragraph, if it's too short (less than {self.config['script']['words_per_paragraph']} words),
        #         enrich them with new and relevant information, not with repetitions
        #      4. IMPORTANT: Each paragraph must remain unique and distinct from the others
        #      5. Respond in JSON format with structure {{"paragraphs": ["paragraph1", "paragraph2", ...]}}"""}
        # ]

        # Return empty list since function is deprecated
        return []

    @deprecated
    def create_i3_prompt(self, i2_content):
        """
        Create the prompt for I3 deliverable.

        DEPRECATED: This function is no longer used with the new outline-based system.
        Use create_outline_prompt() and create_full_script_json() instead.

        Args:
            i2_content (str): Content of I2 deliverable

        Returns:
            list: Messages formatted for OpenAI API
        """
        # DEPRECATED: This function is no longer used
        # return [
        #     {"role": "system", "content": "Verify and adjust the word count per paragraph. Respond in JSON format."},
        #     {"role": "user", "content": f"""Verify and adjust this script:
        #      {i2_content}
        #
        #      Style:
        #      Use these French verbal tics naturally in your sentences (no political correctness / corporate jargon):
        #      des, les, c'est, ce sont, en fait, donc, alors, voilà, par exemple, typiquement, en gros, autrement dit,
        #      imagine, d'abord, ensuite, aujourd'hui, clairement, attention, regardez, voyez, incroyable, énorme,
        #      dingue, fou, encore une fois
        #
        #      Rules:
        #      1. First check the number of existing paragraphs. If you already have {self.config['script']['paragraphs'] + 2}
        #         paragraphs, DO NOT REPEAT the existing content. If you have less than {self.config['script']['paragraphs'] + 2}
        #         paragraphs, create NEW paragraphs with different and original content.
        #      2. Each paragraph must be at least {self.config['script']['words_per_paragraph']} words. If a paragraph
        #         is too short, enrich it with additional information without repeating existing content.
        #      3. The total must be at least {self.config['script']['total_words']} words.
        #      4. IMPORTANT: Never repeat the same content. Each paragraph must be unique and original.
        #      5. Respond in JSON format with structure {{"paragraphs": ["paragraph1", "paragraph2", ...]}}"""}
        # ]

        # Return empty list since function is deprecated
        return []

    @deprecated
    def clean_json_response(self, content):
        """
        Clean the response to extract only valid JSON.

        DEPRECATED: This function is no longer used. JSON parsing is handled directly in call_gpt5().
        """
        # DEPRECATED: This function is no longer used
        # # Remove backticks and the word 'json' if present
        # content = re.sub(r'^```json\s*', '', content)
        # content = re.sub(r'\s*```$', '', content)
        # return content.strip()

        # Return empty string since function is deprecated
        return ""

    @deprecated
    def detect_encoding_corruption(self, content):
        """
        Detect and correct accent encoding issues in the content.

        DEPRECATED: This function is no longer used. Encoding issues are handled at the API level.

        Args:
            content (str): Content to verify

        Returns:
            tuple: (is_corrupted, cleaned_content)
        """
        # DEPRECATED: This function is no longer used
        # # Detect accent corruption patterns
        # corruption_patterns = [
        #     ('\u0000e9', 'é'), ('\u0000e8', 'è'), ('\u0000e0', 'à'), ('\u0000e7', 'ç'),
        #     ('\u0000ea', 'ê'), ('\u0000ef', 'ï'), ('\u0000ee', 'î'), ('\u0000f4', 'ô'),
        #     ('\u0000f9', 'ù'), ('\u0000fb', 'û'), ('\u0000e2', 'â'), ('\u0000c9', 'É'),
        #     ('\u0000c0', 'À'),
        # ]
        #
        # is_corrupted = False
        # cleaned_content = content
        #
        # for corrupted, correct in corruption_patterns:
        #     if corrupted in content:
        #         is_corrupted = True
        #         cleaned_content = cleaned_content.replace(corrupted, correct)
        #         logging.warning(f"Encoding correction: '{corrupted}' → '{correct}'")
        #
        # # Clean generic null characters
        # if '\u0000' in cleaned_content:
        #     is_corrupted = True
        #     cleaned_content = cleaned_content.replace('\u0000', '')
        #     logging.warning("Removed residual null characters")
        #
        # return is_corrupted, cleaned_content

        # Return safe values since function is deprecated
        return False, content

    def call_claude(self, messages, max_retries=3):
        """
        Call Claude API for JSON responses.

        Args:
            messages (list): List of message dictionaries
            max_retries (int): Maximum number of retry attempts

        Returns:
            dict: Parsed JSON response from Claude
        """
        for attempt in range(max_retries):
            try:
                # Claude API expects messages in a specific format
                # Convert system message to system parameter if present
                system_message = None
                user_messages = []

                for msg in messages:
                    if msg["role"] == "system":
                        system_message = msg["content"]
                    else:
                        user_messages.append(msg)

                # Make the API call
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

                # Extract text content from response
                content = response.content[0].text

                # Parse the JSON response from Claude
                parsed_content = json.loads(content)

                # Log the response for debugging
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
                    import time

                    time.sleep(2)
                    continue
                else:
                    raise

    def call_claude_text_only(self, messages, max_retries=3):
        """
        Call Claude API for free-text responses (not JSON).

        Args:
            messages (list): List of message dictionaries
            max_retries (int): Maximum number of retry attempts

        Returns:
            str: Text response from Claude
        """
        for attempt in range(max_retries):
            try:
                # Claude API expects messages in a specific format
                # Convert system message to system parameter if present
                system_message = None
                user_messages = []

                for msg in messages:
                    if msg["role"] == "system":
                        system_message = msg["content"]
                    else:
                        user_messages.append(msg)

                # Make the API call
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

                # Extract text content from response
                content = response.content[0].text

                # Log the response for debugging
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
                    import time

                    time.sleep(2)
                    continue
                else:
                    raise

    @deprecated
    def verify_paragraphs(self, paragraphs):
        """
        Verify that paragraphs meet constraints with a ±20% margin.

        DEPRECATED: This function is no longer used with the new outline-based system.
        Word count validation is handled in create_full_script_json().

        Args:
            paragraphs (list): List of paragraphs

        Returns:
            bool: True if constraints are met
        """
        expected_paragraphs = self.config["script"]["paragraphs"]
        # Tolerance margin of ±2 paragraphs
        min_paragraphs = expected_paragraphs - 2
        max_paragraphs = expected_paragraphs + 2

        if len(paragraphs) < min_paragraphs:
            logging.warning(
                f"Insufficient number of paragraphs: {len(paragraphs)} (minimum: {min_paragraphs})"
            )
            return False
        elif len(paragraphs) > max_paragraphs:
            logging.info(
                f"✅ Excess paragraphs: {len(paragraphs)} (expected: {expected_paragraphs} ±2)"
            )
            logging.info(
                f"ℹ️  Pipeline will automatically adapt to {len(paragraphs)} paragraphs - longer video"
            )
        else:
            logging.info(
                f"✅ Acceptable paragraph count: {len(paragraphs)} (expected: {expected_paragraphs} ±2)"
            )

        # Check for content repetition
        if self._detect_content_repetition(paragraphs):
            logging.error("❌ CONTENT REPETITION DETECTED in paragraphs!")
            return False

        # Wider tolerance: 40-70 words per paragraph
        min_words = 40
        max_words = 70

        # Identify problematic paragraphs
        problematic_paragraphs = []

        for i, para in enumerate(paragraphs, 1):
            words = len(para.split())
            if words < min_words or words > max_words:
                logging.warning(
                    f"Paragraph {i}: {words} words (out of range {min_words}-{max_words})"
                )
                problematic_paragraphs.append((i - 1, para, words))
            else:
                logging.info(f"Paragraph {i}: {words} words (in acceptable range)")

        # If paragraphs are problematic, fix them locally
        if problematic_paragraphs:
            logging.info(
                f"🔧 Local correction of {len(problematic_paragraphs)} problematic paragraph(s)"
            )
            corrected_paragraphs = self._fix_short_paragraphs(
                paragraphs, problematic_paragraphs, min_words, max_words
            )
            if corrected_paragraphs:
                # Replace original paragraphs with corrected ones
                for i, corrected_para in corrected_paragraphs.items():
                    paragraphs[i] = corrected_para
                    logging.info(
                        f"✅ Paragraph {i + 1} corrected: {len(corrected_para.split())} words"
                    )
            else:
                logging.error("❌ Local paragraph correction failed")
                return False

        # Check total word count with wider tolerance
        total_words = sum(len(para.split()) for para in paragraphs)
        min_total = int(self.config["script"]["total_words"] * 0.5)  # 50% minimum
        max_total = int(self.config["script"]["total_words"] * 2.0)  # 200% maximum

        if total_words < min_total or total_words > max_total:
            logging.warning(
                f"Total: {total_words} words (out of range {min_total}-{max_total})"
            )
            return False
        else:
            logging.info(f"Total: {total_words} words (in acceptable range)")

        return True

    @deprecated
    def _fix_short_paragraphs(
        self, paragraphs, problematic_paragraphs, min_words, max_words
    ):
        """
        Locally fix paragraphs that are too short by adding words.

        DEPRECATED: This function is no longer used with the new outline-based system.
        Word count validation is handled in create_full_script_json().

        Args:
            paragraphs (list): Complete list of paragraphs
            problematic_paragraphs (list): List of tuples (index, paragraph, word_count)
            min_words (int): Minimum required word count
            max_words (int): Maximum allowed word count

        Returns:
            dict: Dictionary {index: corrected_paragraph} or None if failed
        """
        corrected_paragraphs = {}

        for index, para, current_words in problematic_paragraphs:
            if current_words < min_words:
                # Paragraph too short - add words
                target_words = min_words + 2
                words_to_add = target_words - current_words

                logging.info(
                    f"🔧 Correcting paragraph {index + 1}: {current_words} → {target_words} words"
                )

                # Create prompt to extend paragraph
                extension_prompt = f"""
                    You are an expert writer. You must extend this paragraph by adding approximately {words_to_add} additional words, 
                    keeping the same style and meaning, without repeating information.

                    Current paragraph ({current_words} words):
                    {para}

                    Instructions:
                    - Add approximately {words_to_add} words
                    - Keep the same style and tone
                    - Don't repeat information
                    - Stay consistent with the content
                    - Return ONLY the extended paragraph, without comments

                    Extended paragraph:"""

                messages = [
                    {
                        "role": "system",
                        "content": "You are an expert writer who extends paragraphs naturally and coherently.",
                    },
                    {"role": "user", "content": extension_prompt},
                ]

                try:
                    response = self.call_claude_text_only(messages)
                    if response and isinstance(response, str):
                        # Clean the response
                        corrected_para = response.strip()
                        # Check that corrected paragraph has the right word count
                        corrected_words = len(corrected_para.split())
                        if min_words <= corrected_words <= max_words:
                            corrected_paragraphs[index] = corrected_para
                            logging.info(
                                f"✅ Paragraph {index + 1} corrected: {current_words} → {corrected_words} words"
                            )
                        else:
                            logging.warning(
                                f"⚠️ Paragraph {index + 1} still incorrect after correction: {corrected_words} words"
                            )
                    else:
                        logging.error(
                            f"❌ Invalid response for paragraph {index + 1} correction"
                        )
                except Exception as e:
                    logging.error(f"❌ Error correcting paragraph {index + 1}: {e}")

            elif current_words > max_words:
                # Paragraph too long - shorten
                target_words = max_words - 2
                words_to_remove = current_words - target_words

                logging.info(
                    f"🔧 Shortening paragraph {index + 1}: {current_words} → {target_words} words"
                )

                # Create prompt to shorten paragraph
                shortening_prompt = f"""
You are an expert writer. You must shorten this paragraph by removing approximately {words_to_remove} words, 
keeping the same style and essential information.

Current paragraph ({current_words} words):
{para}

Instructions:
- Remove approximately {words_to_remove} words
- Keep the same style and tone
- Preserve essential information
- Stay consistent with the content
- Return ONLY the shortened paragraph, without comments

Shortened paragraph:"""

                messages = [
                    {
                        "role": "system",
                        "content": "You are an expert writer who shortens paragraphs while keeping the essential.",
                    },
                    {"role": "user", "content": shortening_prompt},
                ]

                try:
                    response = self.call_claude_text_only(messages)
                    if response and isinstance(response, str):
                        # Clean the response
                        corrected_para = response.strip()
                        # Check that corrected paragraph has the right word count
                        corrected_words = len(corrected_para.split())
                        if min_words <= corrected_words <= max_words:
                            corrected_paragraphs[index] = corrected_para
                            logging.info(
                                f"✅ Paragraph {index + 1} shortened: {current_words} → {corrected_words} words"
                            )
                        else:
                            logging.warning(
                                f"⚠️ Paragraph {index + 1} still incorrect after shortening: {corrected_words} words"
                            )
                    else:
                        logging.error(
                            f"❌ Invalid response for paragraph {index + 1} shortening"
                        )
                except Exception as e:
                    logging.error(f"❌ Error shortening paragraph {index + 1}: {e}")

        return corrected_paragraphs if corrected_paragraphs else None

    @deprecated
    def _detect_content_repetition(self, paragraphs):
        """
        Detect content repetition in paragraphs.

        DEPRECATED: This function is no longer used with the new outline-based system.
        Content quality is handled by GPT-5 in create_full_script_json().

        Args:
            paragraphs (list): List of paragraphs

        Returns:
            bool: True if repetitions are detected
        """
        # Normalize paragraphs for comparison
        normalized_paragraphs = []
        for para in paragraphs:
            # Remove punctuation and convert to lowercase
            normalized = re.sub(r"[^\w\s]", "", para.lower())
            normalized_paragraphs.append(normalized)

        # Check for repetitions
        for i, para1 in enumerate(normalized_paragraphs):
            for j, para2 in enumerate(normalized_paragraphs[i + 1 :], i + 1):
                # Calculate similarity (ratio of common words)
                words1 = set(para1.split())
                words2 = set(para2.split())

                if len(words1) > 0 and len(words2) > 0:
                    similarity = len(words1.intersection(words2)) / max(
                        len(words1), len(words2)
                    )

                    # If more than 70% similarity, it's a repetition
                    if similarity > 0.7:
                        logging.error(
                            f"🚨 REPETITION DETECTED between paragraphs {i + 1} and {j + 1} (similarity: {similarity:.2f})"
                        )
                        logging.error(f"Paragraph {i + 1}: {paragraphs[i][:100]}...")
                        logging.error(f"Paragraph {j + 1}: {paragraphs[j][:100]}...")
                        return True

        logging.info("✅ No content repetition detected")
        return False

    def process(self, language="french", project=None, input_file_path=None):
        """
        Main script generation process using outline-based approach.
        Generates outline.json first, then script section by section.

        Args:
            language (str): Language for generation ("french" or "english")
            project (str): Project name (if provided, reads from ../projects/{project}/input.txt)
            input_file_path (str): Specific input file path (takes priority)

        Returns:
            dict: Dictionary with final script content and metadata
        """
        logging.info("Starting outline-based script generation process")

        # Clear temp directory before starting
        if self.temp_path.exists():
            import shutil

            shutil.rmtree(self.temp_path)
            logging.info("🧹 Temp directory cleared")

        # Recreate temp directory
        self.temp_path.mkdir(exist_ok=True)

        # Read input text
        original_text = self.read_input_text(project, input_file_path)
        logging.info("Input text read successfully")

        # Step 1: Create structured ideas from input text
        target_word_count = len(original_text.split())
        logging.info(
            f"Creating structured ideas from input text... (target: {target_word_count} words)"
        )
        ideas_messages = self.create_ideas_prompt(original_text, language)
        ideas_response = self.call_claude_text_only(ideas_messages)
        logging.info("Ideas generation completed")

        # Save ideas
        self.save_intermediate(ideas_response, "input_ideas.txt")
        logging.info("✅ Ideas saved to input_ideas.txt")

        # Step 2: Generate outline from structured ideas
        logging.info(f"Generating video outline from ideas in {language}...")
        outline_messages = self.create_outline_prompt(
            ideas_response, language, target_word_count
        )
        outline_response = self.call_claude(outline_messages)
        logging.info("Outline generation completed")

        # Save outline
        if isinstance(outline_response, dict):
            outline_json = json.dumps(outline_response, indent=2, ensure_ascii=False)
            self.save_intermediate(outline_json, "outline.json")
            logging.info("✅ Outline saved to outline.json")
        else:
            raise ValueError("Invalid response format for outline")

        # Step 2: Generate full_script.json directly from outline
        logging.info("Generating full_script.json from outline...")
        full_script_data = self.create_full_script_json(outline_response, language)
        full_script_json = json.dumps(full_script_data, indent=2, ensure_ascii=False)
        self.save_intermediate(full_script_json, "full_script.json")
        logging.info("✅ Full script JSON generated successfully")

        logging.info("Script generation process completed successfully")

        # Return script metadata
        return {
            "success": True,
            "ideas": ideas_response,
            "outline": outline_response,
            "full_script": full_script_data,
            "files": {
                "ideas": str(self.temp_path / "input_ideas.txt"),
                "outline": str(self.temp_path / "outline.json"),
                "full_script": str(self.temp_path / "full_script.json"),
            },
        }
