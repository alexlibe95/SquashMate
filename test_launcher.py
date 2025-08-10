#!/usr/bin/env python3
"""
Test script for the launcher wrapper
"""

import subprocess
import sys
from pathlib import Path

def test_launcher():
    """Test the launcher wrapper with a non-existent app."""
    launcher_path = Path.home() / ".local" / "bin" / "squashmate_launcher.py"
    
    if not launcher_path.exists():
        print("❌ Launcher wrapper not found")
        return False
    
    print("✅ Launcher wrapper found")
    
    # Test with non-existent app
    print("Testing with non-existent app...")
    result = subprocess.run([
        str(launcher_path), 
        "TestApp", 
        "/non/existent/path"
    ], capture_output=True, text=True)
    
    if result.returncode != 0:
        print("✅ Launcher correctly detected missing app")
        print(f"Error output: {result.stdout}")
    else:
        print("❌ Launcher should have failed for missing app")
        return False
    
    # Check if log was created
    log_file = Path.home() / ".local" / "share" / "squashmate" / "apps" / "TestApp.log"
    if log_file.exists():
        print("✅ Log file was created")
        with open(log_file, 'r') as f:
            content = f.read()
            if "FAILED" in content:
                print("✅ Error was logged correctly")
                print("Log content preview:")
                print(content[-200:])  # Last 200 chars
            else:
                print("❌ Error not logged properly")
                return False
    else:
        print("❌ Log file was not created")
        return False
    
    print("\n🎉 Launcher wrapper test passed!")
    return True

if __name__ == "__main__":
    if test_launcher():
        sys.exit(0)
    else:
        sys.exit(1)