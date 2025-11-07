#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility functions for the B-roll Intelligence Module
"""

import logging
import json
from pathlib import Path


def clean_broll_selections(config):
    """
    Clean B-roll selection files by removing references to missing video files

    Args:
        config (dict): Configuration dictionary

    Returns:
        bool: True if cleaning was successful, False otherwise
    """
    try:
        temp_path = Path(config["paths"]["temp"])
        broll_file = temp_path / "broll_selections.json"

        if not broll_file.exists():
            logging.error("Fichier broll_selections.json non trouvé")
            return False

        with open(broll_file, "r") as f:
            data = json.load(f)

        b_roll_path = Path(config["paths"]["b_roll"])
        cleaned_data = {}

        for rush_id, rush_data in data.items():
            if "brolls" in rush_data:
                valid_brolls = []
                for broll in rush_data["brolls"]:
                    broll_path = b_roll_path / broll["filename"]
                    if broll_path.exists():
                        valid_brolls.append(broll)
                    else:
                        logging.warning(
                            f"B-roll manquante supprimée: {broll['filename']}"
                        )

                rush_data["brolls"] = valid_brolls
                cleaned_data[rush_id] = rush_data

        # Save cleaned data
        with open(broll_file, "w") as f:
            json.dump(cleaned_data, f, indent=2)

        logging.info("Nettoyage des sélections de b-rolls terminé")
        return True

    except Exception as e:
        logging.error(f"Erreur lors du nettoyage: {e}")
        return False


def get_video_duration_estimate(video_path):
    """
    Get the actual duration for a video or audio file

    Args:
        video_path (Path): Path to the video or audio file

    Returns:
        float: Actual duration in seconds
    """
    try:
        from moviepy import VideoFileClip, AudioFileClip
        import logging

        video_path = Path(video_path)
        file_extension = video_path.suffix.lower()

        # Try to get actual duration using moviepy
        if file_extension in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
            # Video file
            with VideoFileClip(str(video_path)) as clip:
                duration = clip.duration
                logging.debug(f"Video duration for {video_path.name}: {duration:.3f}s")
                return duration
        elif file_extension in [".mp3", ".wav", ".m4a", ".ogg"]:
            # Audio file
            with AudioFileClip(str(video_path)) as clip:
                duration = clip.duration
                logging.debug(f"Audio duration for {video_path.name}: {duration:.3f}s")
                return duration
        else:
            # Unknown format, fall back to file size estimation
            logging.warning(
                f"Unknown file format {file_extension}, using size estimation"
            )
            file_size = video_path.stat().st_size
            # Rough estimate: 1MB per second for typical video quality
            estimated_duration = file_size / (1024 * 1024)
            return max(1.0, estimated_duration)  # Minimum 1 second

    except Exception as e:
        logging.warning(f"Could not get duration for {video_path}: {e}")
        # Fallback: try simple file size estimation
        try:
            file_size = video_path.stat().st_size
            estimated_duration = file_size / (1024 * 1024)
            return max(1.0, estimated_duration)  # Minimum 1 second
        except Exception:
            return 10.0  # Default fallback


def ensure_directory_exists(path):
    """
    Ensure a directory exists, create it if it doesn't

    Args:
        path (Path or str): Directory path to create
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def count_broll_files(broll_path):
    """
    Count the number of B-roll video files and description files

    Args:
        broll_path (Path): Path to B-roll directory

    Returns:
        tuple: (video_count, description_count)
    """
    video_extensions = [".mp4", ".mov"]
    video_files = []
    for ext in video_extensions:
        video_files.extend(list(broll_path.glob(f"*{ext}")))

    txt_files = list(broll_path.glob("*.txt"))

    return len(video_files), len(txt_files)


def validate_config(config):
    """
    Validate the configuration for B-roll processing

    Args:
        config (dict): Configuration dictionary

    Returns:
        list: List of validation errors (empty if valid)
    """
    errors = []

    # Check required API configuration
    if "api" not in config:
        errors.append("Missing 'api' section in configuration")
    elif "openai" not in config["api"]:
        errors.append("Missing 'api.openai' section in configuration")
    elif "api_key" not in config["api"]["openai"]:
        errors.append("Missing 'api.openai.api_key' in configuration")

    # Check required paths
    required_paths = ["b_roll", "temp"]
    if "paths" not in config:
        errors.append("Missing 'paths' section in configuration")
    else:
        for path_key in required_paths:
            if path_key not in config["paths"]:
                errors.append(f"Missing 'paths.{path_key}' in configuration")

    return errors


def get_project_script_content(config):
    """
    Load script content for B-roll selection

    Args:
        config (dict): Configuration dictionary

    Returns:
        str: Script content or None if not found
    """
    try:
        # Try to load from full_script.json first
        temp_path = Path(config["paths"]["temp"])
        script_file = temp_path / "full_script.json"

        if script_file.exists():
            with open(script_file, "r", encoding="utf-8") as f:
                script_data = json.load(f)
                if "bullets" in script_data:
                    # Combine all bullet text
                    return " ".join(
                        [bullet.get("text", "") for bullet in script_data["bullets"]]
                    )

        # Fallback to ori_vid.txt
        ori_vid_path = config.get("paths", {}).get("project_ori_vid")
        if ori_vid_path and Path(ori_vid_path).exists():
            with open(ori_vid_path, "r", encoding="utf-8") as f:
                return f.read().strip()

        return None

    except Exception as e:
        logging.error(f"Error loading script content: {e}")
        return None


def save_broll_timing_json(timing_data, output_path):
    """
    Save B-roll timing data to JSON file

    Args:
        timing_data (dict): Timing data structure
        output_path (Path): Output file path
    """
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(timing_data, f, indent=2, ensure_ascii=False)
        logging.info(f"B-roll timing data saved to {output_path}")
    except Exception as e:
        logging.error(f"Error saving timing data: {e}")
        raise
