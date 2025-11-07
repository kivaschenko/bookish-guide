#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Metadata extraction and analysis module for b-roll videos.
Extracts the first frame from each video and uses OpenAI API to analyze it.
"""

# LibreSSL compatibility fix - suppress urllib3 warnings when LibreSSL is used instead of OpenSSL
import warnings
from urllib3.exceptions import NotOpenSSLWarning
import os
import logging
import traceback
import requests

warnings.filterwarnings("ignore", category=NotOpenSSLWarning)


class MetaExtractor:
    """
    Class responsible for extracting and analyzing metadata from b-roll videos.
    """

    def __init__(self, config):
        """
        Initialize the metadata extractor with configuration.

        Args:
            config (dict): Configuration loaded from config.yml
        """
        self.config = config
        self.b_roll_path = config.get("paths", {}).get("b_roll", "b-roll")

        # Get OpenAI API key from configuration (correct structure)
        self.api_key = None

        # Debug: display configuration structure for verification
        logging.info(f"Structure de la configuration: {config.keys()}")
        if "api" in config and "openai" in config["api"]:
            logging.info(f"Structure de api.openai: {config['api']['openai'].keys()}")

        try:
            if (
                "api" in config
                and "openai" in config["api"]
                and "api_key" in config["api"]["openai"]
            ):
                self.api_key = config["api"]["openai"]["api_key"]
                logging.info("OpenAI API key found in configuration")
                # Debug: display first part of key for verification
                if self.api_key:
                    logging.info(f"API key start: {self.api_key[:10]}...")
        except Exception as e:
            logging.error(f"Error retrieving API key: {e}")

        # Si pas dans la config, essayer les variables d'environnement
        if not self.api_key:
            self.api_key = os.environ.get("OPENAI_API_KEY")
            if self.api_key:
                logging.info("OpenAI API key found in environment variables")
            else:
                logging.warning(
                    "OpenAI API key not found in configuration or environment variables. "
                    "Use OPENAI_API_KEY=your_key before running the script or add it to config.yml."
                )

    def extract_first_frame(self, video_path):
        """
        Extract the first frame from a video and save it as JPG.

        Args:
            video_path (str): Path to the video file

        Returns:
            str: Path to the extracted JPG image, or None if error occurs
        """
        try:
            logging.info(f"Extracting first frame from {video_path}...")
            # Create path for JPG image
            video_name = os.path.basename(video_path)
            logging.debug(f"Video name: {video_name}")
            jpg_name = os.path.splitext(video_name)[0] + ".jpg"
            logging.debug(f"JPG name: {jpg_name}")
            jpg_path = os.path.join(os.path.dirname(video_path), jpg_name)
            logging.debug(f"JPG path: {jpg_path}")

            # If image already exists, return it directly
            if os.path.exists(jpg_path):
                logging.info(
                    f"Image already extracted for {video_name}, using existing one"
                )
                return jpg_path
            else:
                logging.info(f"Extracting first frame from {video_path}...")
                # Extract first frame using FFmpeg
                return self.extract_first_frame_by_ffmpeg(
                    video_path=video_path, image_path=jpg_path
                )
        except Exception as e:
            logging.error(f"Error extracting first frame from {video_path}: {e}")
            traceback.print_exc()
            return None

    def analyze_image(self, image_path):
        """
        Analyze an image using OpenAI GPT-4o API.

        Args:
            image_path (str): Path to the image to analyze

        Returns:
            dict: Dictionary containing the analysis, or an error message
        """
        try:
            # Check if the image exists
            if not os.path.exists(image_path):
                return {
                    "error": f"Image {os.path.basename(image_path)} does not exist",
                    "description": "",
                    "context": "",
                }

            # Check API key
            if not self.api_key:
                return {
                    "error": "OpenAI API key missing",
                    "description": "",
                    "context": "",
                }

            # Préparation de l'image pour l'API
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()

            logging.info(
                f"Sending image {os.path.basename(image_path)} to OpenAI API for analysis..."
            )

            # Préparation de la requête API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            # Get model from config or use default
            model = self.config.get("api", {}).get("openai", {}).get("model", "gpt-4o")

            # Construction de la requête pour GPT-4o avec Vision
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": """You are an expert in image and video analysis. You will receive an image that is a frame from a b-roll video. Provide a detailed, factual and objective description of everything visible in this image, without interpretation or assumptions about what might happen next.

