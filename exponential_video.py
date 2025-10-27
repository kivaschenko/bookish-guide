#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main script for automatic video generation.
Supports step-by-step execution via command line arguments.
"""

# LibreSSL compatibility fix - suppress urllib3 warnings when LibreSSL is used instead of OpenSSL
import warnings
from urllib3.exceptions import NotOpenSSLWarning

warnings.filterwarnings("ignore", category=NotOpenSSLWarning)

# Disable tokenizer parallelism to avoid deadlocks
import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import logging
import sys
import argparse
from pathlib import Path
import yaml
from script_and_voice.paraphraser import Paraphraser
from utils import setup_logging
import json
from b_roll import prepare_brolls_vector
from jouer_son import lancement_premontage, fin_montage
import subprocess
import re
import glob
import html
import requests
import base64

BASE_DIR = Path(__file__).resolve().parent
print(f"Base directory: {BASE_DIR}")


def load_config():
    """Charge la configuration depuis config.yml"""
    try:
        with open("config.yml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Erreur lors du chargement de la configuration: {e}")
        sys.exit(1)


def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    """Configure et sauvegarde un fichier WAV"""
    import wave

    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)


def _generate_bullet_metadata(audio_files, config, temp_dir):
    """
    Generates the audio_bullet_metadata.json file for editing compatibility.
    """
    import json
    import time

    # Lire les textes des bullets depuis les fichiers texte
    bullet_texts = []
    for i in range(1, len(audio_files) + 1):
        text_file = temp_dir / f"bullet{i}_text.txt"
        if text_file.exists():
            bullet_texts.append(text_file.read_text(encoding="utf-8").strip())
        else:
            bullet_texts.append(f"Bullet {i}")  # Fallback

    # Create metadata structure
    metadata = {
        "generation_timestamp": time.time(),
        "tts_config": {
            "model": "gemini-2.5-flash-preview-tts",
            "voice": config.get("api", {}).get("gemini", {}).get("voice", "Kore"),
            "granularity": "bullet",
            "generation_mode": "bullet",
        },
        "generation_mode": "bullet",
        "total_bullets": len(audio_files),
        "bullets": [],
    }

    cumulative_time = 0

    for bullet_index, (audio_file, bullet_text) in enumerate(
        zip(audio_files, bullet_texts), 1
    ):
        # Read actual MP3 file duration (approximation)
        try:
            # Use file size-based approximation
            file_size = audio_file.stat().st_size
            # Estimation: ~1KB per second for MP3 128kbps
            duration = file_size / 1000.0
        except Exception as e:
            logging.warning(f"Unable to read duration of {audio_file}: {e}")
            duration = 0.0

        bullet_info = {
            "bullet_index": bullet_index,
            "audio_file": f"bullet{bullet_index:02d}.mp3",
            "full_path": audio_file,
            "duration": duration,
            "start_time": cumulative_time,
            "end_time": cumulative_time + duration,
            "bullet_text": bullet_text,
            "word_count": len(bullet_text.split()),
            "character_count": len(bullet_text),
        }

        metadata["bullets"].append(bullet_info)
        cumulative_time += duration

    metadata["total_duration"] = cumulative_time

    # Save metadata
    metadata_file = temp_dir / "audio" / "audio_bullet_metadata.json"
    metadata_file.parent.mkdir(exist_ok=True)
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logging.info(f"📄 Bullet metadata saved: {metadata_file}")
    logging.info(
        f"⏱️ Total duration: {cumulative_time:.2f}s ({len(audio_files)} bullets)"
    )


def generate_gemini_tts_audio(config, granularity):
    """
    Generates TTS audio with Gemini API for all rushes/bullets.

    IMPORTANT: This function is designed to be 100% compatible with OpenAI TTS:
    - Generates .mp3 files (like OpenAI TTS)
    - Uses the same naming: bullet01.mp3, bullet02.mp3, etc.
    - Saves in the same temp/ folder
    - Returns the same data structure

    Args:
        config (dict): Project configuration
        granularity (str): Granularity mode ('bullet' or 'rush')

    Returns:
        list: List of generated audio files (MP3 format, OpenAI TTS naming)
    """
    # Check if we should use proxy
    use_proxy = config.get("api", {}).get("gemini", {}).get("use_proxy", False)

    if use_proxy:
        logging.info("🌐 Proxy mode enabled for Gemini TTS (geographic bypass)")
        return generate_gemini_tts_audio_via_proxy(config, granularity)
    else:
        logging.info("📡 Direct API mode for Gemini TTS")
        return generate_gemini_tts_audio_direct(config, granularity)


def generate_gemini_tts_audio_via_proxy(config, granularity):
    """
    Version using PHP proxy to bypass geographic restrictions.
    """
    import time

    # Configuration du proxy
    proxy_url = (
        config.get("api", {})
        .get("gemini", {})
        .get("proxy_url", "https://leader-referencement.com/gemini_tts.php")
    )
    api_key = config["api"]["gemini"]["api_key"]

    temp_dir = Path(config["paths"]["temp"])
    audio_dir = temp_dir / "audio"  # Same structure as OpenAI TTS
    audio_dir.mkdir(exist_ok=True)  # Create audio directory if it doesn't exist
    audio_files = []

    # Rate limiting: 21 seconds between each call (safety margin)
    MIN_INTERVAL_SECONDS = 31
    last_call_timestamp = None

    # Determine file prefix based on granularity
    if granularity == "bullet":
        prefix = "bullet"
        file_pattern = "bullet*_text.txt"
    else:
        prefix = "rush"
        file_pattern = "rush*_text.txt"

    # Trouver tous les fichiers texte
    text_files = list(temp_dir.glob(file_pattern))
    # Sort by NUMERICAL order (not alphabetical)
    text_files.sort(key=lambda x: int(x.stem.split("_")[0].replace(prefix, "")))

    if not text_files:
        raise FileNotFoundError(f"No {file_pattern} files found in {temp_dir}")

    logging.info(
        f"🌐 Gemini TTS audio generation via PROXY for {len(text_files)} {prefix} files"
    )
    logging.info(f"📡 Proxy used: {proxy_url}")
    logging.info(
        f"Rate limiting enabled: {MIN_INTERVAL_SECONDS} seconds between each API call"
    )

    for i, text_file in enumerate(text_files):
        try:
            # Lire le contenu du fichier
            with open(text_file, "r", encoding="utf-8") as f:
                text_content = f.read().strip()

            if not text_content:
                logging.warning(f"File {text_file} is empty, skipped")
                continue

            # Extract file number and convert to integer
            file_number_str = text_file.stem.split("_")[0].replace(prefix, "")
            try:
                file_number = int(file_number_str)
            except ValueError:
                logging.error(
                    f"Unable to convert '{file_number_str}' to number for {text_file}"
                )
                continue

            # Check if MP3 file already exists
            audio_filename = f"{prefix}{file_number:02d}.mp3"
            audio_path = audio_dir / audio_filename

            if audio_path.exists():
                logging.info(f"⏭️ Audio file {audio_filename} already present, skipped")
                audio_files.append(str(audio_path))
                continue

            # Rate limiting: wait if necessary
            if last_call_timestamp is not None:
                time_since_last_call = time.time() - last_call_timestamp
                if time_since_last_call < MIN_INTERVAL_SECONDS:
                    wait_time = MIN_INTERVAL_SECONDS - time_since_last_call
                    logging.info(
                        f"⏳ Rate limiting : attente de {wait_time:.1f} secondes avant l'appel suivant..."
                    )
                    time.sleep(wait_time)

            # Generate audio with Gemini TTS via proxy
            logging.info(
                f"🌐 Audio generation via proxy for {prefix} {file_number}... ({i + 1}/{len(text_files)})"
            )

            # Prepare request for proxy
            payload = {
                "api_key": api_key,
                "text": text_content,
                "voice": "Kore",  # Default voice
            }

            # Make request to proxy
            response = requests.post(
                proxy_url,
                json=payload,
            )

            # Check response status
            if response.status_code != 200:
                error_detail = response.text
                raise Exception(
                    f"Erreur proxy HTTP {response.status_code}: {error_detail}"
                )

            # Debug: check response size
            response_size = len(response.content)
            logging.info(f"📊 Proxy response size: {response_size} bytes")

            # Debug: check headers
            content_type = response.headers.get("Content-Type", "unknown")
            logging.info(f"📋 Content-Type: {content_type}")

            # Parse JSON response with detailed error handling
            try:
                result = response.json()
                logging.info(
                    f"✅ JSON parsed successfully, keys: {list(result.keys())}"
                )
            except ValueError as e:
                logging.error(f"❌ JSON parsing error: {e}")
                logging.error(f"📄 Response start: {response.text[:500]}...")
                raise Exception(f"Erreur parsing JSON de la réponse proxy: {e}")

            if "error" in result:
                raise Exception(f"Erreur API: {result['error']}")

            # Extraire les données audio (format camelCase de l'API)
            data = result["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]

            # Décoder les données PCM (comme l'original)
            pcm_data = base64.b64decode(data)

            # Sauvegarder temporairement en WAV (comme l'original)
            temp_wav = temp_dir / f"temp_{file_number}.wav"
            wave_file(str(temp_wav), pcm_data)

            # Convertir WAV vers MP3 (comme l'original)
            import subprocess

            convert_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(temp_wav),
                "-q:a",
                "0",
                str(audio_path),
            ]
            subprocess.run(convert_cmd, capture_output=True, check=True)

            # Nettoyer le fichier temporaire
            temp_wav.unlink(missing_ok=True)

            logging.info(f"✅ Audio {audio_filename} generated successfully via proxy")
            audio_files.append(str(audio_path))

            # Enregistrer le timestamp pour le rate limiting
            last_call_timestamp = time.time()

        except Exception as e:
            logging.error(f"❌ Erreur lors du traitement de {text_file}: {e}")
            continue

    logging.info(
        f"🎵 Audio generation via proxy completed: {len(audio_files)} MP3 files created"
    )

    # Générer le fichier de métadonnées si en mode bullet
    if granularity == "bullet":
        _generate_bullet_metadata(audio_files, config, temp_dir)

    return audio_files


def generate_gemini_tts_audio_direct(config, granularity):
    """Version originale utilisant l'API Gemini directe"""
    try:
        from google import genai
        from google.genai import types
        import time

        # Initialiser le client Gemini avec l'API key
        api_key = config["api"]["gemini"]["api_key"]  # Clé API Gemini
        client = genai.Client(api_key=api_key)

        temp_dir = Path(config["paths"]["temp"])
        audio_dir = temp_dir / "audio"  # Même structure qu'OpenAI TTS
        audio_dir.mkdir(exist_ok=True)  # Créer le dossier audio s'il n'existe pas
        audio_files = []

        # Rate limiting: 21 seconds between each call (safety margin)
        MIN_INTERVAL_SECONDS = 21
        last_call_timestamp = None

        # Determine file prefix based on granularity
        if granularity == "bullet":
            prefix = "bullet"
            file_pattern = "bullet*_text.txt"
        else:
            prefix = "rush"
            file_pattern = "rush*_text.txt"

        # Trouver tous les fichiers texte
        text_files = list(temp_dir.glob(file_pattern))
        # Sort by NUMERICAL order (not alphabetical)
        text_files.sort(key=lambda x: int(x.stem.split("_")[0].replace(prefix, "")))

        if not text_files:
            raise FileNotFoundError(f"No {file_pattern} files found in {temp_dir}")

        logging.info(
            f"Gemini TTS audio generation for {len(text_files)} {prefix} files"
        )
        logging.info(
            f"Rate limiting enabled: {MIN_INTERVAL_SECONDS} seconds between each API call"
        )

        for i, text_file in enumerate(text_files):
            try:
                # Lire le contenu du fichier
                with open(text_file, "r", encoding="utf-8") as f:
                    text_content = f.read().strip()

                if not text_content:
                    logging.warning(f"File {text_file} is empty, skipped")
                    continue

                # Extract file number and convert to integer
                file_number_str = text_file.stem.split("_")[0].replace(prefix, "")
                try:
                    file_number = int(file_number_str)
                except ValueError:
                    logging.error(
                        f"Unable to convert '{file_number_str}' to number for {text_file}"
                    )
                    continue

                # Check if MP3 file already exists
                audio_filename = f"{prefix}{file_number:02d}.mp3"
                audio_path = audio_dir / audio_filename

                if audio_path.exists():
                    logging.info(
                        f"⏭️ Audio file {audio_filename} already present, skipped"
                    )
                    audio_files.append(str(audio_path))
                    continue

                # Rate limiting: wait if necessary
                if last_call_timestamp is not None:
                    time_since_last_call = time.time() - last_call_timestamp
                    if time_since_last_call < MIN_INTERVAL_SECONDS:
                        wait_time = MIN_INTERVAL_SECONDS - time_since_last_call
                        logging.info(
                            f"⏳ Rate limiting : attente de {wait_time:.1f} secondes avant l'appel suivant..."
                        )
                        time.sleep(wait_time)

                # Générer l'audio avec Gemini TTS
                logging.info(
                    f"Audio generation for {prefix} {file_number}... ({i + 1}/{len(text_files)})"
                )

                # Retry avec attente en cas d'erreur 429
                max_retries = 3
                retry_delay = 4000  # ~67 minutes

                for retry_count in range(max_retries):
                    try:
                        # Enregistrer le timestamp avant l'appel
                        call_start_time = time.time()

                        response = client.models.generate_content(
                            model="gemini-2.5-flash-preview-tts",
                            contents=text_content,
                            config=types.GenerateContentConfig(
                                response_modalities=["AUDIO"],
                                speech_config=types.SpeechConfig(
                                    voice_config=types.VoiceConfig(
                                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                            voice_name="Kore",  # Voix par défaut
                                        )
                                    )
                                ),
                            ),
                        )

                        # Si on arrive ici, l'appel a réussi
                        break

                    except Exception as e:
                        error_str = str(e)
                        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                            if retry_count < max_retries - 1:
                                logging.warning(
                                    f"⚠️ Error 429 (quota exceeded) for {prefix} {file_number}, waiting {retry_delay}s before retry {retry_count + 1}/{max_retries}"
                                )
                                time.sleep(retry_delay)
                                continue
                            else:
                                logging.error(
                                    f"❌ Final failure after {max_retries} attempts for {prefix} {file_number}"
                                )
                                logging.error(
                                    f"❌ Gemini TTS quota exhausted permanently. Stopping script."
                                )
                                logging.error(
                                    f"💡 Tip: Wait until tomorrow or upgrade to a paid Google Cloud plan"
                                )
                                sys.exit(1)
                        else:
                            # Autre erreur, on arrête les retries
                            logging.error(
                                f"❌ Erreur non-429 pour {prefix} {file_number}: {e}"
                            )
                            raise

                # Extraire les données audio
                data = response.candidates[0].content.parts[0].inline_data.data

                # Calculer le temps de réponse IMMÉDIATEMENT après la réponse API
                response_time = time.time() - call_start_time
                logging.info(
                    f"📡 API response received in {response_time:.1f}s, {len(data)} audio bytes"
                )

                # Sauvegarder temporairement en WAV
                temp_wav = temp_dir / f"temp_{file_number}.wav"
                wave_file(str(temp_wav), data)

                # Vérifier que le WAV a été créé
                if temp_wav.exists():
                    wav_size = temp_wav.stat().st_size
                    logging.info(
                        f"🎵 Temporary WAV created: {temp_wav.name} ({wav_size} bytes)"
                    )
                else:
                    logging.error(f"❌ WAV creation failed: {temp_wav}")
                    continue

                # Convertir WAV vers MP3 avec ffmpeg (conversion rapide)
                audio_filename = (
                    f"{prefix}{file_number:02d}.mp3"  # Format: bullet01.mp3, rush01.mp3
                )
                audio_path = audio_dir / audio_filename

                try:
                    # Utiliser ffmpeg pour la conversion (plus rapide que pydub)
                    import subprocess

                    logging.info(
                        f"🔄 Conversion ffmpeg: {temp_wav.name} → {audio_filename}"
                    )
                    result = subprocess.run(
                        [
                            "ffmpeg",
                            "-y",  # -y pour écraser sans demander
                            "-i",
                            str(temp_wav),  # fichier d'entrée WAV
                            "-acodec",
                            "libmp3lame",  # codec MP3
                            "-ab",
                            "128k",  # bitrate 128k (bon compromis qualité/taille)
                            str(audio_path),  # fichier de sortie MP3
                        ],
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0:
                        # Vérifier que le MP3 a été créé
                        if audio_path.exists():
                            mp3_size = audio_path.stat().st_size
                            logging.info(
                                f"✅ MP3 created successfully: {audio_filename} ({mp3_size} bytes)"
                            )
                            # Delete temporary WAV file
                            temp_wav.unlink()
                            logging.info(f"🗑️ Temporary WAV deleted: {temp_wav.name}")
                        else:
                            logging.error(
                                f"❌ MP3 not found after conversion: {audio_path}"
                            )
                            audio_path = temp_wav
                            audio_filename = temp_wav.name
                    else:
                        logging.error(
                            f"❌ ffmpeg error (code {result.returncode}): {result.stderr}"
                        )
                        logging.warning(f"⚠️ Keeping WAV file: {temp_wav.name}")
                        audio_path = temp_wav
                        audio_filename = temp_wav.name

                except FileNotFoundError:
                    logging.error("❌ ffmpeg not found on system")
                    logging.warning(f"⚠️ Keeping WAV file: {temp_wav.name}")
                    audio_path = temp_wav
                    audio_filename = temp_wav.name

                # Vérification finale de l'existence du fichier audio
                if audio_path.exists():
                    final_size = audio_path.stat().st_size
                    logging.info(
                        f"🎯 Final audio file confirmed: {audio_path.name} ({final_size} bytes)"
                    )
                else:
                    logging.error(
                        f"💥 PROBLÈME CRITIQUE: Fichier audio final non trouvé: {audio_path}"
                    )
                    continue

                audio_files.append(audio_path)

                # Mettre à jour le timestamp APRÈS l'appel API (pas après l'attente)
                last_call_timestamp = time.time()

                # Rate limiting: wait if necessary AVANT le prochain appel API
                if last_call_timestamp is not None:
                    time_since_last_call = time.time() - last_call_timestamp
                    if time_since_last_call < MIN_INTERVAL_SECONDS:
                        wait_time = MIN_INTERVAL_SECONDS - time_since_last_call
                        logging.info(
                            f"⏳ Rate limiting : attente de {wait_time:.1f} secondes avant l'appel suivant..."
                        )
                        time.sleep(wait_time)

            except Exception as e:
                logging.error(
                    f"Erreur lors de la génération audio pour {text_file}: {e}"
                )
                continue

        # Vérification finale : compter les fichiers réellement créés
        actual_files = list(audio_dir.glob(f"{prefix}*.mp3"))
        actual_count = len(actual_files)
        expected_count = len(text_files)

        logging.info(f"📊 Résumé génération Gemini TTS:")
        logging.info(f"   - Fichiers texte traités: {expected_count}")
        logging.info(f"   - Fichiers audio créés: {actual_count}")

        if actual_count == expected_count:
            logging.info(
                f"✅ Génération terminée avec succès : {actual_count}/{expected_count} fichiers"
            )
        else:
            missing_count = expected_count - actual_count
            logging.warning(
                f"⚠️ Génération incomplète : {missing_count} fichier(s) manquant(s)"
            )

            # Identifier les fichiers manquants
            expected_numbers = {
                int(f.stem.split("_")[0].replace(prefix, "")) for f in text_files
            }
            actual_numbers = {int(f.stem.replace(prefix, "")) for f in actual_files}
            missing_numbers = expected_numbers - actual_numbers

            if missing_numbers:
                missing_list = sorted(missing_numbers)
                logging.error(f"💥 Fichiers manquants: {prefix}{missing_list}")

        # Générer le fichier de métadonnées si en mode bullet
        if granularity == "bullet":
            _generate_bullet_metadata(audio_files, config, temp_dir)

        return audio_files

    except Exception as e:
        logging.error(f"Erreur lors de l'initialisation Gemini TTS: {e}")
        raise


def check_directories(config):
    """
    Vérifie que les répertoires nécessaires existent, les crée si nécessaire.

    Args:
        config (dict): Configuration du projet
    """
    # Liste des clés qui représentent des dossiers (pas des fichiers)
    directory_keys = ["source", "b_roll", "heygen", "assets", "temp"]

    for key, path in config["paths"].items():
        # Ne traiter que les vrais dossiers
        if key in directory_keys:
            directory = Path(path)
            logging.info(f"... Vérification/création du répertoire: {path}")
            directory.mkdir(exist_ok=True)


def parse_arguments():
    """
    Analyse les arguments de la ligne de commande.

    Returns:
        argparse.Namespace: Arguments analysés
    """
    parser = argparse.ArgumentParser(description="Exponential video generation")
    parser.add_argument(
        "-s", "--script", action="store_true", help="Generate scripts only"
    )
    parser.add_argument(
        "-a", "--audio", action="store_true", help="Generate TTS audio only (OpenAI)"
    )
    parser.add_argument(
        "-ag",
        "--audio-gemini",
        action="store_true",
        help="Generate TTS audio only (Google Gemini)",
    )
    parser.add_argument(
        "--meta", action="store_true", help="Extract and analyze b-roll video metadata"
    )
    parser.add_argument(
        "--vectorbroll",
        action="store_true",
        help="Prepare b-roll selections using vector search (embeddings). Generates broll_timing.json. In TTS mode, automatically extends B-rolls to eliminate gaps.",
    )
    parser.add_argument(
        "--testbrollchoice",
        action="store_true",
        help="Test b-roll selection for first rush only",
    )
    parser.add_argument(
        "--brolls-selection-correct",
        action="store_true",
        help="Clean broll_selections.json file by removing missing b-rolls",
    )
    parser.add_argument(
        "--create_project", action="store_true", help="Create a new project"
    )
    parser.add_argument(
        "--storykw",
        action="store_true",
        help="Generate keywords list for script i3.txt illustration images",
    )
    parser.add_argument(
        "--youtube_help",
        action="store_true",
        help="Generate YouTube information (titles, description, tags) based on script i3.txt",
    )
    parser.add_argument(
        "project_name", nargs="?", help="Project name (required except for --meta)"
    )
    parser.add_argument(
        "--get_ori",
        metavar="YOUTUBE_URL",
        help="Get YouTube video transcript (original audio language) and save to ../projects/<project>/ori_vid.txt",
    )

    return parser.parse_args()


def validate_project_argument(args):
    """
    Valide que le nom du projet est valide et nettoie les préfixes/suffixes.

    Args:
        args: Arguments analysés

    Raises:
        SystemExit: Si le nom du projet est invalide
    """
    # Nettoyer le nom du projet
    project_name = args.project_name

    # Supprimer tous les préfixes "projects/" et "../projects/" (au cas où il y en aurait plusieurs)
    while project_name.startswith("projects/") or project_name.startswith(
        "../projects/"
    ):
        if project_name.startswith("../projects/"):
            project_name = project_name[13:]  # Supprimer "../projects/"
        else:
            project_name = project_name[9:]  # Supprimer "projects/"
        logging.info(f"🔧 Préfixe 'projects/' détecté et supprimé")

    # Supprimer tous les slashes finaux
    while project_name.endswith("/"):
        project_name = project_name[:-1]  # Supprimer le slash final
        logging.info(f"🔧 Slash final détecté et supprimé")

    # Vérifier que le nom n'est pas vide après nettoyage
    if not project_name:
        logging.error("❌ ERREUR: Nom de projet vide après nettoyage")
        logging.error(f"   → Nom original: {args.project_name}")
        sys.exit(1)

    # Mettre à jour le nom du projet dans les arguments
    args.project_name = project_name

    # Vérifier que le nom du projet est valide (pas de caractères spéciaux)
    import re

    if not re.match(r"^[a-zA-Z0-9_-]+$", project_name):
        logging.error("❌ ERREUR: Nom de projet invalide")
        logging.error(
            "   → Utilisez uniquement des lettres, chiffres, tirets et underscores"
        )
        logging.error(f"   → Nom nettoyé: {project_name}")
        logging.error(f"   → Nom original: {args.project_name}")
        sys.exit(1)


def get_projects_path():
    """
    Retourne le chemin vers le dossier des projets.

    Returns:
        Path: Chemin vers le dossier des projets
    """
    config = load_config()
    return Path(config["paths"].get("projects", "../projects"))


def get_project_temp_path(project_name):
    """
    Retourne le chemin du dossier temp pour le projet spécifié.

    Args:
        project_name (str): Nom du projet

    Returns:
        Path: Chemin vers le dossier temp du projet
    """
    return get_projects_path() / project_name / "temp"


def ensure_project_directories(project_name):
    """
    Crée les dossiers nécessaires pour le projet.

    Args:
        project_name (str): Nom du projet
    """
    # Créer le dossier temp du projet
    project_temp_path = get_project_temp_path(project_name)
    project_temp_path.mkdir(parents=True, exist_ok=True)
    logging.info(f"📁 Dossier projet créé: {project_temp_path}")

    # Créer le dossier du projet s'il n'existe pas
    project_dir = get_projects_path() / project_name
    project_dir.mkdir(parents=True, exist_ok=True)

    # Informer l'utilisateur du fichier ori_vid.txt à créer
    project_ori_vid_path = project_dir / "ori_vid.txt"
    if not project_ori_vid_path.exists():
        logging.info(f"📄 Créez le fichier: {project_ori_vid_path}")
        logging.info(
            f"💡 Ajoutez votre transcript dans ce fichier avant de lancer la génération"
        )


def update_config_for_project(config, project_name):
    """
    Met à jour la configuration pour utiliser les dossiers du projet.

    Args:
        config (dict): Configuration originale
        project_name (str): Nom du projet

    Returns:
        dict: Configuration mise à jour
    """
    # Créer une copie de la configuration
    updated_config = config.copy()

    # Mettre à jour le chemin temp
    project_temp_path = get_project_temp_path(project_name)
    updated_config["paths"]["temp"] = str(project_temp_path)

    # Ajouter le chemin vers le fichier ori_vid.txt du projet
    project_ori_vid_path = get_projects_path() / project_name / "ori_vid.txt"
    updated_config["paths"]["project_ori_vid"] = str(project_ori_vid_path)

    return updated_config


def check_initial_structure(config):
    """Vérifie la présence des fichiers et dossiers requis."""
    source_path = Path(config["paths"]["source"])

    # Vérifier que le dossier source/ existe (pour intro.mp4, musique.mp3, etc.)
    if not source_path.exists():
        raise FileNotFoundError(
            "Le dossier source/ est requis et doit contenir :\n"
            "- intro.mp4 (optionnel)\n"
            "- musique.mp3 (optionnel)\n"
            "- extrait_imovie_warren_buffet.mp4 (optionnel)"
        )

    # Vérifier ori_vid.txt du projet si on doit générer les scripts
    if sys.argv[1:] and any(arg in ["-s", "--script"] for arg in sys.argv[1:]):
        project_ori_vid_path = Path(config["paths"]["project_ori_vid"])
        if not project_ori_vid_path.exists():
            raise FileNotFoundError(
                f"Le fichier {project_ori_vid_path} est requis pour la génération des scripts"
            )


def play_completion_sound():
    """Émet un bip sonore répété 3 fois pour signaler la fin de la génération de la vidéo."""
    import time

    # Répéter le bip 5 fois avec une courte pause entre chaque
    for _ in range(5):
        print(
            "\a", flush=True
        )  # Caractère ASCII BEL avec flush pour assurer l'émission immédiate
        time.sleep(0.4)  # Attendre 0.3 seconde entre chaque bip

    logging.info("Signal sonore de fin de génération émis (bips)")


def _detect_original_language(url: str) -> str | None:
    """
    Détecte la langue audio originale via yt-dlp -J.
    Heuristiques: 'language' → première clé de 'automatic_captions' → première clé de 'subtitles'.
    """
    try:
        result = subprocess.run(
            ["yt-dlp", "-J", "--no-warnings", url], capture_output=True, text=True
        )
        if result.returncode != 0:
            logging.warning(f"yt-dlp -J a échoué: {result.stderr.strip()}")
            return None
        import json as _json

        data = _json.loads(result.stdout)
        lang = data.get("language")
        if lang:
            return lang
        ac = data.get("automatic_captions") or {}
        if isinstance(ac, dict) and ac:
            # prendre la première clé (p.ex. 'en')
            return next(iter(ac.keys()))
        subs = data.get("subtitles") or {}
        if isinstance(subs, dict) and subs:
            return next(iter(subs.keys()))
        return None
    except Exception as e:
        logging.warning(f"Impossible de détecter la langue originale: {e}")
        return None


def _run_yt_dlp_for_subtitles(
    url: str, output_dir: Path
) -> tuple[Path | None, str | None]:
    """
    Télécharge TOUS les sous-titres en VTT via yt-dlp dans output_dir.
    Retourne (meilleur_fichier_vtt, langue_originale_detectee).
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        base_out = str(output_dir / "%(id)s.%(ext)s")
        player_clients = ["android", "tv", "web"]
        last_err = None
        for client in player_clients:
            cmd = [
                "yt-dlp",
                "--skip-download",
                "--write-sub",
                "--write-auto-sub",
                "--sub-format",
                "vtt",
                "--sub-langs",
                "all",
                "--extractor-args",
                f"youtube:player_client={client}",
                "-o",
                base_out,
                url,
            ]
            logging.info(
                f"Téléchargement des sous-titres avec yt-dlp (client={client})…"
            )
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                break
            last_err = result.stderr.strip()
        if result.returncode != 0:
            logging.error(f"yt-dlp a échoué: {last_err}")
        # Détecter la langue originale
        orig_lang = _detect_original_language(url)
        # Chercher d'abord la langue originale détectée
        if orig_lang:
            pattern = f"*.{orig_lang}*.vtt"
            matches = sorted(glob.glob(str(output_dir / pattern)))
            if matches:
                return Path(matches[0]), orig_lang
        # Fallback: EN, puis FR, sinon n'importe quel .vtt
        for lang in ("en", "fr"):
            matches = sorted(glob.glob(str(output_dir / f"*.{lang}*.vtt")))
            if matches:
                return Path(matches[0]), orig_lang
        any_vtt = sorted(glob.glob(str(output_dir / "*.vtt")))
        return (Path(any_vtt[0]), orig_lang) if any_vtt else (None, orig_lang)
    except Exception as e:
        logging.error(f"Erreur yt-dlp: {e}")
        return None, None


# ==== Fallback API (youtube-transcript-api) ====
def _extract_video_id(url: str) -> str | None:
    """Extrait l'ID YouTube depuis diverses formes d'URL."""
    patterns = [
        r"v=([\w-]{11})",
        r"youtu\.be/([\w-]{11})",
        r"/shorts/([\w-]{11})",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def _fetch_transcript_via_api(url: str) -> str:
    """
    Fallback via youtube-transcript-api (compatible anciennes versions):
    essaie get_transcript avec priorités langue originale → en → fr → défaut.
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        video_id = _extract_video_id(url)
        if not video_id:
            return ""
        # Construire la liste d'essais par langues
        candidates = []
        try:
            orig = _detect_original_language(url)
            if orig:
                candidates.append([orig])
        except Exception:
            pass
        candidates.extend((["en"], ["fr"], ["en", "fr"], None))
        for langs in candidates:
            try:
                if langs is None:
                    entries = YouTubeTranscriptApi.get_transcript(video_id)
                else:
                    entries = YouTubeTranscriptApi.get_transcript(
                        video_id, languages=langs
                    )
                text = "\n".join(
                    html.unescape(e.get("text", "")).strip()
                    for e in entries
                    if e.get("text")
                )
                if text.strip():
                    return text
            except Exception:
                continue
        return ""
    except ImportError:
        logging.info("youtube-transcript-api non installé: pas de fallback API")
        return ""
    except Exception as e:
        logging.warning(f"Fallback transcript API a échoué: {e}")
        return ""

    # Fallback API supprimé sur demande


def _vtt_to_plain_text(vtt_path: Path) -> str:
    """
    Convertit un fichier .vtt en texte brut sans timecodes ni numéros de cues.
    """
    try:
        lines: list[str] = []
        with open(vtt_path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n")
                if not line:
                    continue
                if line.startswith("WEBVTT") or line.startswith("NOTE"):
                    continue
                if re.match(r"^\d+$", line):
                    continue
                if re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> ", line):
                    continue
                # Retirer les balises simples <c>…</c> et autres tags
                line = re.sub(r"<[^>]+>", "", line)
                lines.append(line)
        # Dédupliquer les répétitions adjacentes fréquentes dans les auto-subs
        deduped: list[str] = []
        for l in lines:
            if not deduped or deduped[-1] != l:
                deduped.append(l)
        text = "\n".join(deduped).strip()
        # Normaliser les espaces multiples
        text = re.sub(r"[ \t]+", " ", text)
        return text
    except Exception as e:
        logging.error(f"Erreur conversion VTT→texte: {e}")
        return ""


def get_ori_from_youtube(url: str, config: dict, project_name: str) -> bool:
    """
    Récupère le transcript YouTube via yt-dlp et écrit projects/<projet>/ori_vid.txt.
    """
    try:
        temp_dir = Path(config["paths"]["temp"]) / "yt_transcript"
        vtt_file, orig_lang = _run_yt_dlp_for_subtitles(url, temp_dir)
        if vtt_file and vtt_file.exists():
            text = _vtt_to_plain_text(vtt_file)
        else:
            text = ""
        if not text:
            # Fallback API
            logging.info("Tentative de fallback via youtube-transcript-api…")
            text = _fetch_transcript_via_api(url)
        if not text:
            print(
                "❌ Impossible de récupérer un transcript pour cette URL (yt-dlp et fallback API)"
            )
            return False
        target_path = get_projects_path() / project_name / "ori_vid.txt"
        with open(target_path, "w", encoding="utf-8") as out:
            out.write(text + "\n")
        if orig_lang:
            print(
                f"✅ Transcript enregistré: {target_path} (langue détectée: {orig_lang})"
            )
        else:
            print(f"✅ Transcript enregistré: {target_path}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la récupération du transcript: {e}")
        return False


def validate_mode_consistency(config, args):
    """
    Valide la cohérence entre le mode configuré et les options demandées.

    Args:
        config (dict): Configuration chargée
        args: Arguments de la ligne de commande

    Raises:
        SystemExit: Si une incohérence est détectée
    """
    audio_mode = config["audio"].get("generation_mode", "heygen")

    # Vérifications de cohérence
    if audio_mode in ["openai_tts", "gemini_tts"]:
        pass  # No rush option to check

        # Vérifier la clé API OpenAI
        if not config["api"]["openai"]["api_key"] or config["api"]["openai"][
            "api_key"
        ].startswith("sk-"):
            if len(config["api"]["openai"]["api_key"]) < 50:
                logging.error(
                    "❌ ERREUR: Clé API OpenAI invalide ou manquante pour le mode TTS"
                )
                logging.error("   → Vérifiez votre clé API dans config.yml")
                sys.exit(1)

    elif audio_mode == "heygen":
        if args.audio:
            logging.error(
                "❌ ERREUR: Option -a (audio TTS) incompatible avec le mode 'heygen'"
            )
            logging.error(
                "   → Changez 'generation_mode: openai_tts' dans config.yml ou utilisez -r au lieu de -a"
            )
            sys.exit(1)
        if args.audio_gemini:
            logging.error(
                "❌ ERREUR: Option -ag (audio Gemini TTS) incompatible avec le mode 'heygen'"
            )
            logging.error(
                "   → Changez 'generation_mode: gemini_tts' dans config.yml ou utilisez -r au lieu de -ag"
            )
            sys.exit(1)

        # Vérifier la clé API Heygen si nécessaire
        if not config["api"]["heygen"]["api_key"]:
            logging.error("❌ ERREUR: Clé API Heygen manquante pour le mode Heygen")
            logging.error("   → Vérifiez votre clé API dans config.yml")
            sys.exit(1)

    elif audio_mode == "gemini_tts":
        pass  # No rush option to check

        # Vérifier la clé API Gemini
        if not config["api"]["gemini"]["api_key"]:
            logging.error("❌ ERREUR: Clé API Gemini manquante pour le mode TTS")
            logging.error("   → Vérifiez votre clé API dans config.yml")
            sys.exit(1)

    else:
        logging.error(f"❌ ERREUR: Mode audio '{audio_mode}' non supporté")
        logging.error(
            "   → Utilisez 'heygen', 'openai_tts' ou 'gemini_tts' dans config.yml"
        )
        sys.exit(1)

    # Vérifier que les dépendances nécessaires sont installées
    if audio_mode == "openai_tts":
        try:
            import openai
        except ImportError:
            logging.error("❌ ERREUR: Module 'openai' manquant pour le mode TTS")
            logging.error("   → Installez avec: pip install openai")
            sys.exit(1)
    elif audio_mode == "gemini_tts":
        try:
            import requests
        except ImportError:
            logging.error(
                "❌ ERREUR: Module 'requests' manquant pour le mode Gemini TTS"
            )
            logging.error("   → Installez avec: pip install requests")
            sys.exit(1)
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            logging.error(
                "❌ ERREUR: Module 'google-genai' manquant pour le mode Gemini TTS"
            )
            logging.error("   → Installez avec: pip install google-genai")
            sys.exit(1)

    # Afficher le mode détecté
    logging.info(f"✅ Mode audio détecté: {audio_mode}")


def generate_story_keywords(project_name):
    """
    Generate a list of keywords for illustration images from the i3.txt script.

    Args:
        project_name (str): Project name
    """
    # Path to i3.txt file
    i3_path = get_projects_path() / project_name / "temp" / "i3.txt"

    if not i3_path.exists():
        print(f"❌ i3.txt file not found: {i3_path}")
        return

    # Read the content of i3.txt file
    try:
        with open(i3_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier i3.txt: {e}")
        return

    # Prompt pour GPT-4
    prompt = f"""
Imaginez que vous entrez dans un casino. Les lumières clignotent, les sons électroniques vous happent, les tables sont pleines de joueurs excités. Sauf qu'ici, le croupier vous tend la main et vous dit : "Bienvenue. Ici, vous ne perdrez jamais." Vous riez, c'est une blague, non ? Personne ne gagne à tous les coups. Et pourtant… ce casino-là existe. Mais il ne distribue pas des jetons : il distribue des milliards. Et à sa tête, il y a un vieil homme en costume simple, qui boit du Coca light et mange des burgers à 2 dollars. Son nom : Warren Buffett. Il est l'un des hommes les plus riches de l'histoire, avec plus de 137 milliards de dollars. Pourtant, contrairement aux Elon Musk ou Jeff Bezos, il n'a pas fondé d'entreprise tech, il n'a pas envoyé de fusées dans l'espace. Sa seule arme : une règle. Une règle que 90 % des gens ignorent, ou méprisent. Elle tient en une phrase, presque ridicule : "Ne jamais perdre d'argent." Voilà. C'est tout. Et si vous croyez que c'est simpliste, attendez d'apprendre ce qu'il y a derrière cette phrase. Car ce n'est pas une maxime, c'est un système de pensée. Un système conçu pour survivre à toutes les crises.

Warren Buffett n'a rien d'un magicien. C'est un artisan de la finance. Il passe ses journées à lire, analyser, comprendre. Pendant que la planète s'affole sur les tendances du moment, lui étudie les fondamentaux d'une entreprise comme un horloger démonte une montre. Chaque pièce compte. Mais ce qui frappe, c'est son obsession de la perte. Il le répète encore et encore : "Règle numéro 1 : ne jamais perdre d'argent. Règle numéro 2 : ne jamais oublier la règle numéro 1." Ce n'est pas une blague. Pour lui, perdre un euro, ce n'est pas anodin. C'est tuer son potentiel futur. Il compare chaque dollar à un soldat. Perdez-le aujourd'hui, et vous perdez tout ce qu'il aurait pu vous rapporter dans 5, 10, 20 ans. La majorité des investisseurs pensent rendement, lui pense protection. Ils veulent doubler la mise, lui veut éviter le naufrage. C'est la différence entre un pirate et un capitaine de navire. L'un cherche le trésor, l'autre veut rentrer entier. Et ce qui est fascinant, c'est que cette prudence, moquée au départ, l'a rendu plus riche que tous les autres.

Pendant que les foules courent après les tendances brûlantes, Warren Buffett reste sur le quai. En 1999, c'est la folie des .com. Internet promet de tout révolutionner. Les actions montent en flèche. Des dizaines de milliers de personnes deviennent millionnaires en quelques mois. Buffett, lui, ne bouge pas. Il regarde. Et il refuse d'investir. "Je ne mets pas un cent dans ce que je ne comprends pas", dit-il. On le traite de vieux con, de dinosaure. Deux ans plus tard, la bulle explose. Le Nasdaq perd 78 % de sa valeur. Les fortunes s'effondrent. Buffett ? Il est intact. Mieux : il a de la trésorerie pour acheter à bas prix. C'est la première grande leçon. Refuser d'investir dans ce qu'on ne comprend pas. Pas parce que c'est risqué. Mais parce que c'est flou. Parce qu'il suffit d'une seule erreur pour anéantir des années de travail. Buffett évite les choses brillantes mais opaques. Il préfère l'ennuyeux et lisible. C'est le paradoxe : là où les autres cherchent l'or dans la boue, lui cherche la boue… stable, solide, fiable.


Pour illustrer ce texte, je vais avoir besoin d'images d'illustration que je vais chercher sur un moteur de recherche d'images.

Je souhaite donc une liste de keywords (en liste js) pour obtenir les images d'illustration correspondante à chaque phrase ou paragraphe.


Voici le résultat exemple pour le texte précédent : 

const keywords = [
  "casino-player", "dealer", "lose", "laugh", "chips", "billions", "old", "burger", "coke",
  "business-money", "technology", "rocket", "rule", "simple", "mindset", "economic-crisis", "magician",
  "craftsman", "understand", "trends", "watchmaker", "law", "euro", "future", "soldier", "years",
  "protection", "shipwreck", "pirate", "caution", "rich", "yacht", "internet", "refuse", "cent",
  "price", "blur", "work", "mud", "gold"
];

Note: "Buffett-perspective" est un exemple de mauvaise proposition car les personalités ne sont pas disponibles dans storyblocks



Maintenant tu vas générer une nouvelle liste de keyword pour le texte suivant. Je ne veux aucune explication, juste la liste, avec peu keywords d'un seul mot et 3 maximum par paragraphe.

{content}

la réponse sera juste affichée dans la console, pour pouvoir être copiée collée. cette option est donc indépendante du reste mais elle prend aussi l'argument obligatoire du nom du projet à la fin.
"""

    # Appeler GPT-4
    try:
        from script_and_voice.paraphraser import Paraphraser

        config = load_config()
        config["paths"]["temp"] = str(get_project_temp_path(project_name))
        paraphraser = Paraphraser(config)

        messages = [
            {
                "role": "system",
                "content": "You are an expert in generating keywords for illustration images.",
            },
            {"role": "user", "content": prompt},
        ]

        response = paraphraser.call_gpt5_text_only(messages)
        print(response)

        # Extraire les keywords et les sauvegarder en CSV
        try:
            import csv
            import json
            import re
            from datetime import datetime

            # Nettoyer la réponse (enlever les balises markdown si présentes)
            cleaned_response = response.strip()
            if cleaned_response.startswith("```"):
                # Enlever les balises markdown
                cleaned_response = re.sub(r"^```\w*\s*", "", cleaned_response)
                cleaned_response = re.sub(r"\s*```$", "", cleaned_response)

            # Extraire les keywords du JavaScript (const keywords = [...])
            if "const keywords =" in cleaned_response:
                # Extraire la partie entre crochets
                start = cleaned_response.find("[")
                end = cleaned_response.rfind("]") + 1
                if start != -1 and end != 0:
                    array_content = cleaned_response[start:end]
                    # Parser le contenu du tableau
                    keywords = json.loads(array_content)
                else:
                    raise ValueError("Impossible de trouver le tableau keywords")
            else:
                raise ValueError("Format de réponse invalide")

            if keywords:
                # Supprimer les doublons et trier alphabétiquement
                unique_keywords = sorted(list(set(keywords)))

                # Timestamp actuel
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Lire les keywords existants dans le CSV
                existing_keywords = set()
                csv_path = Path("keywords.csv")

                if csv_path.exists():
                    with open(csv_path, "r", encoding="utf-8") as csvfile:
                        reader = csv.reader(csvfile)
                        for row in reader:
                            if row:  # Vérifier que la ligne n'est pas vide
                                existing_keywords.add(
                                    row[0]
                                )  # Première colonne = keyword

                # Trouver les nouveaux keywords (sans doublons)
                new_keywords = [
                    kw for kw in unique_keywords if kw not in existing_keywords
                ]

                # Sauvegarder seulement les nouveaux keywords en CSV
                if new_keywords:
                    # Ajouter les nouveaux keywords au CSV existant
                    with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
                        writer = csv.writer(csvfile)
                        for keyword in new_keywords:
                            writer.writerow([keyword, timestamp])

                    print(f"\n✅ {len(new_keywords)} nouveaux keywords ajoutés au CSV")

                    # Afficher les nouveaux keywords en format JavaScript
                    print(f"\n🆕 Nouveaux keywords ({len(new_keywords)}):")
                    keywords_js = ", ".join([f'"{kw}"' for kw in new_keywords])
                    print(f"const newKeywords = [{keywords_js}];")
                else:
                    print(f"\nℹ️ Tous les keywords étaient déjà présents dans le CSV")

            else:
                print("❌ Aucun keyword trouvé dans la réponse")

        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde CSV: {e}")

    except Exception as e:
        print(f"❌ Erreur lors de la génération des keywords: {e}")


def generate_youtube_help(project_name):
    """
    Generate YouTube information (titles, description, tags) based on the i3.txt script.

    Args:
        project_name (str): Project name
    """
    # Path to i3.txt file
    i3_path = get_projects_path() / project_name / "temp" / "i3.txt"

    if not i3_path.exists():
        print(f"❌ i3.txt file not found: {i3_path}")
        return

    # Read the content of i3.txt file
    try:
        with open(i3_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading i3.txt file: {e}")
        return

    # YouTube prompt
    prompt = f"""
I am about to publish my video on YouTube.

1. Generate 5 best possible YouTube titles for my video (respect the max character count, try to be clickbait)

2. Generate a short description putting 3 tags only at the end. And below the exact sentence: This video is for informational and entertainment purposes only. It does not constitute financial, investment or legal advice in any way. Always do your own research or consult a professional before making financial decisions.

3. The 3 tags with #, put them again in the "Tags with commas" paragraph where you don't put the # and you separate them with commas

Here is my video script:
{content}
"""

    # Display the prompt for thumbnail BEFORE the rest
    print("\n" + "=" * 80)
    print("To put in GPT with the inspiration thumbnail:")
    print(
        "I am publishing my video on YouTube. You will find the thumbnail of the video I was inspired by. Generate a similar thumbnail for my video in French. Create a 16/9 image with the same person, but with a black and white background with yellow or white colors for the elements and text"
    )
    print("=" * 80)

    # Appeler GPT-4
    try:
        from script_and_voice.paraphraser import Paraphraser

        config = load_config()
        config["paths"]["temp"] = str(get_project_temp_path(project_name))
        paraphraser = Paraphraser(config)

        messages = [
            {
                "role": "system",
                "content": "You are an expert in YouTube marketing and viral content creation.",
            },
            {"role": "user", "content": prompt},
        ]

        response = paraphraser.call_gpt5_text_only(messages)
        print(response)

    except Exception as e:
        print(f"❌ Erreur lors de la génération des infos YouTube: {e}")


def clean_broll_selections():
    """Nettoie le fichier broll_selections.json en retirant les b-rolls manquantes"""
    try:
        broll_file = Path("temp/broll_selections.json")
        if not broll_file.exists():
            logging.error("Fichier broll_selections.json non trouvé")
            return False

        with open(broll_file, "r") as f:
            selections = json.load(f)

        cleaned_selections = {}
        for rush_id, rush_data in selections.items():
            valid_brolls = []
            for broll in rush_data["brolls"]:
                broll_path = (
                    Path("b-roll") / broll["filename"]
                )  # On utilise "filename" au lieu de "path"
                if broll_path.exists():
                    valid_brolls.append(broll)
                else:
                    logging.info(f"Suppression de la b-roll manquante: {broll_path}")

            # On garde la même structure avec duration et brolls
            cleaned_selections[rush_id] = {
                "duration": rush_data["duration"],
                "brolls": valid_brolls,
            }

        with open(broll_file, "w") as f:
            json.dump(cleaned_selections, f, indent=2)

        logging.info("Nettoyage des b-rolls terminé avec succès")
        return True

    except Exception as e:
        logging.error(f"Erreur lors du nettoyage des b-rolls: {e}")
        return False


def main():
    """Fonction principale du script"""
    setup_logging()
    args = parse_arguments()

    # L'option --meta ne nécessite pas de nom de projet
    if args.meta:
        logging.info("Début de l'extraction des métadonnées des b-rolls...")
        from b_roll import MetaExtractor

        config = load_config()
        extractor = MetaExtractor(config)
        total, success = extractor.process_all_videos()
        logging.info(
            f"Extraction des métadonnées terminée : {success}/{total} vidéos traitées"
        )
        return

    # Validation obligatoire du nom du projet pour les autres options
    if not args.project_name:
        print("❌ Erreur: Le nom du projet est obligatoire (sauf pour l'option --meta)")
        sys.exit(1)

    validate_project_argument(args)
    ensure_project_directories(args.project_name)

    config = load_config()

    # Mise à jour de la configuration pour utiliser le dossier temp du projet
    config = update_config_for_project(config, args.project_name)

    # Récupération du transcript YouTube → ori_vid.txt (skip exit si --pipeline)
    if args.get_ori and not args.pipeline:
        success = get_ori_from_youtube(args.get_ori, config, args.project_name)
        sys.exit(0 if success else 1)

    # Si --create_project, on sort après avoir créé le projet
    if args.create_project:
        logging.info(f"✅ Projet '{args.project_name}' créé avec succès.")
        sys.exit(0)

    logging.info(f"📁 Utilisation du projet: {args.project_name}")

    check_initial_structure(config)
    check_directories(config)

    # Ajout de l'option vectorbroll
    if args.vectorbroll:
        logging.info("Début de la préparation des b-rolls vectorielle...")
        from b_roll import prepare_brolls_vector

        prepare_brolls_vector(config=config)
        return

    if args.testbrollchoice:
        logging.info("Mode test de sélection des b-rolls")
        from b_roll import BRollFinder

        # Assume first rush is already generated and available
        first_rush_path = os.path.join(config["paths"]["heygen"], "rush1.mp4")
        if not os.path.exists(first_rush_path):
            logging.error(f"Le rush 1 n'existe pas: {first_rush_path}")
            return

        # Get first rush duration (approximation)
        # Use default duration for testing
        rush_duration = 10.0  # Approximate duration for testing

        # Create BRollFinder instance and prepare b-rolls for this rush only
        b_roll_finder = BRollFinder(config)
        json_path = b_roll_finder.generate_broll_timing([rush_duration])

        logging.info(
            f"Test de sélection des b-rolls terminé, résultats sauvegardés dans {json_path}"
        )
        return

    if args.brolls_selection_correct:
        from b_roll import clean_broll_selections

        config = load_config()
        if clean_broll_selections(config):
            logging.info("Nettoyage des sélections de b-rolls terminé avec succès")
        else:
            logging.error("Erreur lors du nettoyage des sélections de b-rolls")
        return

    # Génération des keywords pour images d'illustration
    if args.storykw:
        generate_story_keywords(args.project_name)
        return

    # Génération des informations YouTube
    if args.youtube_help:
        generate_youtube_help(args.project_name)
        return

    # Validation de la cohérence des modes avant exécution
    validate_mode_consistency(config, args)

    try:
        # Étapes unitaires (mode non-pipeline)
        # Étape 1: Génération des scripts
        if args.script:
            logging.info("Début de la génération des scripts...")

            # Use the new CLI module instead of direct paraphraser
            import subprocess
            import os

            # Get language from config or default to french
            language = config.get("script", {}).get("language", "french")

            # Prepare input file path
            input_file = Path(config["paths"]["project_ori_vid"])
            if not input_file.exists():
                logging.error(f"Input file not found: {input_file}")
                sys.exit(1)

            # Call the CLI module
            cmd = [
                sys.executable,
                "script_and_voice/module_script_and_voice.py",
                "--project",
                args.project_name,
                "--language",
                language,
                "--input-file",
                str(input_file),
            ]

            logging.info(f"🚀 Calling script and voice module: {' '.join(cmd)}")

            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, cwd=os.getcwd()
                )

                if result.returncode == 0:
                    logging.info(
                        "✅ Script and voice generation completed successfully"
                    )
                    logging.info("📋 Output:")
                    for line in result.stdout.split("\n"):
                        if line.strip():
                            logging.info(f"   {line}")
                else:
                    logging.error("❌ Script and voice generation failed")
                    logging.error(f"📋 Return code: {result.returncode}")
                    if result.stdout:
                        logging.error("📋 Standard output:")
                        for line in result.stdout.split("\n"):
                            if line.strip():
                                logging.error(f"   {line}")
                    if result.stderr:
                        logging.error("📋 Error output:")
                        for line in result.stderr.split("\n"):
                            if line.strip():
                                logging.error(f"   {line}")
                    sys.exit(1)

            except Exception as e:
                logging.error(f"❌ Error calling script and voice module: {e}")
                logging.error(f"📋 Command attempted: {' '.join(cmd)}")
                import traceback

                logging.error(f"📋 Traceback: {traceback.format_exc()}")
                sys.exit(1)

        # Étape 2: Génération audio TTS (OpenAI)
        if args.audio:
            logging.info("Début de la génération audio TTS (OpenAI)...")
            from src.tts_generator import TTSGenerator  # Import conditionnel

            tts_generator = TTSGenerator(config)

            try:
                # Charger le contenu de i3.txt pour créer les fichiers rush{i}_text.txt
                i3_path = Path(config["paths"]["temp"]) / "i3.txt"

                if not i3_path.exists():
                    raise FileNotFoundError(
                        f"Le fichier {i3_path} n'existe pas. Exécutez d'abord l'option -s."
                    )

                with open(i3_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Détecter le mode de granularité pour créer les bons fichiers de compatibilité B-roll
                granularity = (
                    config.get("audio", {})
                    .get("openai_tts", {})
                    .get("granularity", "rush")
                )

                if granularity == "bullet":
                    # Mode bullet : chaque paragraphe de i3.txt est déjà un bullet thématique
                    bullets = [p.strip() for p in content.split("\n\n") if p.strip()]

                    # Sauvegarder les fichiers bullet{i}_text.txt ET rush{i}_text.txt pour compatibilité B-roll
                    for i, bullet_text in enumerate(bullets, 1):
                        # Fichier bullet pour clarté
                        bullet_text_file = (
                            Path(config["paths"]["temp"]) / f"bullet{i}_text.txt"
                        )
                        with open(bullet_text_file, "w", encoding="utf-8") as f:
                            f.write(bullet_text)

                        # Fichier rush pour compatibilité B-roll existant
                        rush_text_file = (
                            Path(config["paths"]["temp"]) / f"rush{i}_text.txt"
                        )
                        with open(rush_text_file, "w", encoding="utf-8") as f:
                            f.write(bullet_text)

                        logging.info(
                            f"Texte du bullet TTS {i} sauvegardé dans {bullet_text_file} et {rush_text_file}"
                        )

                else:
                    # Mode legacy : regrouper par 4 paragraphes (comme Heygen)
                    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
                    grouped_paragraphs = []
                    for i in range(0, len(paragraphs), 4):
                        group = paragraphs[i : i + 4]
                        grouped_text = "\n\n".join(group)
                        grouped_paragraphs.append(grouped_text)

                    # Sauvegarder les fichiers rush{i}_text.txt pour compatibilité B-roll
                    for i, text in enumerate(grouped_paragraphs, 1):
                        rush_text_file = (
                            Path(config["paths"]["temp"]) / f"rush{i}_text.txt"
                        )
                        with open(rush_text_file, "w", encoding="utf-8") as f:
                            f.write(text)
                        logging.info(
                            f"Texte du rush TTS {i} sauvegardé dans {rush_text_file}"
                        )

                # Générer l'audio TTS
                audio_files = tts_generator.generate_all_audio()
                logging.info("Génération audio TTS terminée avec succès!")

                # Signal sonore à la fin du traitement
                play_completion_sound()

            except FileNotFoundError as e:
                logging.error(f"Erreur: {e}")
                sys.exit(1)
            except Exception as e:
                logging.error(f"Erreur lors de la génération audio TTS: {e}")
                sys.exit(1)

        # Étape 2bis: Génération audio TTS (Google Gemini)
        elif args.audio_gemini:
            logging.info("Début de la génération audio TTS (Google Gemini)...")

            try:
                # Vérifier que google-genai est installé
                try:
                    from google import genai
                    from google.genai import types
                except ImportError:
                    logging.error(
                        "❌ ERREUR: Module 'google-genai' manquant pour le mode Gemini TTS"
                    )
                    logging.error("   → Installez avec: pip install google-genai")
                    sys.exit(1)

                # Charger le contenu de i3.txt pour créer les fichiers rush{i}_text.txt
                i3_path = Path(config["paths"]["temp"]) / "i3.txt"

                if not i3_path.exists():
                    raise FileNotFoundError(
                        f"Le fichier {i3_path} n'existe pas. Exécutez d'abord l'option -s."
                    )

                with open(i3_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Détecter le mode de granularité
                granularity = (
                    config.get("audio", {})
                    .get("gemini_tts", {})
                    .get("granularity", "rush")
                )

                if granularity == "bullet":
                    # Mode bullet : chaque paragraphe de i3.txt est déjà un bullet thématique
                    bullets = [p.strip() for p in content.split("\n\n") if p.strip()]

                    # Sauvegarder les fichiers bullet{i}_text.txt ET rush{i}_text.txt pour compatibilité B-roll
                    for i, bullet_text in enumerate(bullets, 1):
                        # Fichier bullet pour clarté
                        bullet_text_file = (
                            Path(config["paths"]["temp"]) / f"bullet{i}_text.txt"
                        )
                        with open(bullet_text_file, "w", encoding="utf-8") as f:
                            f.write(bullet_text)

                        # Fichier rush pour compatibilité B-roll existant
                        rush_text_file = (
                            Path(config["paths"]["temp"]) / f"rush{i}_text.txt"
                        )
                        with open(rush_text_file, "w", encoding="utf-8") as f:
                            f.write(bullet_text)

                        logging.info(
                            f"Texte du bullet Gemini TTS {i} sauvegardé dans {bullet_text_file} et {rush_text_file}"
                        )

                else:
                    # Mode legacy : regrouper par 4 paragraphes (comme Heygen)
                    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
                    grouped_paragraphs = []
                    for i in range(0, len(paragraphs), 4):
                        group = paragraphs[i : i + 4]
                        grouped_text = "\n\n".join(group)
                        grouped_paragraphs.append(grouped_text)

                    # Sauvegarder les fichiers rush{i}_text.txt pour compatibilité B-roll
                    for i, text in enumerate(grouped_paragraphs, 1):
                        rush_text_file = (
                            Path(config["paths"]["temp"]) / f"rush{i}_text.txt"
                        )
                        with open(rush_text_file, "w", encoding="utf-8") as f:
                            f.write(text)
                        logging.info(
                            f"Texte du rush Gemini TTS {i} sauvegardé dans {rush_text_file}"
                        )

                # Générer l'audio TTS avec Gemini
                audio_files = generate_gemini_tts_audio(config, granularity)
                logging.info("Génération audio Gemini TTS terminée avec succès!")

                # Signal sonore à la fin du traitement
                play_completion_sound()

            except FileNotFoundError as e:
                logging.error(f"Erreur: {e}")
                sys.exit(1)
            except Exception as e:
                logging.error(f"Erreur lors de la génération audio Gemini TTS: {e}")
                sys.exit(1)

        # L'option --meta est maintenant traitée au début de main()

    except Exception as e:
        logging.error(f"Erreur lors de l'exécution du script: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
