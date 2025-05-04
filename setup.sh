#!/bin/bash
# Setup script for Universal Video Downloader

# Function to display colored messages
print_message() {
  local color=$1
  local message=$2
  
  # Colors
  local red='\033[0;31m'
  local green='\033[0;32m'
  local yellow='\033[1;33m'
  local blue='\033[0;34m'
  local nc='\033[0m' # No Color
  
  case $color in
    "red") echo -e "${red}${message}${nc}" ;;
    "green") echo -e "${green}${message}${nc}" ;;
    "yellow") echo -e "${yellow}${message}${nc}" ;;
    "blue") echo -e "${blue}${message}${nc}" ;;
    *) echo "$message" ;;
  esac
}

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Print welcome message
clear
print_message "blue" "=================================================="
print_message "blue" "      Universal Video Downloader Setup Script      "
print_message "blue" "=================================================="
print_message "green" "  No API keys or external services required!  "
print_message "blue" "=================================================="
echo ""

# Check Python installation
print_message "yellow" "Checking Python installation..."
if command_exists python3; then
  python_version=$(python3 --version)
  print_message "green" "✓ Python is installed: $python_version"
else
  print_message "red" "✗ Python 3 is not installed. Please install Python 3.10 or higher."
  exit 1
fi

# Check for FFmpeg
print_message "yellow" "Checking FFmpeg installation..."
if command_exists ffmpeg; then
  ffmpeg_version=$(ffmpeg -version | head -n 1)
  print_message "green" "✓ FFmpeg is installed: $ffmpeg_version"
else
  print_message "red" "✗ FFmpeg is not installed."
  echo "Please install FFmpeg before continuing:"
  echo "  - Ubuntu/Debian: sudo apt install ffmpeg"
  echo "  - macOS: brew install ffmpeg"
  echo "  - Windows: Download from https://ffmpeg.org/download.html"
  exit 1
fi

# Create virtual environment
print_message "yellow" "Setting up Python virtual environment..."
if [ -d "venv" ]; then
  print_message "yellow" "Virtual environment already exists. Skipping creation."
else
  python3 -m venv venv
  if [ $? -eq 0 ]; then
    print_message "green" "✓ Virtual environment created successfully."
  else
    print_message "red" "✗ Failed to create virtual environment."
    exit 1
  fi
fi

# Activate virtual environment
print_message "yellow" "Activating virtual environment..."
source venv/bin/activate
if [ $? -eq 0 ]; then
  print_message "green" "✓ Virtual environment activated."
else
  print_message "red" "✗ Failed to activate virtual environment."
  exit 1
fi

# Install Python dependencies
print_message "yellow" "Installing Python dependencies..."
pip install Flask flask-sqlalchemy gunicorn yt-dlp ffmpeg-python pytube youtube-transcript-api trafilatura
if [ $? -eq 0 ]; then
  print_message "green" "✓ Dependencies installed successfully."
else
  print_message "red" "✗ Failed to install dependencies."
  exit 1
fi

# Create downloads directory
print_message "yellow" "Creating downloads directory..."
mkdir -p static/downloads
if [ $? -eq 0 ]; then
  print_message "green" "✓ Downloads directory created."
else
  print_message "red" "✗ Failed to create downloads directory."
  exit 1
fi

# Run verification script
print_message "yellow" "Running verification script..."
python3 test_setup.py

# Final instructions
echo ""
print_message "blue" "=================================================="
print_message "blue" "            Setup completed successfully           "
print_message "blue" "=================================================="
echo ""
print_message "yellow" "To start the application:"
echo "1. Activate the virtual environment (if not already active):"
echo "   source venv/bin/activate"
echo ""
echo "2. Start the application:"
echo "   python main.py"
echo ""
echo "3. Open your browser and go to:"
echo "   http://localhost:5000"
echo ""
print_message "green" "For more information, see the USER_GUIDE.md file."
echo ""