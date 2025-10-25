#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module d'extraction et d'analyse des métadonnées pour les vidéos b-roll.
Extrait la première frame de chaque vidéo et utilise l'API OpenAI pour l'analyser.
"""

import os
import logging
import traceback

# Image extraction disabled
import requests


class MetaExtractor:
    """
    Classe responsable de l'extraction et de l'analyse des métadonnées des vidéos b-roll.
    """

    def __init__(self, config):
        """
        Initialise l'extracteur de métadonnées avec la configuration.

        Args:
            config (dict): Configuration chargée depuis config.yml
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
        Extrait la première frame d'une vidéo et la sauvegarde en JPG.

        Args:
            video_path (str): Chemin vers le fichier vidéo

        Returns:
            str: Chemin vers l'image JPG extraite, ou None en cas d'erreur
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
        Analyse une image avec l'API OpenAI GPT-4o.

        Args:
            image_path (str): Chemin vers l'image à analyser

        Returns:
            dict: Dictionnaire contenant l'analyse, ou un message d'erreur
        """
        try:
            # Vérifier que l'image existe
            if not os.path.exists(image_path):
                return {
                    "error": f"L'image {os.path.basename(image_path)} n'existe pas",
                    "description": "",
                    "context": "",
                }

            # Vérifier la clé API
            if not self.api_key:
                return {
                    "error": "Clé API OpenAI manquante",
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
                        "content": """Tu es un expert en analyse d'images et de vidéos. Tu vas recevoir une image qui est une frame d'une vidéo b-roll. Fournis une description détaillée, factuelle et objective de tout ce qui est visible dans cette image, sans interprétation ni supposition sur ce qui pourrait se passer ensuite.

Ta description doit inclure, dans un seul paragraphe :
- L'action en cours ou la posture des personnes.
- Une description générale des personnes (âge approximatif, sexe, posture, vêtements, accessoires, rôle probable, émotion observable si clairement visible, ethnie apparente si visible ; sinon "ethnie non identifiable").
- L'environnement et le décor (lieu, mobilier, objets notables, ambiance visuelle).
- L'époque (moderne ou ancienne, ou décennie approximative si identifiable, sinon "époque non identifiable").
- Les couleurs dominantes ou si la vidéo est en noir et blanc.

Utilise un langage simple, direct et précis. La description doit être rédigée en un seul paragraphe narratif, sans liste ni titre. Même si certaines informations sont difficiles à identifier, donne une estimation ou indique explicitement qu'elles ne sont pas visibles.

**À la fin de la description, ajoute une ou deux phrases indiquant :**
- Les thèmes, concepts ou émotions que cette scène pourrait illustrer (par exemple : maladie, solitude, joie, drame, ambiance familiale, crise, etc.).
- Les contextes narratifs possibles (par exemple : "cette scène pourrait être utilisée pour illustrer un diagnostic médical, l'annonce d'une maladie grave, une situation de stress ou d'attente en milieu hospitalier…").

**Enfin, termine par une ligne :**
Mots-clés : mot1, mot2, mot3, ..., mot20

où chaque mot-clé résume un thème, une émotion, une situation ou un concept illustré par la scène.

**Exemple de format attendu** :

