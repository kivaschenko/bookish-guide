#!/usr/bin/env python3
"""
Test Runner for script_and_voice module
Run all tests from the tests directory
"""

import subprocess
import sys
from pathlib import Path


def run_all_tests():
    """Run all test suites"""
    print("🧪 Running All Tests for script_and_voice Module")
    print("=" * 60)
    
    test_files = [
        "test_file_creation.py",
        "test_simple.py", 
        "demo_structure.py",
        "test_summary.py"
    ]
    
    results = []
    
    for test_file in test_files:
        print(f"\n📋 Running: {test_file}")
        print("-" * 40)
        
        try:
            if test_file == "demo_structure.py":
                # Demo is run directly
                result = subprocess.run([sys.executable, test_file], 
                                      cwd=Path(__file__).parent, 
                                      capture_output=True, text=True)
            elif test_file == "test_summary.py":
                # Summary runs its own tests
                result = subprocess.run([sys.executable, test_file], 
                                      cwd=Path(__file__).parent, 
                                      capture_output=True, text=True)
            else:
                # Unit tests
                result = subprocess.run([sys.executable, "-m", "unittest", test_file, "-v"], 
                                      cwd=Path(__file__).parent, 
                                      capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ PASSED: {test_file}")
                results.append((test_file, True))
            else:
                print(f"❌ FAILED: {test_file}")
                if result.stdout:
                    print("STDOUT:", result.stdout[-200:])  # Last 200 chars
                if result.stderr:
                    print("STDERR:", result.stderr[-200:])  # Last 200 chars
                results.append((test_file, False))
                
        except Exception as e:
            print(f"❌ ERROR running {test_file}: {e}")
            results.append((test_file, False))
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_file, success in results:
        emoji = "✅" if success else "❌"
        status = "PASSED" if success else "FAILED"
        print(f"{emoji} {test_file}: {status}")
    
    print(f"\n📈 Overall Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print("\n⚠️ Some tests failed. See details above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)