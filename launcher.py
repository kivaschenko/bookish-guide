#!/usr/bin/env python3
"""
StoryForge Launcher - Simple interface for common operations
"""

import argparse
import subprocess
import sys


def run_editing_server():
    """Start the web editing interface."""
    print("🎬 Starting StoryForge Timeline Editor...")
    print("📍 Web interface will be available at: http://localhost:8080")
    print("📍 Press Ctrl+C to stop the server")

    subprocess.run([sys.executable, "editing_server/server.py"])


def generate_video(input_text, output_name, language="english"):
    """Generate a complete video."""
    print(f"🎬 Generating video: {output_name}")

    subprocess.run(
        [
            sys.executable,
            "generate_video.py",
            "--input",
            input_text,
            "--output",
            output_name,
            "--language",
            language,
        ]
    )


def run_script_voice(project, language, input_file):
    """Run script and voice generation only."""
    print(f"🎤 Generating script and voice for: {project}")

    subprocess.run(
        [
            sys.executable,
            "script_and_voice/module_script_and_voice.py",
            "--project",
            project,
            "--language",
            language,
            "--input-file",
            input_file,
        ]
    )


def main():
    parser = argparse.ArgumentParser(
        description="StoryForge Launcher - Simple operations interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  web                    Start web editing interface
  video                  Generate complete video
  script                 Generate script and voice only

Examples:
  python launcher.py web
  python launcher.py video --input "Your text..." --output "my-video"
  python launcher.py script --project my-project --input input.txt
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Web interface command
    subparsers.add_parser("web", help="Start web editing interface")

    # Video generation command
    video_parser = subparsers.add_parser("video", help="Generate complete video")
    video_parser.add_argument("--input", required=True, help="Input text content")
    video_parser.add_argument("--output", required=True, help="Output video name")
    video_parser.add_argument("--language", default="english", help="Language")

    # Script generation command
    script_parser = subparsers.add_parser(
        "script", help="Generate script and voice only"
    )
    script_parser.add_argument("--project", required=True, help="Project name")
    script_parser.add_argument("--input", required=True, help="Input file path")
    script_parser.add_argument("--language", default="english", help="Language")

    args = parser.parse_args()

    if args.command == "web":
        run_editing_server()
    elif args.command == "video":
        generate_video(args.input, args.output, args.language)
    elif args.command == "script":
        run_script_voice(args.project, args.language, args.input)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
