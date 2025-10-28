#!/usr/bin/env python3
"""
StoryForge - One-Command Video Generator
Complete MVP: Input text → Final video in one command

Usage:
    python generate_video.py --input "Your content..." --output "video-name"
"""

import argparse
import subprocess
import sys
import logging
from pathlib import Path
import tempfile

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_requirements():
    """Check if all required components are available."""
    checks = []

    # Check script_and_voice module
    script_module = Path("script_and_voice/module_script_and_voice.py")
    checks.append(("Script & Voice module", script_module.exists()))

    # Check b_roll module
    broll_module = Path("b_roll/cli.py")
    checks.append(("B-roll Intelligence module", broll_module.exists()))

    # Check video assembler
    assembler = Path("simple_video_assembler.py")
    checks.append(("Video Assembler", assembler.exists()))

    # Check B-roll directory
    broll_dir = Path("b-roll")
    has_videos = False
    if broll_dir.exists():
        videos = list(broll_dir.glob("*.mp4")) + list(broll_dir.glob("*.mov"))
        has_videos = len(videos) > 0
    checks.append(("B-roll videos available", has_videos))

    # Print status
    print("🔍 System Requirements Check:")
    all_good = True
    for name, status in checks:
        symbol = "✅" if status else "❌"
        print(f"  {symbol} {name}")
        if not status:
            all_good = False

    if not all_good:
        print("\n❌ Some requirements are missing. Please check the setup.")
        return False

    print("\n✅ All requirements satisfied!")
    return True


def run_command(cmd, description, check_output=True):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    logger.info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, check=True, capture_output=True, text=True, cwd=Path.cwd()
        )

        if check_output and result.stdout:
            # Show relevant output lines
            lines = result.stdout.strip().split("\n")
            for line in lines[-3:]:  # Show last 3 lines
                if line.strip():
                    print(f"  📋 {line}")

        print(f"✅ {description} completed")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        if e.stderr:
            print(f"  Error: {e.stderr}")
        if e.stdout:
            print(f"  Output: {e.stdout}")
        return False


def generate_complete_video(input_text, output_name, language="english"):
    """
    Complete video generation pipeline.

    Args:
        input_text (str): Text content for the video
        output_name (str): Name for the project and output file
        language (str): Language for generation

    Returns:
        str: Path to final video file, or None if failed
    """
    # Create temp directory for input
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)

    # Step 1: Save input text
    input_file = temp_dir / "input.txt"
    with open(input_file, "w", encoding="utf-8") as f:
        f.write(input_text)

    # Step 2: Generate script and voice
    cmd = [
        sys.executable,
        "script_and_voice/module_script_and_voice.py",
        "--project",
        output_name,
        "--language",
        language,
        "--input-file",
        str(input_file),
    ]

    if not run_command(cmd, "Step 1/4: Generating script and voice"):
        return None

    # Step 2: Copy audio files to temp directory (B-roll system expects them there)
    project_audio_dir = Path(f"projects/{output_name}/{language}/audio")
    temp_audio_dir = Path("temp/audio")

    if project_audio_dir.exists():
        import shutil

        # Create temp audio directory
        temp_audio_dir.mkdir(parents=True, exist_ok=True)

        # Copy all bullet*.mp3 files
        bullet_files = list(project_audio_dir.glob("bullet*.mp3"))
        if bullet_files:
            for bullet_file in bullet_files:
                shutil.copy2(bullet_file, temp_audio_dir / bullet_file.name)
            print(f"  📄 Copied {len(bullet_files)} audio files to temp directory")
        else:
            print("  ⚠️ No bullet*.mp3 files found in project audio directory")
    else:
        print(f"  ⚠️ Project audio directory not found: {project_audio_dir}")

    # Step 3: Extract B-roll metadata (first time setup)
    cmd = [sys.executable, "-m", "b_roll.cli", "extract-metadata"]
    run_command(
        cmd,
        "Step 3/5: Extracting B-roll metadata (may skip if already done)",
        check_output=False,
    )

    # Step 4: Select B-roll footage
    cmd = [sys.executable, "-m", "b_roll.cli", "prepare-vectors"]
    if not run_command(cmd, "Step 4/5: Selecting B-roll footage"):
        return None

    # Step 5: Create final video
    output_video = f"{output_name}.mp4"
    cmd = [
        sys.executable,
        "simple_video_assembler.py",
        "--project",
        output_name,
        "--language",
        language,
        "--output",
        output_video,
    ]

    if not run_command(cmd, "Step 5/5: Creating final video"):
        return None

    return output_video


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="StoryForge - Generate complete videos from text",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_video.py --input "Today I'll share 3 investing tips..." --output "investing-tips"
  python generate_video.py --input "$(cat my_script.txt)" --output "my-video" --language french
        """,
    )

    parser.add_argument("--input", help="Input text content for the video")
    parser.add_argument("--output", help="Output video name (without .mp4)")
    parser.add_argument(
        "--language",
        default="english",
        help="Language (english, french, german, spanish, etc.)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check requirements, don't generate video",
    )

    args = parser.parse_args()

    print("🎬 StoryForge - AI Video Generator")
    print("=" * 50)

    # Check requirements
    if not check_requirements():
        sys.exit(1)

    if args.check:
        print("\n✅ System check passed! Ready to generate videos.")
        return

    # Validate inputs (only when not checking)
    if not args.input or not args.input.strip():
        print("❌ Error: --input is required when generating videos")
        sys.exit(1)

    if not args.output or not args.output.strip():
        print("❌ Error: --output is required when generating videos")
        sys.exit(1)

    # Show what we're about to do
    print(f"\n📋 Generation Plan:")
    print(f"  📝 Input: {len(args.input)} characters")
    print(f"  🎯 Output: {args.output}.mp4")
    print(f"  🌍 Language: {args.language}")

    # Generate video
    print(f"\n🚀 Starting video generation for '{args.output}'...")
    print("⏱️ Expected time: 2-8 minutes (depending on content length)")

    result = generate_complete_video(args.input, args.output, args.language)

    if result:
        # Check if file actually exists and get size
        output_path = Path(result)
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"\n🎉 SUCCESS! Your video is ready:")
            print(f"  📁 File: {result}")
            print(f"  📊 Size: {size_mb:.1f} MB")
            print(f"  📺 Ready to upload to YouTube, TikTok, or any platform!")

            # Additional tips
            print(f"\n💡 Next steps:")
            print(f"  1. Preview your video: Open {result} in your video player")
            print(f"  2. Upload to social media platforms")
            print(f"  3. Create more videos with different content!")
        else:
            print(f"❌ Error: Video file {result} was not created")
            sys.exit(1)
    else:
        print("❌ Video generation failed. Check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