Une femme adulte d'apparence caucasienne, habillée d'une blouse blanche et d'un chapeau d'infirmière, se tient debout dans un cabinet médical à l'aspect vintage (années 1950). Elle tient un téléphone à cadran noir près de son oreille et porte des lunettes. Sur la table à côté d'elle, il y a un microscope, des flacons, une lampe de bureau articulée et des documents. Le mur derrière elle est en briques, les rideaux sont blancs et la lumière est douce. La scène est en noir et blanc. L'ambiance semble sérieuse.  
Cette scène pourrait illustrer des thèmes comme la médecine d'époque, l'urgence médicale, l'attente d'un diagnostic, ou la solitude du personnel soignant dans les années 1950. Elle pourrait être utilisée dans un documentaire historique sur la santé, une fiction dramatique, ou toute situation liée à la maladie et à l'espoir.  
Mots-clés : médecine, hôpital, infirmière, années 1950, diagnostic, travail, solitude, tension, vintage, maladie""",
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Voici l'image extraite d'une vidéo b-roll. Décris cette scène en détail, en un seul paragraphe narratif, selon les instructions précédentes. Concentre-toi uniquement sur ce qui est visible.""",
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
                "max_tokens": 1000,
            }

            # Appel à l'API OpenAI
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                logging.error(
                    f"Erreur API OpenAI: {response.status_code} - {response.text}"
                )
                return {
                    "error": f"Erreur API: {response.status_code}",
                    "description": "",
                    "context": "",
                }

            # Traitement de la réponse
            response_content = response.json()
            if "choices" in response_content:
                # Extraire directement le texte de la réponse
                analysis_text = response_content["choices"][0]["message"][
                    "content"
                ].strip()

                # Écrire le résultat dans un fichier .txt
                txt_path = os.path.splitext(image_path)[0] + ".txt"
                try:
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(analysis_text)
                    logging.info(f"Metadata saved in {txt_path}")
                except Exception as e:
                    logging.error(f"Error writing metadata: {e}")
                    return {"error": str(e)}

                return {"context": analysis_text, "error": None}

        except Exception as e:
            logging.error(
                f"Erreur lors de l'analyse de l'image {os.path.basename(image_path)}: {e}"
            )
            traceback.print_exc()
            return {"error": str(e), "description": "", "context": ""}

    def _encode_image(self, image_data):
        """
        Encode une image en base64 pour l'API OpenAI.

        Args:
            image_data (bytes): Données de l'image en bytes

        Returns:
            str: Image encodée en base64
        """
        import base64

        return base64.b64encode(image_data).decode("utf-8")

    def process_video(self, video_path):
        """
        Traite une vidéo : extraction de la première frame et analyse.

        Args:
            video_path (str): Chemin vers le fichier vidéo

        Returns:
            bool: True si le traitement a réussi, False sinon
        """
        try:
            # Créer les chemins pour les fichiers de sortie
            video_name = os.path.basename(video_path)
            txt_name = os.path.splitext(video_name)[0] + ".txt"
            txt_path = os.path.join(os.path.dirname(video_path), txt_name)

            # Vérifier si l'analyse a déjà été effectuée (présence du fichier .txt)
            if os.path.exists(txt_path):
                logging.info(f"Analysis already done for {video_name}, skipping")
                return True

            # Extraire la première frame
            jpg_path = self.extract_first_frame(video_path)
            if not jpg_path:
                # Enregistrer l'erreur dans le fichier .txt - format simple
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(
                        f"Erreur: Impossible d'extraire la première frame de {video_name}"
                    )
                return False

            # Analyser l'image
            analysis = self.analyze_image(jpg_path)

            # Enregistrer uniquement le contexte dans un fichier .txt
            with open(txt_path, "w", encoding="utf-8") as f:
                if analysis and "context" in analysis:
                    f.write(analysis["context"])
                else:
                    f.write("Aucun contexte disponible pour cette vidéo")

            logging.info(f"Context saved for {video_name} (simplified format)")
            return True

        except Exception as e:
            logging.error(
                f"Erreur lors du traitement de {os.path.basename(video_path)}: {e}"
            )
            traceback.print_exc()
            return False

    def process_all_videos(self):
        """
        Traite toutes les vidéos du dossier b-roll.

        Returns:
            tuple: (nombre de vidéos traitées, nombre de succès)
        """
        # Vérifier que le dossier existe
        if not os.path.exists(self.b_roll_path):
            logging.error(f"Le dossier {self.b_roll_path} n'existe pas")
            return 0, 0

        # Récupérer la liste des vidéos MP4 et MOV
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

        # Compter les succès
        success_count = 0

        # Traiter chaque vidéo
        for i, video_path in enumerate(videos):
            logging.info(
                f"[{i + 1}/{total}] Traitement de {os.path.basename(video_path)}..."
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
