#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script Paraphraser Module
This module handles the transformation of original text into structured scripts (I1, I2, I3)
using configurable AI API with JSON-formatted responses.
"""

import logging
import json
import re
from pathlib import Path
from functools import wraps

# Import AI client interface and factory
try:
    from ai_client_interface import create_ai_client
except ImportError:
    # Fallback for direct imports
    from .ai_client_interface import create_ai_client


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
    Handles text paraphrasing using configurable AI API.
    Generates three deliverables: I1 (initial paraphrase), I2 (voice-over format), I3 (final script).
    """

    def __init__(self, config):
        """
        Initialize the paraphraser with configuration.

        Args:
            config (dict): Configuration loaded from config.yml
        """
        # Create AI client based on provider configuration
        self.ai_client = create_ai_client(config)
        self.config = config

        # Use script_and_voice/temp directory regardless of execution location
        script_dir = Path(__file__).parent
        self.temp_path = script_dir / "temp"

        # Get provider-specific settings
        provider = config.get("api", {}).get("provider", "openai")
        if provider == "anthropic":
            self.max_retries = config["api"]["anthropic"].get("max_retries", 3)
        elif provider == "openai":
            self.max_retries = config["api"]["openai"].get("max_retries", 3)
        else:
            self.max_retries = 3

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

        # Language-specific examples for hooks, curiosity loops, and key points
        if language.lower() == "french":
            examples_block = """
HOOK EXAMPLES (First 10 seconds - must grab attention):
❌ BAD: "Aujourd'hui on parle d'inflation" (boring, generic)
❌ BAD: "Bonjour, je vais vous expliquer l'investissement" (slow start)
✅ GOOD: "En 2023, l'inflation a volé 1 400€ à chaque Français. Voici comment les récupérer."
✅ GOOD: "Warren Buffett a gagné 47% pendant la crise de 2008 avec une technique simple. Je vous la montre."

CURIOSITY LOOP EXAMPLES (Promise that keeps them watching):
❌ BAD: "Nous verrons comment investir" (vague, no specific benefit)
❌ BAD: "C'est important pour vous" (weak, everyone says this)
✅ GOOD: "À la fin, vous saurez éviter l'erreur qui coûte 20 000€ par an aux débutants"
✅ GOOD: "Je révèle la stratégie utilisée par seulement 3% des investisseurs - et qui bat le marché"

RHETORICAL QUESTION EXAMPLES (Make them think, not yes/no):
❌ BAD: "Est-ce que vous investissez?" (yes/no, not thought-provoking)
❌ BAD: "Voulez-vous devenir riche?" (obvious, everyone says yes)
✅ GOOD: "Pourquoi les banques nous cachent-elles cette information?"
✅ GOOD: "Qu'est-ce qui différencie un investisseur qui gagne de celui qui perd?"

KEY POINT FORMAT (Concise concept names):
✅ GOOD: "La règle des 4% pour la retraite" (7 words, specific)
✅ GOOD: "L'erreur des débutants avec les ETF" (6 words, concrete)
✅ GOOD: "Diversification géographique" (2 words, clear)
❌ BAD: "Comprendre les concepts fondamentaux de l'investissement à long terme pour réussir" (14 words, too long)
❌ BAD: "Important stuff about money" (vague, not specific)
"""
        else:  # English and other languages
            examples_block = """
HOOK EXAMPLES (First 10 seconds - must grab attention):
❌ BAD: "Today we're talking about inflation" (boring, generic)
❌ BAD: "Hello, I'm going to explain investing" (slow start)
✅ GOOD: "In 2023, inflation stole $1,400 from every American. Here's how to get it back."
✅ GOOD: "Warren Buffett made 47% during the 2008 crisis with one simple technique. I'll show you."

CURIOSITY LOOP EXAMPLES (Promise that keeps them watching):
❌ BAD: "We'll see how to invest" (vague, no specific benefit)
❌ BAD: "This is important for you" (weak, everyone says this)
✅ GOOD: "By the end, you'll know how to avoid the $20,000/year mistake most beginners make"
✅ GOOD: "I'm revealing the strategy used by only 3% of investors - that beats the market"

RHETORICAL QUESTION EXAMPLES (Make them think, not yes/no):
❌ BAD: "Do you invest?" (yes/no, not thought-provoking)
❌ BAD: "Do you want to be rich?" (obvious, everyone says yes)
✅ GOOD: "Why do banks hide this information from us?"
✅ GOOD: "What separates investors who win from those who lose?"

KEY POINT FORMAT (Concise concept names):
✅ GOOD: "The 4% rule for retirement" (5 words, specific)
✅ GOOD: "Common beginner ETF mistake" (4 words, concrete)
✅ GOOD: "Geographic diversification" (2 words, clear)
❌ BAD: "Understanding fundamental concepts of long-term investment strategies for success" (10 words, too long)
❌ BAD: "Important stuff about money" (vague, not specific)
"""

        output_format_label = (
            "OUTPUT FORMAT (STRICT JSON)"
            if language.lower() == "english"
            else "FORMAT DE SORTIE (JSON STRICT)"
        )

        prompt = [
            {
                "role": "system",
                "content": f"""You are an expert YouTube retention strategist. Create a video OUTLINE optimized for viewer retention and watch time.

TARGET LANGUAGE: {language.upper()} - ALL text fields must be in {language.upper()}

VIDEO SPECIFICATIONS:
- Target length: {final_target_words} words (approximately {final_target_words // 150} minutes)
- Number of sections: {num_sections}
- Key points per section: 2-{max_keypoints_per_section}
- Total key points needed: approximately {num_key_points}

AUDIENCE: {target_audience}
TONE STYLE: {tone_style}

{examples_block}

RETENTION STRATEGY (Critical for success):
1. HOOK (first 10 seconds): Must grab attention immediately - use shocking fact, bold promise, or intriguing question
2. CURIOSITY LOOPS: Every section should promise something valuable coming later - keep them watching
3. RHETORICAL QUESTIONS: Make audience pause and reflect (1-2 per section) - engage their thinking
4. MICRO-LOOPS: Use transitions like "But here's where it gets interesting..." or "Wait until you see this..."

CONTENT TRANSFORMATION RULES:
- Use the input text as INSPIRATION, not as content to copy word-for-word
- Extract facts, data, and key concepts BUT rewrite all explanations in your own words
- If input says "I did X" or "In my experience" → transform to "Research shows X" or "Studies reveal X"
- Remove ALL author self-promotion (courses, books, coaching, success stories)
- Remove channel promotion, sponsor mentions, calls-to-action from original
- Focus on TEACHING valuable concepts that benefit the viewer
- Maintain factual accuracy but change the presentation style

FIELD-BY-FIELD GUIDELINES:
- "title_variants": 3 clickable video titles, each 8-12 words, include numbers/benefits/intrigue
- "hook.text": 20-30 words maximum, must grab attention in first 3 seconds
- "hook.curiosity_loop": Specific promise of value coming later (not vague "you'll learn a lot")
- "section.title": 4-7 words, descriptive and clear
- "section.core_idea": 1-2 sentences maximum explaining the main concept of this section
- "key_points.text": 5-10 words MAXIMUM - just the concept name, not full sentences
- "micro_curiosity_loop": Teaser for the next section - keep them from clicking away
- "rhetorical_question": Thought-provoking question (not yes/no), makes them reflect
- "visual_suggestion": Specific B-roll ideas (not vague "stock footage" - be concrete)

JSON TECHNICAL REQUIREMENTS:
- ALL fields are required (use empty string "" if truly not applicable)
- Valid JSON syntax - check quotes, commas, brackets carefully
- Numbers without quotes (integers and floats)
- No comments allowed in JSON
- No trailing commas

QUALITY CHECKLIST - Verify before responding:
□ Is the hook attention-grabbing within the first 3 seconds?
□ Does each section have a compelling curiosity loop that creates suspense?
□ Are ALL key_points concise (5-10 words maximum)?
□ Is EVERY field filled with content in {language.upper()} language?
□ Is the JSON syntactically valid and parseable?
□ Did I transform the content (not copy verbatim from source)?
□ Did I remove author self-promotion and channel promotion?
□ Are rhetorical questions thought-provoking (not simple yes/no)?
□ Are visual suggestions specific and concrete?

RESPOND WITH VALID JSON ONLY. NO PREAMBLE. NO EXPLANATION. NO META-COMMENTARY.""",
            },
            {
                "role": "user",
                "content": f"""SOURCE MATERIAL (use as inspiration, transform into your own words):
{original_text}

{output_format_label}:
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
        # Detailed language-specific voice-over style guides
        if language.lower() == "french":
            style_guide = """
FRENCH VOICE-OVER STYLE GUIDE:

1. SENTENCE STRUCTURE:
   - SVO (Subject-Verb-Object), active voice, present tense
   - 12-18 words per sentence MAXIMUM
   - Maximum 1-2 commas per sentence (keep it simple)
   - Start with something concrete, end with consequence/action
   
2. RHYTHM & CONVERSATIONAL FLOW:
   - Vary sentence length: Short → Medium → Short (creates rhythm)
   - Use French verbal tics naturally (2-3 per paragraph):
     "en fait", "donc", "d'ailleurs", "par exemple", "c'est-à-dire", 
     "clairement", "typiquement", "autrement dit"
   - Transitions that sound natural spoken aloud:
     "Et là" / "Mais attention" / "Le truc, c'est que" / "Sauf que" / 
     "D'abord" / "Ensuite" / "Et surtout"

3. TONE - Formal "VOUS" but Conversational:
   - Think: Conference speaker, NOT textbook or friend
   - ❌ "Il convient de noter que" → ✅ "Attention, vous devez savoir que"
   - ❌ "Premièrement, deuxièmement" → ✅ "D'abord... Ensuite... Et surtout"
   - ❌ "Par conséquent" → ✅ "Donc" / "Du coup"
   
4. TECHNICAL TERMS (Your audience knows finance):
   - Use them when needed, BUT always explain simply right after
   - ✅ "Les ETF, c'est-à-dire des paniers d'actions automatiques"
   - ✅ "Le rendement, autrement dit l'argent que vous gagnez chaque année"
   - ✅ "La plus-value, donc le profit quand vous vendez"

5. EXAMPLES - Before/After Comparison:

❌ BAD EXAMPLE (too formal, written style, stiff):
"L'inflation constitue un phénomène économique complexe qui nécessite une compréhension approfondie. Premièrement, elle érode progressivement le pouvoir d'achat des ménages. Deuxièmement, elle affecte négativement la valeur des investissements à long terme."

✅ GOOD EXAMPLE (conversational voice-over, flows naturally):
"L'inflation, c'est simple : votre argent perd de la valeur chaque année. Par exemple, vos 1000€ d'aujourd'hui valent seulement 960€ l'année prochaine. Et là, vous perdez du pouvoir d'achat. Le truc, c'est que ça touche aussi vos investissements. Donc vous devez protéger votre capital."

6. PARAGRAPH STRUCTURE (Follow this template):
   - Opening: State the concept concretely (1-2 sentences)
   - Example or data point to illustrate (1 sentence)
   - Consequence or "So what?" (1-2 sentences)
   - Optional: Action or implication (1 sentence)
"""
        else:  # English and other languages
            style_guide = """
ENGLISH VOICE-OVER STYLE GUIDE:

1. SENTENCE STRUCTURE:
   - SVO (Subject-Verb-Object), active voice, present tense
   - 12-18 words per sentence MAXIMUM
   - Maximum 1-2 commas per sentence (keep it simple)
   - Start with something concrete, end with consequence/action

2. RHYTHM & CONVERSATIONAL FLOW:
   - Vary sentence length: Short → Medium → Short (creates rhythm)
   - Use English conversational markers naturally (2-3 per paragraph):
     "actually", "basically", "in fact", "for example", "meaning", 
     "clearly", "typically", "in other words"
   - Transitions that sound natural spoken aloud:
     "Here's the thing" / "But wait" / "Now here's why" / "Except" / 
     "First" / "Then" / "Most importantly"

3. TONE - Direct but Conversational:
   - Think: TED talk speaker, NOT textbook or casual friend
   - ❌ "It should be noted that" → ✅ "Here's what you need to know"
   - ❌ "Firstly, secondly" → ✅ "First... Then... Most importantly"
   - ❌ "Therefore, consequently" → ✅ "So" / "That means"

4. TECHNICAL TERMS (Your audience knows finance):
   - Use them when needed, BUT always explain simply right after
   - ✅ "ETFs, basically baskets of stocks that trade like single stocks"
   - ✅ "Yield, meaning the money you earn on your investment each year"
   - ✅ "Capital gains, the profit when you sell for more than you paid"

5. EXAMPLES - Before/After Comparison:

❌ BAD EXAMPLE (too formal, written style, stiff):
"Inflation represents a complex economic phenomenon requiring comprehensive understanding. Firstly, it progressively erodes household purchasing power. Secondly, it negatively affects the value of long-term investments."

✅ GOOD EXAMPLE (conversational voice-over, flows naturally):
"Inflation is simple: your money loses value every year. For example, your $1000 today is worth only $960 next year. And that means you lose buying power. Here's the thing: it also hits your investments. So you need to protect your capital."

6. PARAGRAPH STRUCTURE (Follow this template):
   - Opening: State the concept concretely (1-2 sentences)
   - Example or data point to illustrate (1 sentence)
   - Consequence or "So what?" (1-2 sentences)
   - Optional: Action or implication (1 sentence)
"""

        prompt = [
            {
                "role": "system",
                "content": f"""You are an expert YouTube voice-over scriptwriter. Write a script designed to be SPOKEN aloud, not read silently.

TARGET LANGUAGE: {language.upper()}
TARGET LENGTH: {target_words} words (±10 words acceptable, quality over exact count)

CONTEXT: You are expanding ONE key point from a larger video outline into a complete voice-over paragraph.
The key point "{key_point_text}" is intentionally brief. Your job is to develop it fully while staying focused on this specific topic.

{style_guide}

CRITICAL RULES FOR VOICE-OVER:
✓ Write for EARS, not EYES - how would you say this out loud naturally?
✓ One main idea + maximum two concrete examples
✓ NO bullet points, NO lists, NO colons in the paragraph (pure flowing text)
✓ NO abstract philosophizing - stay concrete and practical
✓ Use third-person neutral perspective (international advisor voice):
  ❌ "We must invest" / "Our country" / "I recommend"
  ✅ "Investors should" / "Countries typically" / "Data shows"

QUALITY CHECKLIST - Verify before responding:
□ Would this sound natural if read aloud? (test it!)
□ Did I vary sentence length for rhythm?
□ Did I include 2-3 conversational markers/verbal tics?
□ Did I explain any technical terms in simple language?
□ Is it approximately {target_words} words (±10)?
□ Is ALL content in {language.upper()}?
□ Does it follow the paragraph structure template?
□ Did I avoid lists, bullet points, and colons?

OUTPUT FORMAT (JSON):
{{"title": "Short descriptive title (5 words maximum)", "paragraph": "Your complete voice-over script here as one flowing paragraph"}}

RESPOND WITH VALID JSON ONLY.""",
            },
            {
                "role": "user",
                "content": f"""KEY POINT TO DEVELOP:
{key_point_text}

Write a {target_words}-word voice-over paragraph expanding on this key point. Make it sound natural, conversational, and engaging when spoken aloud. Follow all style guidelines above.""",
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
        target_audience = self.config.get("script", {}).get(
            "target_audience",
            "investisseurs particuliers, curieux en économie, 30–60 ans",
        )

        # Language-specific tone examples
        if language.lower() == "french":
            tone_examples = """
TONE EXAMPLES (French):
❌ BAD (too formal/academic):
- "L'inflation représente un défi macroéconomique significatif"
- "Il convient de noter que les investisseurs avertis"
- "Premièrement, il est essentiel de comprendre"

✅ GOOD (conversational but professional):
- "L'inflation, c'est un gros problème pour l'économie"
- "Attention : les investisseurs doivent savoir que"
- "D'abord, vous devez comprendre"

STYLE: Direct, conversational, concrete. Like a smart conference speaker explaining to interested professionals."""
        else:
            tone_examples = """
TONE EXAMPLES (English):
❌ BAD (too formal/academic):
- "Inflation represents a significant macroeconomic challenge"
- "It should be noted that informed investors"
- "Firstly, it is essential to understand"

✅ GOOD (conversational but professional):
- "Inflation is a major problem for the economy"
- "Here's what investors need to know"
- "First, you need to understand"

STYLE: Direct, conversational, concrete. Like a smart conference speaker explaining to interested professionals."""

        prompt = [
            {
                "role": "system",
                "content": f"""You are an expert content analyst transforming complex text into clear, scannable ideas.

TARGET OUTPUT LANGUAGE: {language.upper()} (ALL content must be in {language.upper()})

AUDIENCE: {target_audience}

{tone_examples}

YOUR TASK:
1. Read the input text carefully
2. Extract ONLY the core ideas (ignore fluff, author self-promotion, CTAs)
3. Organize into logical hierarchy using markdown
4. Rewrite in YOUR OWN WORDS using our brand voice (conversational, direct, concrete)
5. Make it scannable - a busy person should understand the main points in 30 seconds

MARKDOWN STRUCTURE:
- # = Main topic (1 only)
- ## = Major themes (3-5 recommended)
- ### = Sub-topics under each theme
- Bullet points (-) = Individual facts/ideas/examples
- Keep bullets SHORT (10-15 words maximum)
- Use numbers when showing sequences or steps

CONTENT TRANSFORMATION RULES:
- Don't copy the author's exact phrasing - paraphrase in your own words
- Remove "In this video..." or "I will show you..." type phrases
- Remove promotional language, course pitches, channel promotion, sponsor mentions
- Remove personal anecdotes unless they contain valuable lessons
- If input says "I did X" → transform to "Research shows X" or "Data reveals X"
- Use technical terms when needed BUT explain them simply
- Stay concrete - avoid abstract philosophizing

QUALITY CHECKLIST (verify before responding):
□ Can someone scan this in 30 seconds and grasp the main ideas?
□ Is every bullet point valuable and concise?
□ Did I use simple, everyday words where possible?
□ Is ALL content in {language.upper()} language?
□ Did I remove author self-promotion?
□ Is the hierarchy logical and easy to follow?

OUTPUT FORMAT: Markdown document ONLY. No preamble, no explanation, no meta-commentary.""",
            },
            {
                "role": "user",
                "content": f"""INPUT TEXT TO STRUCTURE:
{original_text}

Transform this into structured markdown ideas following all instructions above. Remember: output in {language.upper()} language, use conversational tone, make it scannable, remove fluff.""",
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
        Call AI API for JSON responses using dependency injection.

        Args:
            messages (list): List of message dictionaries
            max_retries (int): Maximum number of retry attempts

        Returns:
            dict: Parsed JSON response from AI model
        """
        return self.ai_client.generate_json_response(messages, max_retries)

    def call_claude_text_only(self, messages, max_retries=3):
        """
        Call AI API for text responses using dependency injection.

        Args:
            messages (list): List of message dictionaries
            max_retries (int): Maximum number of retry attempts

        Returns:
            str: Text response from AI model
        """
        return self.ai_client.generate_text_response(messages, max_retries)

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
