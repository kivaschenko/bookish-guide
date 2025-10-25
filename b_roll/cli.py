#!/usr/bin/env python3
"""
B-roll Management CLI - Simple interface for B-roll operations
"""

import argparse
import sys
import logging
from pathlib import Path
import yaml

# Import B-roll modules
from .meta_extractor import MetaExtractor
from .broll_finder import BRollFinder, prepare_brolls_vector
from .utils import clean_broll_selections

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.yml"""
    config_path = Path(__file__).parent.parent / "config.yml"
    logger.info(f"Loading config from {config_path}")
    if not config_path.exists():
        logger.warning(f"Config file not found at {config_path}")
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def cmd_extract_metadata(args):
    """Extract metadata from all B-roll videos"""
    logger.info("Starting B-roll metadata extraction...")
    
    config = load_config()
    
    try:
        extractor = MetaExtractor(config)
        total, success = extractor.process_all_videos()
        
        errors = total - success
        
        logger.info(f"Processed {total} videos with {success} successes")
        if errors > 0:
            logger.warning(f"Encountered {errors} errors")
        
        print("✅ Metadata extraction complete!")
        print(f"📹 Processed: {total} videos")
        print(f"✅ Success: {success} videos")
        print(f"❌ Errors: {errors}")
        
    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}")
        print(f"❌ Failed to extract metadata: {e}")
        sys.exit(1)


def cmd_prepare_vectors(args):
    """Prepare vector embeddings for B-roll library"""
    logger.info("Preparing B-roll vector embeddings...")
    
    config = load_config()
    
    try:
        result_path = prepare_brolls_vector(config)
        
        if result_path:
            print("✅ Vector preparation complete!")
            print(f"� Results saved to: {result_path}")
        else:
            print("❌ Failed to prepare vector embeddings")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Vector preparation failed: {e}")
        print(f"❌ Failed to prepare vectors: {e}")
        sys.exit(1)


def cmd_clean_selections(args):
    """Clean B-roll selections"""
    logger.info("Cleaning B-roll selections...")
    
    config = load_config()
    
    try:
        result = clean_broll_selections(config)
        
        if result:
            print("✅ B-roll selections cleaned successfully")
        else:
            print("❌ Failed to clean B-roll selections")
    
    except Exception as e:
        logger.error(f"Cleaning failed: {e}")
        print(f"❌ Failed to clean selections: {e}")
        sys.exit(1)


def cmd_analyze_library(args):
    """Analyze B-roll library statistics"""
    logger.info("Analyzing B-roll library...")
    
    config = load_config()
    broll_library_path = Path(config.get('paths', {}).get('b_roll', 'b_roll_library'))
    
    if not broll_library_path.exists():
        print(f"❌ Error: B-roll library not found at {broll_library_path}")
        sys.exit(1)
    
    try:
        # Count video files
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
        video_files = []
        
        for ext in video_extensions:
            video_files.extend(broll_library_path.glob(f"**/*{ext}"))
        
        total_videos = len(video_files)
        
        # Check metadata
        metadata_dir = broll_library_path / "metadata"
        metadata_files = list(metadata_dir.glob("*.json")) if metadata_dir.exists() else []
        
        print("📊 B-roll Library Analysis")
        print("=" * 40)
        print(f"📁 Library Path: {broll_library_path}")
        print(f"📹 Total Videos: {total_videos}")
        print(f"📋 Metadata Files: {len(metadata_files)}")
        
        if total_videos > 0:
            coverage = len(metadata_files) / total_videos * 100
            print(f"📈 Coverage: {len(metadata_files)}/{total_videos} ({coverage:.1f}%)")
        
        if args.verbose:
            print("\n📝 Sample Metadata Files:")
            for i, meta_file in enumerate(metadata_files[:5]):
                print(f"  {i+1}. {meta_file.name}")
            
            if len(metadata_files) > 5:
                print(f"  ... and {len(metadata_files) - 5} more")
        
    except Exception as e:
        logger.error(f"Library analysis failed: {e}")
        print(f"❌ Failed to analyze library: {e}")
        sys.exit(1)


def cmd_test_selection(args):
    """Test B-roll selection system"""
    logger.info("Testing B-roll selection...")
    
    config = load_config()
    
    try:
        broll_finder = BRollFinder(config)
        
        # Simple test with default duration
        test_duration = args.duration if hasattr(args, 'duration') else 10.0
        result = broll_finder.test_broll_selection(test_duration)
        
        if result:
            print("✅ B-roll selection test complete!")
            print(f"📊 Test result: {result}")
        else:
            print("❌ B-roll selection test failed")
            
    except Exception as e:
        logger.error(f"B-roll selection test failed: {e}")
        print(f"❌ Failed to test selection: {e}")
        sys.exit(1)


def create_parser():
    """Create the argument parser"""
    parser = argparse.ArgumentParser(
        description="B-roll Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract metadata from all B-roll videos
  python -m b_roll.cli extract-metadata
  
  # Prepare vector embeddings
  python -m b_roll.cli prepare-vectors
  
  # Test B-roll selection system
  python -m b_roll.cli test-selection
  
  # Clean B-roll selections
  python -m b_roll.cli clean-selections
  
  # Analyze B-roll library
  python -m b_roll.cli analyze-library --verbose
        """
    )
    
    # Create subparsers
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Extract metadata command
    subparsers.add_parser(
        'extract-metadata',
        help='Extract metadata from all B-roll videos'
    )
    
    # Prepare vectors command
    subparsers.add_parser(
        'prepare-vectors', 
        help='Prepare vector embeddings for B-roll library'
    )
    
    # Test selection command
    test_parser = subparsers.add_parser(
        'test-selection',
        help='Test B-roll selection system'
    )
    test_parser.add_argument(
        '--duration',
        type=float,
        default=10.0,
        help='Test duration in seconds (default: 10.0)'
    )
    
    # Clean selections command
    subparsers.add_parser(
        'clean-selections',
        help='Clean B-roll selections'
    )
    
    # Analyze library command
    analyze_parser = subparsers.add_parser(
        'analyze-library',
        help='Analyze B-roll library statistics'
    )
    analyze_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information'
    )
    
    return parser


def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Command dispatch
    commands = {
        'extract-metadata': cmd_extract_metadata,
        'prepare-vectors': cmd_prepare_vectors,
        'test-selection': cmd_test_selection,
        'clean-selections': cmd_clean_selections,
        'analyze-library': cmd_analyze_library,
    }
    
    command_func = commands.get(args.command)
    if command_func:
        command_func(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()