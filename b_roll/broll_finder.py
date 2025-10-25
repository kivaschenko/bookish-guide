#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
B-roll Intelligence Module - Core B-roll Selection Engine

This module provides the main BRollFinder class that orchestrates
the entire B-roll selection process using vector similarity and AI ranking.
"""

import logging
import json
import math
from pathlib import Path
import traceback

from .vector_matcher import VectorMatcher
from .utils import (
    get_project_script_content,
    save_broll_timing_json,
    get_video_duration_estimate,
)


class BRollFinder:
    """
    Main class for intelligent B-roll selection.
    Coordinates vector matching, AI ranking, and timing synchronization.
    """

    def __init__(self, config):
        """
        Initialize the B-roll finder with configuration.

        Args:
            config (dict): Configuration loaded from config.yml
        """
        self.config = config
        self.temp_path = Path(config["paths"]["temp"])
        self.b_roll_path = Path(config["paths"]["b_roll"])

        # Editing parameters for b-rolls
        self.b_roll_seconds = config.get("editing", {}).get("b_roll_seconds", 4)
        self.b_roll_spacing = config.get("editing", {}).get("b_roll_spacing", 0.5)
        self.b_roll_start_delay = config.get("editing", {}).get(
            "b_roll_start_delay", 2.4
        )

        # Initialize vector matcher
        self.vector_matcher = VectorMatcher(
            config=config, broll_folder=str(self.b_roll_path)
        )

        # List of available b-rolls (MP4 and MOV)
        self.b_roll_files = list(self.b_roll_path.glob("*.mp4"))
        self.b_roll_files.extend(list(self.b_roll_path.glob("*.mov")))

        logging.info(
            f"BRollFinder initialized with {len(self.b_roll_files)} available b-rolls"
        )

    def calculate_needed_b_rolls(self, rush_duration):
        """
        Calculate the number of b-rolls needed for a given rush duration.

        Args:
            rush_duration (float): Duration of the rush in seconds

        Returns:
            int: Number of b-rolls needed
        """
        # Calculate available space for b-rolls (accounting for initial delay)
        available_space = rush_duration - self.b_roll_start_delay

        # If not enough space, no b-roll is needed
        if available_space <= 0:
            logging.info(f"Rush too short ({rush_duration}s) to add b-rolls")
            return 0

        # Calculate number of b-rolls that can fit in available space
        # Each b-roll occupies: b_roll_seconds + b_roll_spacing (except the last one)
        num_b_rolls = math.floor(
            available_space / (self.b_roll_seconds + self.b_roll_spacing)
        )

        # If we can add at least one b-roll
        if num_b_rolls >= 1:
            # We can add an additional b-roll because the last one doesn't need spacing
            # after it (it ends with the rush)
            space_without_last_spacing = available_space + self.b_roll_spacing
            num_b_rolls = math.floor(
                space_without_last_spacing / (self.b_roll_seconds + self.b_roll_spacing)
            )

        # Ensure at least one b-roll if space is sufficient
        if available_space >= self.b_roll_seconds and num_b_rolls == 0:
            num_b_rolls = 1

        logging.info(f"Rush duration: {rush_duration}s -> {num_b_rolls} b-rolls needed")
        return num_b_rolls

    def generate_broll_timing(
        self, rush_durations, selection_mode="vector", audio_mode="heygen"
    ):
        """
        Generate B-roll timing synchronization for all rushes.

        Args:
            rush_durations (list): List of rush durations in seconds
            selection_mode (str): Selection mode ('vector' for AI-powered selection)
            audio_mode (str): Audio generation mode ('heygen', 'openai_tts', 'gemini_tts')

        Returns:
            Path: Path to the generated timing JSON file
        """
        timing_data = {
            "rushes": {},
            "metadata": {
                "selection_mode": selection_mode,
                "audio_mode": audio_mode,
                "total_rushes": len(rush_durations),
                "b_roll_config": {
                    "duration": self.b_roll_seconds,
                    "spacing": self.b_roll_spacing,
                    "start_delay": self.b_roll_start_delay,
                },
            },
        }

        # Get script content for B-roll selection
        script_content = get_project_script_content(self.config)
        if not script_content:
            logging.warning("No script content found for B-roll selection")
            script_content = "Default content for B-roll selection"

        # Track globally used B-rolls to avoid repetition
        used_brolls_global = set()

        for i, duration in enumerate(rush_durations, 1):
            rush_id = f"rush{i}"
            logging.info(f"Processing {rush_id} (duration: {duration:.2f}s)")

            # Calculate timing for this rush
            num_brolls = self.calculate_needed_b_rolls(duration)

            if num_brolls == 0:
                timing_data["rushes"][rush_id] = {
                    "duration": duration,
                    "brolls": [],
                    "message": "Rush too short for B-roll placement",
                }
                continue

            # Select B-rolls using vector matching
            if selection_mode == "vector":
                broll_selections = self.vector_matcher.select_brolls_for_rush(
                    script_content, used_brolls_global_set=used_brolls_global
                )

                # Update globally used B-rolls
                for selection in broll_selections.values():
                    if selection.get("broll"):
                        used_brolls_global.add(selection["broll"])
            else:
                # Fallback: simple selection
                broll_selections = self._simple_broll_selection(
                    num_brolls, used_brolls_global
                )

            # Generate timing points
            broll_timings = self._calculate_broll_timings(
                duration, num_brolls, broll_selections
            )

            timing_data["rushes"][rush_id] = {
                "duration": duration,
                "brolls": broll_timings,
                "selection_method": selection_mode,
            }

        # Save timing data
        output_path = self.temp_path / "broll_timing.json"
        save_broll_timing_json(timing_data, output_path)

        return output_path

    def _calculate_broll_timings(self, rush_duration, num_brolls, broll_selections):
        """
        Calculate precise timing for B-roll placement within a rush.

        Args:
            rush_duration (float): Total duration of the rush
            num_brolls (int): Number of B-rolls to place
            broll_selections (dict): Selected B-roll filenames

        Returns:
            list: List of B-roll timing dictionaries
        """
        timings = []

        if num_brolls == 0:
            return timings

        # Calculate timing intervals
        start_time = self.b_roll_start_delay
        available_time = rush_duration - start_time

        if num_brolls == 1:
            # Single B-roll: place it optimally
            broll_start = start_time
        else:
            # Multiple B-rolls: distribute evenly
            interval = available_time / num_brolls

        for i in range(num_brolls):
            if num_brolls == 1:
                broll_start = start_time
            else:
                broll_start = start_time + (i * interval)

            broll_end = min(broll_start + self.b_roll_seconds, rush_duration)

            # Get selected B-roll filename
            selection_key = str(i + 1)
            broll_filename = None
            if selection_key in broll_selections:
                broll_filename = broll_selections[selection_key].get("broll")

            if not broll_filename and self.b_roll_files:
                # Fallback to first available B-roll
                broll_filename = self.b_roll_files[i % len(self.b_roll_files)].name

            timing = {
                "filename": broll_filename,
                "start_time": round(broll_start, 3),
                "end_time": round(broll_end, 3),
                "duration": round(broll_end - broll_start, 3),
                "position": i + 1,
            }

            # Add alternative B-rolls if available
            if selection_key in broll_selections:
                selection = broll_selections[selection_key]
                if selection.get("broll2"):
                    timing["alternative_1"] = selection["broll2"]
                if selection.get("broll3"):
                    timing["alternative_2"] = selection["broll3"]

            timings.append(timing)

        return timings

    def _simple_broll_selection(self, num_brolls, used_brolls_global):
        """
        Simple fallback B-roll selection method.

        Args:
            num_brolls (int): Number of B-rolls to select
            used_brolls_global (set): Set of already used B-roll filenames

        Returns:
            dict: Simple selection structure
        """
        selections = {}
        available_brolls = [
            f for f in self.b_roll_files if f.name not in used_brolls_global
        ]

        for i in range(num_brolls):
            if i < len(available_brolls):
                selections[str(i + 1)] = {"broll": available_brolls[i].name}
                used_brolls_global.add(available_brolls[i].name)

        return selections

    def test_broll_selection(self, test_duration=10.0):
        """
        Test B-roll selection quality for validation.

        Args:
            test_duration (float): Duration to test with

        Returns:
            Path: Path to the generated test results file
        """
        logging.info(f"Testing B-roll selection with {test_duration}s duration")

        try:
            # Generate test timing
            test_path = self.generate_broll_timing(
                [test_duration], selection_mode="vector"
            )

            # Load and validate results
            with open(test_path, "r", encoding="utf-8") as f:
                test_results = json.load(f)

            # Add quality metrics
            test_results["test_metadata"] = {
                "test_duration": test_duration,
                "brolls_selected": len(test_results["rushes"]["rush1"]["brolls"]),
                "selection_quality": "good"
                if test_results["rushes"]["rush1"]["brolls"]
                else "no_selection",
            }

            # Save enhanced test results
            test_output_path = self.temp_path / "broll_test_results.json"
            save_broll_timing_json(test_results, test_output_path)

            logging.info(f"B-roll selection test completed successfully")
            return test_output_path

        except Exception as e:
            logging.error(f"Error during B-roll selection test: {e}")
            logging.error(traceback.format_exc())
            return None


def prepare_brolls_vector(config=None):
    """
    Main function for preparing B-roll selections using vector matching.
    Compatible with Heygen (rush*.mp4) and TTS (bullet*.mp3) modes.
    Generates broll_timing.json for video editing integration.

    Args:
        config (dict): Configuration dictionary (loads from config.yml if None)

    Returns:
        Path: Path to generated timing file, or None if failed
    """
    import yaml

    # Clean up previous log files
    log_files = [
        "log-openai-ask_gpt_to_choose_best_broll.txt",
        "log-openai-ask_gpt_to_choose_best_broll.html",
    ]
    for log_file in log_files:
        if Path(log_file).exists():
            Path(log_file).unlink()
            logging.info(f"Removed previous log file: {log_file}")

    try:
        # Load configuration if not provided
        if config is None:
            try:
                with open("config.yml", "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
            except Exception as e:
                logging.error(f"Error loading config.yml: {e}")
                return None

        finder = BRollFinder(config)
        rush_durations = []

        # Detect audio mode (TTS or Heygen)
        audio_mode = config["audio"].get("generation_mode", "heygen")
        logging.info(f"Audio mode detected: {audio_mode}")

        if audio_mode in ["openai_tts", "gemini_tts"]:
            # TTS mode: read actual MP3 durations
            audio_dir = Path(config["paths"]["temp"]) / "audio"

            # Find all bullet*.mp3 files
            bullet_files = sorted(audio_dir.glob("bullet*.mp3"))

            if not bullet_files:
                logging.error(f"No bullet*.mp3 files found in {audio_dir}")
                logging.error(
                    "Generate TTS audio first before running B-roll selection"
                )
                return None

            # Read actual MP3 durations
            for bullet_file in bullet_files:
                try:
                    duration = get_video_duration_estimate(bullet_file)
                    rush_durations.append(duration)
                    logging.info(f"{bullet_file.name}: {duration:.3f}s")
                except Exception as e:
                    logging.error(f"Unable to read duration of {bullet_file}: {e}")
                    return None

        else:
            # Heygen mode: read MP4 videos
            heygen_path = Path(config["paths"]["heygen"])
            rush_videos = sorted(heygen_path.glob("rush*.mp4"))

            if not rush_videos:
                logging.error("No rush videos found in heygen folder")
                logging.error(
                    "Generate Heygen rushes first before running B-roll selection"
                )
                return None

            for video_path in rush_videos:
                duration = get_video_duration_estimate(video_path)
                rush_durations.append(duration)
                logging.info(f"Duration of {video_path.name}: {duration}s")

        if not rush_durations:
            logging.error("No rush durations found")
            return None

        # Generate B-roll timing
        result_path = finder.generate_broll_timing(
            rush_durations, selection_mode="vector", audio_mode=audio_mode
        )
        logging.info(
            f"Vector B-roll preparation completed, results saved in {result_path}"
        )

        return result_path

    except Exception as e:
        logging.error(f"Error during vector B-roll preparation: {e}")
        logging.error(traceback.format_exc())
        return None
