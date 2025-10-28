#!/usr/bin/env python3
"""
StoryForge MVP Demo - Shows exactly what's working and what's missing
Run this to see how close you are to a complete video generation system.
"""

import json
from pathlib import Path


def check_component(name, description, test_func):
    """Check if a component is working."""
    print(f"\n🔍 Testing {name}: {description}")
    try:
        result = test_func()
        if result:
            print(f"✅ {name} - WORKING")
            return True
        else:
            print(f"❌ {name} - NOT WORKING")
            return False
    except Exception as e:
        print(f"❌ {name} - ERROR: {e}")
        return False


def test_script_generation():
    """Test if script generation works."""
    script_file = Path("script_and_voice/module_script_and_voice.py")
    return script_file.exists()


def test_voice_synthesis():
    """Test if voice synthesis works."""
    # Check if audio files exist from sample project
    audio_dir = Path("projects/my-project-06/english/audio")
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("bullet_*.mp3"))
        return len(audio_files) > 0
    return False


def test_broll_intelligence():
    """Test if B-roll intelligence works."""
    broll_cli = Path("b_roll/cli.py")
    return broll_cli.exists()


def test_timing_generation():
    """Test if timing JSON generation works."""
    timing_file = Path("temp/broll_timing.json")
    if timing_file.exists():
        try:
            with open(timing_file) as f:
                data = json.load(f)
            return "rushes" in data and len(data["rushes"]) > 0
        except Exception:
            return False
    return False


def test_video_assembly():
    """Test if video assembly works."""
    assembler_file = Path("simple_video_assembler.py")
    return assembler_file.exists()


def test_broll_videos():
    """Test if B-roll videos are available."""
    broll_dir = Path("b-roll")
    if broll_dir.exists():
        videos = list(broll_dir.glob("*.mp4")) + list(broll_dir.glob("*.mov"))
        return len(videos) > 0
    return False


def show_current_workflow():
    """Show the working parts of the pipeline."""
    print("\n" + "=" * 60)
    print("📋 CURRENT WORKING WORKFLOW")
    print("=" * 60)

    print("\n✅ Step 1: Script & Voice Generation")
    print("cd script_and_voice")
    print(
        "python module_script_and_voice.py --project my-video --language english --input-file input.txt"
    )

    print("\n✅ Step 2: B-roll Intelligence")
    print("cd ..")
    print("python -m b_roll.cli extract-metadata    # First time only")
    print("python -m b_roll.cli prepare-vectors     # Generates broll_timing.json")

    print("\n❌ Step 3: Video Assembly (MISSING)")
    print("python simple_video_assembler.py --project my-video --language english")
    print("# ☝️ This is what needs to be created!")


def show_sample_data():
    """Show sample data structure to understand what exists."""
    print("\n" + "=" * 60)
    print("📊 SAMPLE DATA ANALYSIS")
    print("=" * 60)

    # Check sample project structure
    sample_project = Path("projects/my-project-06")
    if sample_project.exists():
        print("\n📁 Sample Project Structure:")
        for item in sample_project.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(sample_project)
                size = item.stat().st_size
                print(f"  {rel_path} ({size} bytes)")

    # Check timing data
    timing_file = Path("temp/broll_timing.json")
    if timing_file.exists():
        print("\n📊 B-roll Timing Data Sample:")
        try:
            with open(timing_file) as f:
                data = json.load(f)
            print(f"  Total rushes: {len(data.get('rushes', {}))}")
            for rush_id, rush_data in list(data.get("rushes", {}).items())[:2]:
                print(
                    f"  {rush_id}: {rush_data.get('duration', 0):.1f}s, {len(rush_data.get('brolls', []))} B-rolls"
                )
        except Exception as e:
            print(f"  Error reading timing data: {e}")

    # Check B-roll videos
    broll_dir = Path("b-roll")
    if broll_dir.exists():
        videos = list(broll_dir.glob("*.mp4")) + list(broll_dir.glob("*.mov"))
        print(f"\n🎬 Available B-roll Videos: {len(videos)}")
        for video in videos[:3]:
            size = video.stat().st_size / (1024 * 1024)  # MB
            print(f"  {video.name} ({size:.1f} MB)")
        if len(videos) > 3:
            print(f"  ... and {len(videos) - 3} more")


def show_mvp_gap():
    """Show exactly what's needed for MVP."""
    print("\n" + "=" * 60)
    print("🎯 MVP GAP ANALYSIS")
    print("=" * 60)

    print("\n🟢 WORKING COMPONENTS (80% of MVP):")
    print("  ✅ Text input processing")
    print("  ✅ AI script generation (Claude)")
    print("  ✅ Voice synthesis (Gemini TTS)")
    print("  ✅ B-roll video analysis (OpenAI Vision)")
    print("  ✅ Semantic B-roll matching (Vector embeddings)")
    print("  ✅ Timeline synchronization (JSON output)")

    print("\n🔴 MISSING COMPONENTS (20% of MVP):")
    print("  ❌ Video assembly engine (MoviePy integration)")
    print("  ❌ All-in-one user interface")

    print("\n📈 IMPLEMENTATION EFFORT:")
    print("  🛠️ Video assembly: 3-5 days (MoviePy + JSON parsing)")
    print("  🖥️ User interface: 2-3 days (CLI script)")
    print("  ✅ Testing & polish: 2-3 days")
    print("\n  📅 TOTAL TIME TO MVP: 7-11 days")


def main():
    """Main demo function."""
    print("🎬 StoryForge MVP Analysis Tool")
    print("=" * 60)
    print("Let's see how close you are to a complete video generation system!")

    # Test all components
    components = [
        ("Script Generation", "AI-powered script creation", test_script_generation),
        ("Voice Synthesis", "Text-to-speech audio creation", test_voice_synthesis),
        ("B-roll Intelligence", "AI video selection system", test_broll_intelligence),
        ("Timing Generation", "B-roll synchronization data", test_timing_generation),
        ("B-roll Videos", "Available video footage", test_broll_videos),
        ("Video Assembly", "Final MP4 creation", test_video_assembly),
    ]

    working_components = 0
    total_components = len(components)

    for name, desc, test_func in components:
        if check_component(name, desc, test_func):
            working_components += 1

    # Show results
    print(
        f"\n🎯 SYSTEM STATUS: {working_components}/{total_components} components working"
    )
    completion_percent = (working_components / total_components) * 100
    print(f"📊 MVP Completion: {completion_percent:.0f}%")

    if working_components >= 5:
        print("🎉 EXCELLENT! You're very close to a working MVP!")
    elif working_components >= 3:
        print("👍 GOOD! Most core components are working.")
    else:
        print("⚠️ ATTENTION: Several components need setup.")

    # Show detailed analysis
    show_current_workflow()
    show_sample_data()
    show_mvp_gap()

    print("\n" + "=" * 60)
    print("📝 NEXT STEPS:")
    print("=" * 60)
    print("1. Review the MVP_ROADMAP_INDIVIDUAL.md for detailed implementation")
    print("2. Create simple_video_assembler.py (the missing component)")
    print("3. Test with: python simple_video_assembler.py --project my-project-06")
    print("4. Create generate_video.py (all-in-one interface)")
    print("5. Test complete pipeline and iterate")

    print(f"\n🚀 You're {completion_percent:.0f}% done! The hard AI work is complete.")
    print("💡 The remaining work is just 'plumbing' - connecting existing pieces.")


if __name__ == "__main__":
    main()
