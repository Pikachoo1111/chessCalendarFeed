#!/usr/bin/env python3
"""
Setup script for Chess Tournament Calendar Feed
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"[RUNNING] {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"[SUCCESS] {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def main():
    """Main setup function."""
    print("[SETUP] Setting up Chess Tournament Calendar Feed")
    print("=" * 50)

    # Check Python version
    if sys.version_info < (3, 8):
        print("[ERROR] Python 3.8 or higher is required")
        sys.exit(1)

    print(f"[SUCCESS] Python {sys.version.split()[0]} detected")
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        sys.exit(1)
    
    # Run tests
    if not run_command("python -m pytest test_calendar.py -v", "Running tests"):
        print("[WARNING] Tests failed, but continuing setup...")

    # Generate initial calendar
    if not run_command("python generate_calendar.py", "Generating initial calendar"):
        print("[WARNING] Initial calendar generation failed")
    else:
        if os.path.exists("calendar.ics"):
            print("[SUCCESS] Calendar generated with events!")

    print("\n[COMPLETE] Setup completed!")
    print("\nNext steps:")
    print("1. Push this repository to GitHub")
    print("2. Enable GitHub Pages in repository settings")
    print("3. Your calendar feed will be available at:")
    print("   https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/calendar.ics")
    print("4. Subscribe to this URL in Apple Calendar")

    print("\nCommands:")
    print("• Generate calendar: python generate_calendar.py")
    print("• Run tests: python -m pytest test_calendar.py -v")
    print("• View calendar: cat calendar.ics")

if __name__ == "__main__":
    main()
