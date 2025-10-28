#!/usr/bin/env python3
"""
Quick Video Generator - Bypass API issues and create videos from existing projects
For when Gemini TTS API is down but you want to test the video assembly pipeline
"""

import argparse
import json
import shutil
from pathlib import Path
import subprocess
import sys


def copy_working_project(source_project, target_project, language="english"):
    """Copy a working project structure to a new project name."""
    source_dir = Path(f"projects/{source_project}/{language}")
    target_dir = Path(f"projects/{target_project}/{language}")

    if not source_dir.exists():
        print(f"❌ Source project not found: {source_dir}")
        return False

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy all files
    for file_path in source_dir.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(source_dir)
            target_path = target_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, target_path)

    print(f"✅ Copied project structure from {source_project} to {target_project}")
    return True


def prepare_audio_files(project, language="english"):
    """Copy project audio files to temp directory for B-roll system."""
    project_audio_dir = Path(f"projects/{project}/{language}/audio")
    temp_audio_dir = Path("temp/audio")

    if not project_audio_dir.exists():
        print(f"❌ Project audio directory not found: {project_audio_dir}")
        return False

    # Create temp audio directory
    temp_audio_dir.mkdir(parents=True, exist_ok=True)

    # Copy bullet*.mp3 files
    bullet_files = list(project_audio_dir.glob("bullet*.mp3"))
    if not bullet_files:
        print(f"❌ No bullet*.mp3 files found in {project_audio_dir}")
        return False

    for bullet_file in bullet_files:
        shutil.copy2(bullet_file, temp_audio_dir / bullet_file.name)

    print(f"✅ Copied {len(bullet_files)} audio files to temp directory")
    return True


def create_working_broll_timing(num_audio_files=6):
    """Create a working B-roll timing file with realistic data."""
    # List available B-roll videos
    broll_dir = Path("b-roll")
    broll_videos = [f.name for f in broll_dir.glob("*.mp4")]

    if not broll_videos:
        print("❌ No B-roll videos found")
        return False

    timing_data = {"rushes": {}}

    # Assume each audio file is 20-30 seconds
    durations = [25.0, 24.0, 22.0, 23.0, 24.0, 25.0, 26.0, 23.0, 22.0, 24.0]

    for i in range(1, num_audio_files + 1):
        rush_name = f"rush{i}"
        duration = durations[i - 1] if i <= len(durations) else 22.0

        # Add B-roll clip
        brolls = []
        if broll_videos:
            video_file = broll_videos[(i - 1) % len(broll_videos)]
            brolls.append(
                {
                    "video": video_file,
                    "start": 2.0,
                    "duration": min(5.0, duration - 4.0),
                    "score": 0.8,
                }
            )

        timing_data["rushes"][rush_name] = {
            "duration": duration,
            "brolls": brolls,
            "message": f"Rush {i} with {len(brolls)} B-roll clips",
        }

    # Save timing file
    with open("temp/broll_timing.json", "w") as f:
        json.dump(timing_data, f, indent=2)

    print(f"✅ Created B-roll timing file for {num_audio_files} audio segments")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Quick Video Generator - Bypass API issues"
    )
    parser.add_argument(
        "--source", default="my-project-06", help="Source project to copy from"
    )
    parser.add_argument("--output", required=True, help="Output video name")
    parser.add_argument("--language", default="english", help="Language")

    args = parser.parse_args()

    print("🎬 Quick Video Generator")
    print("=" * 40)
    print("📌 Bypassing API issues by reusing existing project structure")

    # Step 1: Copy working project structure
    if not copy_working_project(args.source, args.output, args.language):
        sys.exit(1)

    # Step 2: Prepare audio files
    if not prepare_audio_files(args.output, args.language):
        sys.exit(1)

    # Step 3: Count audio files and create timing
    temp_audio_dir = Path("temp/audio")
    bullet_files = list(temp_audio_dir.glob("bullet*.mp3"))
    num_audio = len(bullet_files)

    if not create_working_broll_timing(num_audio):
        sys.exit(1)

    # Step 4: Run video assembler
    print(f"🔄 Creating final video...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "simple_video_assembler.py",
                "--project",
                args.output,
                "--language",
                args.language,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        output_video = f"{args.output}_final.mp4"
        if Path(output_video).exists():
            size_mb = Path(output_video).stat().st_size / (1024 * 1024)
            print(f"🎉 SUCCESS! Video created:")
            print(f"  📁 File: {output_video}")
            print(f"  📊 Size: {size_mb:.1f} MB")
        else:
            print("❌ Video file was not created")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"❌ Video assembly failed: {e}")
        if e.stdout:
            print("Output:", e.stdout)
        if e.stderr:
            print("Error:", e.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
