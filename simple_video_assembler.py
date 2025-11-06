#!/usr/bin/env python3
"""
Simple Video Assembler - The Missing MVP Component
Combines audio + B-roll into final MP4 using existing JSON timing data.
"""

import json
from pathlib import Path
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
)
import logging
import yaml


def create_video_from_project(project_name, language="english", output_path=None):
    """
    Main function that creates final video from existing components.

    Args:
        project_name (str): Project name (e.g., "my-project-06")
        language (str): Language (e.g., "english")
        output_path (str): Output file path (default: project_name.mp4)

    Returns:
        str: Path to created video file
    """
    # 1. Load config for audio settings
    config_path = Path("config.yml")
    voice_volume = 1.3  # Default value
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
                voice_volume = config.get("audio", {}).get("voice_volume", 1.3)
        except Exception as e:
            logging.warning(f"Could not load config: {e}")

    logging.info(f"Using voice volume multiplier: {voice_volume}")

    # 2. Load timing data
    timing_file = Path("temp/broll_timing.json")
    # TODO: Adjust path if needed based on project structure, e.g., temp/{project_name}/broll_timing.json
    if not timing_file.exists():
        raise FileNotFoundError(
            "broll_timing.json not found. Run B-roll selection first."
        )

    with open(timing_file) as f:
        timing_data = json.load(f)

    # 2. Load audio files
    audio_dir = Path(f"projects/{project_name}/{language}/audio")
    audio_files = sorted(audio_dir.glob("bullet_*.mp3"))

    if not audio_files:
        raise FileNotFoundError(f"No audio files found in {audio_dir}")

    # 3. Create video timeline
    video_clips = []
    audio_clips = []
    current_time = 0

    for rush_id, rush_data in timing_data["rushes"].items():
        rush_duration = rush_data["duration"]
        brolls = rush_data.get("brolls", [])

        # Add audio clip with volume boost
        audio_file = audio_files[int(rush_id.replace("rush", "")) - 1]
        audio_clip = AudioFileClip(str(audio_file))
        # Apply volume boost from config
        if voice_volume != 1.0:
            audio_clip = audio_clip.with_volume_scaled(voice_volume)
        audio_clips.append(audio_clip.with_start(current_time))

        # Add B-roll clips for this rush
        for broll in brolls:
            broll_path = Path("b-roll") / broll["video"]
            if broll_path.exists():
                # TODO: Check size/dimensions if needed, resize if necessary
                video_clip = VideoFileClip(str(broll_path))
                # Trim to specified duration and set timing
                video_clip = video_clip.subclipped(
                    0, min(broll["duration"], video_clip.duration)
                )
                video_clip = video_clip.with_start(current_time + broll["start"])
                video_clips.append(video_clip)

        current_time += rush_duration

    # 4. Combine everything
    if not video_clips:
        raise ValueError("No B-roll clips found to create video")

    final_video = CompositeVideoClip(video_clips)
    final_audio = CompositeAudioClip(audio_clips)
    final_video = final_video.with_audio(final_audio)

    # 5. Export final video
    if output_path is None:
        output_path = f"{project_name}_final.mp4"

    logging.info(f"Exporting final video to {output_path}...")
    final_video.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac")

    # 6. Cleanup
    final_video.close()
    for clip in video_clips + audio_clips:
        clip.close()

    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create final video from project components"
    )
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--language", default="english", help="Language")
    parser.add_argument("--output", help="Output file path")

    args = parser.parse_args()

    try:
        output_file = create_video_from_project(
            args.project, args.language, args.output
        )
        print(f"✅ Video created successfully: {output_file}")
    except Exception as e:
        print(f"❌ Error: {e}")
