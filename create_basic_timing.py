#!/usr/bin/env python3
"""
Create basic B-roll timing for English audio files
"""

import json
import random
from pathlib import Path


def create_basic_timing(project_name, language="english"):
    """Create basic timing file for video assembly"""

    project_path = Path(f"projects/{project_name}")
    audio_path = project_path / language / "audio"
    timing_output = project_path / "temp" / "broll_timing.json"

    print(f"🎬 Creating basic timing for {project_name} ({language})")

    # Get available B-roll videos
    broll_videos = []
    broll_path = Path("b-roll")

    if broll_path.exists():
        for ext in ["*.mp4", "*.mov"]:
            broll_videos.extend(list(broll_path.glob(ext)))

    print(f"📹 Found {len(broll_videos)} B-roll videos")

    if not broll_videos:
        print("❌ No B-roll videos found in b-roll/ directory")
        return False

    # Get audio files
    audio_files = sorted(list(audio_path.glob("bullet_*.mp3")))
    print(f"🎵 Found {len(audio_files)} audio files")

    if not audio_files:
        print("❌ No audio files found")
        return False

    # Create basic timing data
    rushes = {}

    for audio_file in audio_files:
        audio_name = audio_file.name

        # Estimate duration (roughly 30 seconds per audio file)
        estimated_duration = 30.0

        # Create 2-3 segments per audio file
        segments = []

        # First segment (0 to mid)
        mid_point = estimated_duration / 2
        segments.append(
            {
                "rush": audio_name,
                "broll": random.choice(broll_videos).name,
                "start_time": 0.0,
                "end_time": mid_point,
                "phrase": f"First segment of {audio_name}",
                "phrase_id": "1",
                "word_count": 15,
                "selected_broll": "broll",
            }
        )

        # Second segment (mid to end)
        segments.append(
            {
                "rush": audio_name,
                "broll": random.choice(broll_videos).name,
                "start_time": mid_point,
                "end_time": estimated_duration,
                "phrase": f"Second segment of {audio_name}",
                "phrase_id": "2",
                "word_count": 15,
                "selected_broll": "broll",
            }
        )

        rushes[audio_name] = segments

    # Create the timing structure expected by the assembler
    timing_data = {"rushes": rushes}

    # Ensure temp directory exists
    timing_output.parent.mkdir(exist_ok=True)

    # Save timing file
    with open(timing_output, "w", encoding="utf-8") as f:
        json.dump(timing_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Basic timing created: {timing_output}")
    print(f"📊 Structure: {len(rushes)} audio files with timing segments")

    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python create_basic_timing.py <project_name> [language]")
        print("Example: python create_basic_timing.py my-project-06 english")
        sys.exit(1)

    project_name = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "english"

    if create_basic_timing(project_name, language):
        print(
            f"\n🎯 Next step: python simple_video_assembler.py --project {project_name} --language {language}"
        )
    else:
        print("❌ Failed to create timing file")