Your description should include, in a single paragraph:
- The ongoing action or posture of people.
- A general description of people (approximate age, gender, posture, clothing, accessories, probable role, observable emotion if clearly visible, apparent ethnicity if visible; otherwise "ethnicity not identifiable").
- The environment and setting (place, furniture, notable objects, visual atmosphere).
- The era (modern or ancient, or approximate decade if identifiable, otherwise "era not identifiable").
- Dominant colors or if the video is in black and white.

Use simple, direct and precise language. The description must be written in a single narrative paragraph, without lists or titles. Even if some information is difficult to identify, give an estimate or explicitly indicate that they are not visible.

**At the end of the description, add one or two sentences indicating:**
- The themes, concepts or emotions that this scene could illustrate (for example: illness, loneliness, joy, drama, family atmosphere, crisis, etc.).
- Possible narrative contexts (for example: "this scene could be used to illustrate a medical diagnosis, the announcement of a serious illness, a situation of stress or waiting in a hospital environment...").

**Finally, end with a line:**
Keywords: word1, word2, word3, ..., word20

where each keyword summarizes a theme, emotion, situation or concept illustrated by the scene.

**Expected format example:**

An adult woman of Caucasian appearance, dressed in a white blouse and a nurse's cap, stands in a vintage-looking medical office (1950s). She holds a black rotary phone near her ear and wears glasses. On the table next to her, there is a microscope, vials, an articulated desk lamp and documents. The wall behind her is brick, the curtains are white and the light is soft. The scene is in black and white. The atmosphere seems serious.
This scene could illustrate themes such as period medicine, medical emergency, waiting for a diagnosis, or the loneliness of healthcare workers in the 1950s. It could be used in a historical documentary about health, a dramatic fiction, or any situation related to illness and hope.
Keywords: medicine, hospital, nurse, 1950s, diagnosis, work, loneliness, tension, vintage, illness""",
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Here is the image extracted from a b-roll video. Describe this scene in detail, in a single narrative paragraph, according to the previous instructions. Focus only on what is visible.""",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{self._encode_image(image_data)}"
                                },
                            },
                        ],
                    },
                ],
                "max_completion_tokens": 1000,
            }

            # Appel à l'API OpenAI
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                logging.error(
                    f"OpenAI API error: {response.status_code} - {response.text}"
                )
                return {
                    "error": f"API Error: {response.status_code}",
                    "description": "",
                    "context": "",
                }

            # Process the response
            response_content = response.json()
            if "choices" in response_content:
                # Extraire directement le texte de la réponse
                analysis_text = response_content["choices"][0]["message"][
                    "content"
                ].strip()

                logging.info(f"Received analysis text: {len(analysis_text)} characters")
                return {"context": analysis_text, "error": None}

        except Exception as e:
            logging.error(
                f"Erreur lors de l'analyse de l'image {os.path.basename(image_path)}: {e}"
            )
            traceback.print_exc()
            return {"error": str(e), "description": "", "context": ""}

    def _encode_image(self, image_data):
        """
        Encode an image in base64 for OpenAI API.

        Args:
            image_data (bytes): Image data in bytes

        Returns:
            str: Base64 encoded image
        """
        import base64

        return base64.b64encode(image_data).decode("utf-8")

    def process_video(self, video_path):
        """
        Process a video: extract first frame and analyze it.

        Args:
            video_path (str): Path to the video file

        Returns:
            bool: True if processing succeeded, False otherwise
        """
        try:
            # Create paths for output files
            video_name = os.path.basename(video_path)
            txt_name = os.path.splitext(video_name)[0] + ".txt"
            txt_path = os.path.join(os.path.dirname(video_path), txt_name)

            # Check if analysis has already been done (presence of .txt file with content)
            if os.path.exists(txt_path):
                # Check if file has content
                try:
                    with open(txt_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    if (
                        content
                        and not content.startswith("Error:")
                        and not content == "No context available for this video"
                    ):
                        logging.info(
                            f"Analysis already done for {video_name}, skipping"
                        )
                        return True
                    else:
                        logging.info(
                            f"Found empty or error file for {video_name}, re-processing"
                        )
                except Exception as e:
                    logging.warning(
                        f"Could not read existing file for {video_name}: {e}"
                    )
                # Continue processing if file is empty or contains error

            # Extract first frame
            jpg_path = self.extract_first_frame(video_path)
            if not jpg_path:
                # Save error in .txt file - simple format
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(f"Error: Unable to extract first frame from {video_name}")
                return False

            # Analyze the image
            analysis = self.analyze_image(jpg_path)

            # Enregistrer le résultat dans un fichier .txt
            with open(txt_path, "w", encoding="utf-8") as f:
                if analysis and "context" in analysis and analysis["context"]:
                    f.write(analysis["context"])
                    logging.info(
                        f"Context saved for {video_name}: {len(analysis['context'])} characters"
                    )
                elif analysis and "error" in analysis and analysis["error"]:
                    error_msg = f"Error during analysis: {analysis['error']}"
                    f.write(error_msg)
                    logging.error(f"Error analyzing {video_name}: {analysis['error']}")
                    return False
                else:
                    f.write("No context available for this video")
                    logging.warning(f"No context available for {video_name}")
                    return False

            return True

        except Exception as e:
            logging.error(
                f"Erreur lors du traitement de {os.path.basename(video_path)}: {e}"
            )
            traceback.print_exc()
            return False

    def process_all_videos(self):
        """
        Process all videos in the b-roll folder.

        Returns:
            tuple: (number of videos processed, number of successes)
        """
        # Check that folder exists
        if not os.path.exists(self.b_roll_path):
            logging.error(f"Folder {self.b_roll_path} does not exist")
            return 0, 0

        # Get list of MP4 and MOV videos
        videos = [
            os.path.join(self.b_roll_path, f)
            for f in os.listdir(self.b_roll_path)
            if f.lower().endswith((".mp4", ".mov"))
        ]
        total = len(videos)

        if total == 0:
            logging.warning(f"No MP4 or MOV videos found in {self.b_roll_path}")
            return 0, 0

        logging.info(f"Processing {total} videos in {self.b_roll_path}")

        # Count successes
        success_count = 0

        # Process each video
        for i, video_path in enumerate(videos):
            logging.info(
                f"[{i + 1}/{total}] Processing {os.path.basename(video_path)}..."
            )
            if self.process_video(video_path):
                success_count += 1

        return total, success_count

    def extract_first_frame_by_ffmpeg(self, video_path, image_path=None):
        """
        Extracts the first frame from an MP4/MOV video using ffmpeg
        FFmpeg Command Breakdown:
        -i video.mp4 → Input file
        -vframes 1 → Extract only 1 frame
        -q:v 2 → Quality setting (1=best, 31=worst)
        -y → Overwrite output without asking
        output.jpg → Output file
        """
        if image_path is None:
            # Create path for JPG image
            video_name = os.path.basename(video_path)
            jpg_name = os.path.splitext(video_name)[0] + ".jpg"
            image_path = os.path.join(os.path.dirname(video_path), jpg_name)

        import subprocess

        # FFmpeg command to extract first frame
        cmd = [
            "ffmpeg",
            "-i",
            str(video_path),  # Input video
            "-vframes",
            "1",  # Extract only 1 frame
            "-q:v",
            "2",  # High quality (1-31, lower = better)
            "-y",  # Overwrite output file
            str(image_path),  # Output image
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            logging.debug(f"FFmpeg command output: {result.stdout}")
            if result.returncode == 0:
                logging.info(f"Extracted first frame: {image_path}")
                return image_path
            else:
                logging.error(f"FFmpeg failed: {result.stderr}")
                return None
        except FileNotFoundError:
            logging.error("FFmpeg not found on system")
            return None
