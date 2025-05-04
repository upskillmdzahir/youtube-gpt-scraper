# Installation Guide

This document provides instructions for setting up the Universal Video Downloader application.

> **Important:** Unlike many video processing applications, this one requires **NO API keys** or external paid services. Everything runs locally without external dependencies beyond the open-source tools installed below.

## System Requirements

- Python 3.10 or higher
- FFmpeg installed on your system

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd video-downloader
```

### 2. Create a Virtual Environment

```bash
# On Linux/macOS
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Required Packages

The following packages are needed:

- Flask
- flask-sqlalchemy 
- gunicorn
- yt-dlp
- ffmpeg-python
- pytube
- youtube-transcript-api
- trafilatura

You can install them with pip:

```bash
pip install Flask flask-sqlalchemy gunicorn yt-dlp ffmpeg-python pytube youtube-transcript-api trafilatura
```

### 4. Install FFmpeg

FFmpeg is required for video processing.

#### On Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg
```

#### On macOS (using Homebrew):
```bash
brew install ffmpeg
```

#### On Windows:
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract the files to a directory (e.g., `C:\ffmpeg`)
3. Add the `bin` folder to your system PATH

### 5. Create Downloads Directory

```bash
# Create a directory for downloaded files
mkdir -p static/downloads
```

### 6. Starting the Application

```bash
# Using gunicorn (recommended for production)
gunicorn --bind 0.0.0.0:5000 main:app

# For development
python main.py
```

The application will be available at http://localhost:5000

## Troubleshooting

### Common Issues

1. **FFmpeg not found** - Ensure FFmpeg is properly installed and available in your PATH
2. **Download errors** - Some platforms may restrict certain videos or formats
3. **Slow performance** - High-resolution videos may take longer to process

### Checking FFmpeg Installation

To verify FFmpeg is properly installed, run:

```bash
ffmpeg -version
```

This should display the FFmpeg version information.