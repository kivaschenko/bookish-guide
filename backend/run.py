#!/usr/bin/env python3
"""
Startup script for the Premontage FastAPI server.
Provides easy server startup with configuration loading and validation.
"""

import sys
import logging
import argparse
from pathlib import Path

import uvicorn

from config.settings import (
    get_settings,
    ensure_directories_exist,
    validate_configuration,
)


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("premontage.log"),
        ],
    )


def validate_environment():
    """Validate the environment and configuration."""
    settings = get_settings()

    # Validate configuration
    issues = validate_configuration(settings)
    if issues:
        logging.error("Configuration validation failed:")
        for issue in issues:
            logging.error(f"  - {issue}")
        return False

    # Ensure directories exist
    try:
        ensure_directories_exist(settings)
        logging.info("All required directories are available")
    except Exception as e:
        logging.error(f"Failed to create required directories: {e}")
        return False

    return True


def check_broll_timing_file():
    """Check if broll_timing.json exists and warn if not."""
    settings = get_settings()
    broll_timing_file = Path(settings.paths.temp) / "broll_timing.json"

    if not broll_timing_file.exists():
        logging.warning(f"⚠️  broll_timing.json not found at {broll_timing_file}")
        logging.warning(
            "   The timeline API will not work until B-roll processing is completed."
        )
        logging.warning("   Run the B-roll processing first to generate this file.")
        return False
    else:
        logging.info(f"✅ Found broll_timing.json at {broll_timing_file}")
        return True


def print_startup_info():
    """Print startup information and access URLs."""
    settings = get_settings()

    print("\n" + "=" * 60)
    print("🎬 StoryForge Premontage FastAPI Server")
    print("=" * 60)
    print(f"🌐 Server URL: http://{settings.server.host}:{settings.server.port}")
    print(
        f"📚 API Documentation: http://{settings.server.host}:{settings.server.port}/docs"
    )
    print(f"📖 ReDoc: http://{settings.server.host}:{settings.server.port}/redoc")
    print(
        f"💚 Health Check: http://{settings.server.host}:{settings.server.port}/health"
    )

    if settings.authentication.enabled:
        print("🔒 Authentication: ENABLED")
        print(f"👤 Username: {settings.authentication.username}")
        print("ℹ️  Use these credentials for HTTP Basic Auth")
    else:
        print("🔓 Authentication: DISABLED")

    print(f"📁 Projects Path: {settings.paths.projects}")
    print(f"🎥 B-roll Path: {settings.paths.b_roll}")
    print(f"📂 Temp Path: {settings.paths.temp}")
    print("\n💡 Press Ctrl+C to stop the server")
    print("=" * 60 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Start the Premontage FastAPI server")
    parser.add_argument(
        "--host", default=None, help="Host to bind the server to (overrides config)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind the server to (overrides config)",
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--project", help="Specify the project name to update temp path"
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Set logging level",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate configuration and exit",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Update log level if specified
    if args.log_level:
        level = getattr(logging, args.log_level.upper())
        logging.getLogger().setLevel(level)

    # Update temp path for specific project if provided
    if args.project:
        from config.settings import update_temp_path_for_project

        update_temp_path_for_project(args.project)
        logging.info(f"Updated temp path for project: {args.project}")

    # Validate environment
    if not validate_environment():
        logging.error("Environment validation failed. Exiting.")
        sys.exit(1)

    # Check for broll_timing.json
    check_broll_timing_file()

    # If validation-only mode, exit here
    if args.validate_only:
        logging.info("Configuration validation completed successfully.")
        sys.exit(0)

    # Get settings
    settings = get_settings()

    # Override settings with command line arguments
    host = args.host or settings.server.host
    port = args.port or settings.server.port
    reload = args.reload or settings.server.reload

    # Print startup information
    print_startup_info()

    try:
        # Start the server
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=args.log_level,
            access_log=True,
        )
    except KeyboardInterrupt:
        logging.info("🛑 Server stopped by user")
    except Exception as e:
        logging.error(f"❌ Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
