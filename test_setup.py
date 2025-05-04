#!/usr/bin/env python3
"""
Test script for verifying the setup of Universal Video Downloader
This script verifies dependencies and system configurations are correct
"""

import os
import sys
import subprocess
import importlib
import platform

def print_header(text):
    """Print a header with decoration"""
    print("\n" + "=" * 70)
    print(f" {text} ".center(70, "="))
    print("=" * 70)

def check_python_version():
    """Check if Python version is sufficient"""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python version: {sys.version}")
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10 or higher is required")
        return False
    print("✅ Python version is compatible")
    return True

def check_ffmpeg():
    """Check if FFmpeg is installed and available"""
    print_header("Checking FFmpeg Installation")
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                               capture_output=True, 
                               text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ FFmpeg is installed: {version_line}")
            return True
        else:
            print("❌ FFmpeg is not installed or not working correctly.")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg not found in PATH.")
        if platform.system() == 'Windows':
            print("   Install FFmpeg and add it to your PATH.")
            print("   Download from: https://ffmpeg.org/download.html")
        elif platform.system() == 'Darwin':  # macOS
            print("   Install using: brew install ffmpeg")
        else:  # Linux
            print("   Install using: sudo apt install ffmpeg")
        return False

def check_python_packages():
    """Check if required Python packages are installed"""
    print_header("Checking Required Python Packages")
    
    required_packages = [
        'flask',
        'flask_sqlalchemy',
        'yt_dlp',
        'ffmpeg',
        'pytube',
        'youtube_transcript_api',
        'trafilatura',
    ]
    
    print("Note: No API keys or external services required!")
    
    all_installed = True
    
    for package in required_packages:
        try:
            # Try to import the package
            importlib.import_module(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is NOT installed")
            all_installed = False
    
    return all_installed

def check_download_directory():
    """Check if the downloads directory exists and is writable"""
    print_header("Checking Downloads Directory")
    
    download_dir = os.path.join("static", "downloads")
    
    # Check if directory exists
    if not os.path.exists(download_dir):
        print(f"❌ Directory {download_dir} does not exist")
        try:
            os.makedirs(download_dir)
            print(f"✅ Created directory {download_dir}")
        except Exception as e:
            print(f"❌ Failed to create directory: {e}")
            return False
    else:
        print(f"✅ Directory {download_dir} exists")
    
    # Check if directory is writable
    test_file = os.path.join(download_dir, "test_write.txt")
    try:
        with open(test_file, 'w') as f:
            f.write("Test write")
        os.remove(test_file)
        print(f"✅ Directory {download_dir} is writable")
        return True
    except Exception as e:
        print(f"❌ Directory {download_dir} is not writable: {e}")
        return False

def main():
    """Run all checks and report results"""
    print("\nUNIVERSAL VIDEO DOWNLOADER - SETUP TEST")
    print("This script will check if your system is properly configured.\n")
    
    python_ok = check_python_version()
    ffmpeg_ok = check_ffmpeg()
    packages_ok = check_python_packages()
    directory_ok = check_download_directory()
    
    print_header("SUMMARY")
    print(f"Python version: {'✅ OK' if python_ok else '❌ Not compatible'}")
    print(f"FFmpeg installation: {'✅ OK' if ffmpeg_ok else '❌ Not installed or not in PATH'}")
    print(f"Python packages: {'✅ All installed' if packages_ok else '❌ Some packages missing'}")
    print(f"Downloads directory: {'✅ OK' if directory_ok else '❌ Not writable'}")
    
    if python_ok and ffmpeg_ok and packages_ok and directory_ok:
        print("\n✅ All checks passed! Your system is ready to run the application.")
        print("   Start the application with: python main.py")
    else:
        print("\n❌ Some checks failed. Please fix the issues before running the application.")
        print("   See the INSTALL.md file for detailed installation instructions.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())