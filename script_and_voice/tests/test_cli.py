#!/usr/bin/env python3
"""
Final validation test - Test CLI argument handling
This test validates the script can properly handle command line arguments
"""

import subprocess
import sys
import tempfile
import shutil
from pathlib import Path


def test_cli_help():
    """Test that the script shows help without errors"""
    print("🔍 Testing CLI help command...")
    
    try:
        result = subprocess.run([
            sys.executable, "module_script_and_voice.py", "--help"
        ], cwd=Path(__file__).parent.parent, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Help command works correctly")
            print("📋 Available arguments:")
            # Extract argument information from help text
            help_lines = result.stdout.split('\n')
            for line in help_lines:
                if line.strip().startswith('--') or line.strip().startswith('-'):
                    print(f"   {line.strip()}")
            return True
        else:
            print("❌ Help command failed")
            print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Help command timed out")
        return False
    except Exception as e:
        print(f"❌ Error running help command: {e}")
        return False


def test_cli_validation():
    """Test CLI argument validation"""
    print("\n🔍 Testing CLI argument validation...")
    
    # Test missing required arguments
    try:
        result = subprocess.run([
            sys.executable, "module_script_and_voice.py"
        ], cwd=Path(__file__).parent.parent, capture_output=True, text=True, timeout=5)
        
        if result.returncode != 0 and "required" in result.stderr.lower():
            print("✅ Correctly rejects missing required arguments")
        else:
            print("❌ Should reject missing required arguments")
            return False
            
    except Exception as e:
        print(f"❌ Error testing argument validation: {e}")
        return False
    
    return True


def test_input_file_validation():
    """Test input file validation"""
    print("\n🔍 Testing input file validation...")
    
    # Create temporary directory for test
    temp_dir = tempfile.mkdtemp()
    try:
        fake_input = Path(temp_dir) / "nonexistent.txt"
        
        # Test with non-existent input file
        result = subprocess.run([
            sys.executable, "module_script_and_voice.py",
            "--project", "test-project",
            "--language", "english", 
            "--input-file", str(fake_input),
            "-s"
        ], cwd=Path(__file__).parent.parent, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0 and ("not found" in result.stderr.lower() or 
                                      "not found" in result.stdout.lower()):
            print("✅ Correctly validates input file existence")
            return True
        else:
            print("❌ Should validate input file existence")
            print(f"Stdout: {result.stdout}")
            print(f"Stderr: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing input file validation: {e}")
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def create_test_environment():
    """Create a test environment with proper input file"""
    temp_dir = tempfile.mkdtemp()
    input_file = Path(temp_dir) / "test_input.txt"
    
    with open(input_file, "w", encoding="utf-8") as f:
        f.write("This is a test input for the script validation.")
    
    return temp_dir, input_file


def test_argument_combinations():
    """Test different argument combinations"""
    print("\n🔍 Testing argument combinations...")
    
    temp_dir, input_file = create_test_environment()
    
    test_cases = [
        {
            "name": "Script-only flag",
            "args": ["--project", "test-proj", "--language", "english", 
                    "--input-file", str(input_file), "-s"],
            "should_pass": True
        },
        {
            "name": "Audio-only flag", 
            "args": ["--project", "test-proj", "--language", "english",
                    "--input-file", str(input_file), "-ag"],
            "should_pass": False  # Will fail because no script exists
        },
        {
            "name": "Invalid language",
            "args": ["--project", "test-proj", "--language", "klingon",
                    "--input-file", str(input_file), "-s"],
            "should_pass": False
        },
        {
            "name": "Both flags (should work)",
            "args": ["--project", "test-proj", "--language", "french",
                    "--input-file", str(input_file), "-s", "-ag"],
            "should_pass": True  # Only -s will be processed
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"  Testing: {test_case['name']}")
        
        try:
            result = subprocess.run([
                sys.executable, "module_script_and_voice.py"
            ] + test_case["args"], 
            cwd=Path(__file__).parent.parent, capture_output=True, text=True, timeout=15)
            
            if test_case["should_pass"]:
                if result.returncode == 0:
                    print(f"    ✅ PASSED - {test_case['name']}")
                    results.append(True)
                else:
                    print(f"    ❌ FAILED - {test_case['name']} (should have passed)")
                    print(f"    Error: {result.stderr}")
                    results.append(False)
            else:
                if result.returncode != 0:
                    print(f"    ✅ PASSED - {test_case['name']} (correctly failed)")
                    results.append(True)
                else:
                    print(f"    ❌ FAILED - {test_case['name']} (should have failed)")
                    results.append(False)
                    
        except subprocess.TimeoutExpired:
            print(f"    ⏰ TIMEOUT - {test_case['name']}")
            results.append(False)
        except Exception as e:
            print(f"    ❌ ERROR - {test_case['name']}: {e}")
            results.append(False)
    
    shutil.rmtree(temp_dir, ignore_errors=True)
    return all(results)


def main():
    """Main test execution"""
    print("🧪 CLI Argument Validation Test Suite")
    print("=" * 50)
    
    tests = [
        ("CLI Help", test_cli_help),
        ("Argument Validation", test_cli_validation), 
        ("Input File Validation", test_input_file_validation),
        ("Argument Combinations", test_argument_combinations)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 CLI TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        emoji = "✅" if result else "❌"
        status = "PASSED" if result else "FAILED"
        print(f"{emoji} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{total} CLI tests passed")
    
    if passed == total:
        print("\n🎉 ALL CLI TESTS PASSED!")
        print("✅ The script correctly handles command line arguments")
        print("✅ Argument validation is working properly")
        print("✅ Help system is functional")
        return True
    else:
        print("\n⚠️ Some CLI tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)