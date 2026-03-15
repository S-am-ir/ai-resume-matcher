"""
Anti-Berojgar - Test Runner
Run all tests with coverage reporting
"""
import subprocess
import sys
import os

def run_tests():
    """Run all unit tests."""
    print("=" * 60)
    print("Anti-Berojgar - Unit Test Suite")
    print("=" * 60)
    
    # Change to backend directory
    os.chdir(os.path.join(os.path.dirname(__file__), "backend"))
    
    # Run pytest with verbose output
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_unit.py",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback
        "-W", "ignore::DeprecationWarning"  # Ignore deprecation warnings
    ]
    
    print(f"\nRunning: {' '.join(cmd)}\n")
    print("-" * 60)
    
    result = subprocess.run(cmd)
    
    print("-" * 60)
    
    if result.returncode == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code: {result.returncode}")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
