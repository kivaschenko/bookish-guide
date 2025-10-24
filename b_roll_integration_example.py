#!/usr/bin/env python3
"""
B-roll Integration Example

This script demonstrates how to integrate the new b_roll package 
with the existing exponential_video.py workflow.
"""

import sys
import logging
from pathlib import Path

# Import the new B-roll package
from b_roll import MetaExtractor, VectorMatcher, BRollFinder, prepare_brolls_vector
from b_roll.cli import main as broll_cli_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def integrate_broll_with_exponential_video():
    """
    Example integration showing how to use B-roll package with existing workflow
    """
    print("🚀 B-roll Integration Example")
    print("=" * 50)
    
    # Step 1: Load configuration (same as exponential_video.py)
    try:
        import yaml
        with open("config.yml", "r") as f:
            config = yaml.safe_load(f)
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load config.yml: {e}")
        return False
    
    # Step 2: Extract metadata from B-roll library (first time setup)
    print("\n📋 Step 1: Extract B-roll metadata")
    try:
        extractor = MetaExtractor(config)
        total, success = extractor.process_all_videos()
        print(f"   📹 Processed: {total} videos, ✅ Success: {success}")
    except Exception as e:
        print(f"   ❌ Metadata extraction failed: {e}")
        return False
    
    # Step 3: Prepare vector embeddings and timing
    print("\n🔍 Step 2: Prepare B-roll selections")
    try:
        result_path = prepare_brolls_vector(config)
        if result_path:
            print(f"   ✅ B-roll timing generated: {result_path}")
        else:
            print("   ❌ Failed to generate B-roll timing")
            return False
    except Exception as e:
        print(f"   ❌ Vector preparation failed: {e}")
        return False
    
    # Step 4: Integration with exponential_video.py
    print("\n🎬 Step 3: Integration with video generation")
    print("   📝 The b_roll package is now ready to integrate with exponential_video.py")
    print("   📁 Generated files:")
    print(f"      - B-roll timing: {result_path}")
    print("      - Metadata: b_roll_library/metadata/*.json")
    print("      - Vector embeddings: broll_vector_embeddings.json")
    
    return True


def show_cli_usage():
    """Show CLI usage examples"""
    print("\n🔧 CLI Usage Examples")
    print("=" * 30)
    print("# Extract metadata from B-roll library:")
    print("python -m b_roll.cli extract-metadata")
    print()
    print("# Prepare vector embeddings and B-roll selections:")
    print("python -m b_roll.cli prepare-vectors")
    print()
    print("# Test B-roll selection quality:")
    print("python -m b_roll.cli test-selection --duration 15.0")
    print()
    print("# Clean B-roll selections:")
    print("python -m b_roll.cli clean-selections")
    print()
    print("# Analyze B-roll library statistics:")
    print("python -m b_roll.cli analyze-library --verbose")


def show_integration_points():
    """Show key integration points with exponential_video.py"""
    print("\n🔗 Integration Points with exponential_video.py")
    print("=" * 50)
    print("1. Replace existing B-roll logic:")
    print("   - Remove old vector matching code from exponential_video.py")
    print("   - Import: from b_roll import prepare_brolls_vector")
    print("   - Call: prepare_brolls_vector(config) instead of inline logic")
    print()
    print("2. Use generated timing files:")
    print("   - B-roll timing: script_and_voice/temp/broll_timing.json")
    print("   - Compatible with existing video editing pipeline")
    print()
    print("3. Metadata integration:")
    print("   - B-roll metadata stored in: b_roll_library/metadata/")
    print("   - Vector embeddings in: broll_vector_embeddings.json")
    print("   - Both used automatically by the B-roll package")
    print()
    print("4. Configuration:")
    print("   - Uses same config.yml as exponential_video.py")
    print("   - No additional configuration needed")


def main():
    """Main integration example"""
    print("🎯 StoryForge B-roll Package Integration")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("config.yml").exists():
        print("❌ Error: config.yml not found")
        print("   Please run this script from the StoryForge root directory")
        sys.exit(1)
    
    # Run integration example
    success = integrate_broll_with_exponential_video()
    
    if success:
        print("\n🎉 B-roll package integration successful!")
        show_cli_usage()
        show_integration_points()
        
        print("\n✨ Next Steps:")
        print("1. Update exponential_video.py to use the new B-roll package")
        print("2. Test the integration with a sample project")
        print("3. Use the CLI for daily B-roll management tasks")
        
    else:
        print("\n❌ Integration failed - please check the errors above")
        sys.exit(1)


if __name__ == "__main__":
    main()