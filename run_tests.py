#!/usr/bin/env python3
"""
Test runner script for media2vid unit tests.
"""
import sys
import subprocess
from pathlib import Path

def check_pytest_available():
    """Check if pytest is available."""
    try:
        import pytest
        return True
    except ImportError:
        return False

def install_pytest():
    """Install pytest and test dependencies."""
    print("Installing test dependencies...")
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', 
            '-r', 'tests/requirements.txt'
        ], check=True)
        return True
    except subprocess.CalledProcessError:
        print("Failed to install test dependencies")
        return False

def run_tests():
    """Run the test suite."""
    if not check_pytest_available():
        print("pytest not found. Attempting to install...")
        if not install_pytest():
            print("Cannot run tests without pytest")
            return 1
    
    print("Running test suite...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/', 
            '-v',  # Verbose output
            '--tb=short',  # Short traceback format
            '--cov=media2vid',  # Coverage report
            '--cov-report=term-missing'  # Show missing lines
        ], check=False)
        return result.returncode
    except FileNotFoundError:
        print("pytest command not found")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())