#!/usr/bin/env python3
"""
Create basic B-roll timing for English audio files in the format expected by simple_video_assembler.py
"""

import json
import random
from pathlib import Path


def create_assembler_timing(project_name, language="english"):
    """Create timing file compatible with simple_video_assembler.py"""

    project_path = Path(f"projects/{project_name}")
    audio_path = project_path / language / "audio"
    timing_output = project_path / "temp" / "broll_timing.json"

    print(f"🎬 Creating assembler-compatible timing for {project_name} ({language})")

    # Get available B-roll videos from b-roll/ directory (with hyphen)
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

    # Create timing data in format expected by video assembler
    rushes = {}

    for i, audio_file in enumerate(audio_files):
        rush_id = f"rush{i + 1}"

        # Estimate duration (roughly 30 seconds per audio file)
        estimated_duration = 30.0

        # Create B-roll segments for this rush
        brolls = []

        # First B-roll segment (0 to mid)
        mid_point = estimated_duration / 2
        brolls.append(
            {
                "video": random.choice(broll_videos).name,
                "start": 0.0,
                "duration": mid_point,
            }
        )

        # Second B-roll segment (mid to end)
        brolls.append(
            {
                "video": random.choice(broll_videos).name,
                "start": mid_point,
                "duration": estimated_duration - mid_point,
            }
        )

        rushes[rush_id] = {
            "duration": estimated_duration,
            "brolls": brolls,
            "audio_file": audio_file.name,
        }

    # Create the timing structure expected by the assembler
    timing_data = {"rushes": rushes}

    # Ensure temp directory exists
    timing_output.parent.mkdir(exist_ok=True)

    # Save timing file
    with open(timing_output, "w", encoding="utf-8") as f:
        json.dump(timing_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Assembler-compatible timing created: {timing_output}")
    print(f"📊 Structure: {len(rushes)} rushes with B-roll segments")

    # Display summary
    for rush_id, rush_data in rushes.items():
        print(
            f"  🎵 {rush_id}: {rush_data['audio_file']} ({rush_data['duration']}s, {len(rush_data['brolls'])} B-roll clips)"
        )

    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python create_assembler_timing.py <project_name> [language]")
        print("Example: python create_assembler_timing.py my-project-06 english")
        sys.exit(1)

    project_name = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "english"

    if create_assembler_timing(project_name, language):
        print(
            f"\n🎯 Next step: python simple_video_assembler.py --project {project_name} --language {language}"
        )
    else:
        print("❌ Failed to create timing file")
