#!/usr/bin/env python3
"""
StoryForge Setup Script - Initialize the system for first use
"""

import os
import sys
from pathlib import Path
import subprocess


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def check_venv():
    """Check if virtual environment exists."""
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Virtual environment found")
        return True

    print("⚠️  Virtual environment not found")
    print("   Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create virtual environment")
        return False


def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")

    # Determine Python executable in venv
    if os.name == "nt":  # Windows
        pip_path = "venv/Scripts/pip"
    else:  # Unix/Linux/MacOS
        pip_path = "venv/bin/pip"

    try:
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False


def setup_config():
    """Setup configuration file."""
    config_example = Path("config.yml.example")
    config_file = Path("config.yml")

    if config_file.exists():
        print("✅ Configuration file already exists")
        return True

    if config_example.exists():
        print("📝 Creating configuration file from template...")
        try:
            content = config_example.read_text()
            config_file.write_text(content)
            print("✅ Configuration file created")
            print("   ⚠️  Please edit config.yml and add your API keys")
            return True
        except Exception as e:
            print(f"❌ Failed to create config file: {e}")
            return False
    else:
        print("❌ Configuration template not found")
        return False


def check_directories():
    """Check and create necessary directories."""
    dirs = ["projects", "temp", "b-roll"]

    for dir_name in dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir()
            print(f"📁 Created directory: {dir_name}")
        else:
            print(f"✅ Directory exists: {dir_name}")


def test_modules():
    """Test that core modules can be imported."""
    print("🧪 Testing module imports...")

    # Determine Python executable in venv
    if os.name == "nt":  # Windows
        python_path = "venv/Scripts/python"
    else:  # Unix/Linux/MacOS
        python_path = "venv/bin/python"

    tests = [
        ("Script & Voice", "import script_and_voice.module_script_and_voice"),
        ("B-roll Intelligence", "import b_roll.cli"),
        ("Utils", "import utils"),
    ]

    all_passed = True
    for test_name, import_code in tests:
        try:
            subprocess.run(
                [python_path, "-c", import_code],
                capture_output=True,
                text=True,
                check=True,
            )
            print(f"✅ {test_name} module")
        except subprocess.CalledProcessError as e:
            print(f"❌ {test_name} module: {e.stderr}")
            all_passed = False

    return all_passed


def main():
    """Main setup function."""
    print("🚀 StoryForge Setup")
    print("=" * 50)

    # Check Python version
    if not check_python_version():
        return False

    # Check/create virtual environment
    if not check_venv():
        return False

    # Install dependencies
    if not install_dependencies():
        return False

    # Setup configuration
    if not setup_config():
        return False

    # Check directories
    check_directories()

    # Test modules
    if not test_modules():
        print("\n⚠️  Some modules failed to import. Check the error messages above.")
        print("   This might be due to missing API keys in config.yml")

    print("\n" + "=" * 50)
    print("✅ Setup completed!")
    print("\nNext steps:")
    print("1. Edit config.yml and add your API keys")
    print("2. Add B-roll videos to the b-roll/ directory")
    print("3. Start creating videos!")
    print("\nQuick start:")
    print("   python editing_server/server.py               # Start web interface")
    print('   python generate_video.py --input "Your text" --output "my-video"')

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
