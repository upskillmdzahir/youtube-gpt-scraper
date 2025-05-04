# Technical Documentation

This document provides a technical overview of the Universal Video Downloader application architecture, explaining key components and how they interact.

## Architecture Overview

The application follows a simple Flask-based web architecture:

```
┌─────────────┐    ┌─────────────┐    ┌──────────────┐
│  Web Browser │◄──►│  Flask App  │◄──►│  Video APIs  │
└─────────────┘    └─────────────┘    └──────────────┘
                         │
                         ▼
                   ┌─────────────┐
                   │ FFmpeg/yt-dlp│
                   └─────────────┘
```

## Key Components

### Backend (Python/Flask)

1. **app.py**: Main application file containing:
   - API endpoints for video information and download
   - Core functionality for video processing
   - Download and merge operations

2. **main.py**: Application entry point
   - Imports the Flask app
   - Configures the server

3. **utils.py**: Utility functions
   - Format conversions (duration, timestamps, etc.)
   - Video ID extraction
   - Transcript cleaning

### Frontend (HTML/JS/CSS)

1. **index.html**: Main user interface
   - URL input form
   - Format selection dropdowns
   - Download type selection
   - Progress indicators
   - Results display (download link and transcript)

2. **main.js**: Frontend JavaScript functionality
   - Fetching video information
   - UI updates and interactions
   - Progress monitoring
   - Download handling

### External Libraries

1. **yt-dlp**:
   - Video information extraction
   - Format identification
   - Media downloading

2. **FFmpeg**:
   - Video/audio processing
   - Format conversion
   - Stream merging

3. **Transcript API**:
   - Subtitle extraction and processing

## Request Flow

1. **User Enters URL**:
   - Browser sends URL to `/get_video_info` endpoint
   - Backend uses yt-dlp to fetch video details
   - Response includes available formats and metadata

2. **User Selects Formats**:
   - User selects video quality, audio quality, and download type
   - Selections are stored in browser memory

3. **Download Request**:
   - Browser sends POST to `/download` with selected format IDs
   - Backend generates a unique session ID
   - Download process starts in a background thread

4. **Progress Monitoring**:
   - Browser polls `/download_progress` endpoint
   - Backend reports current status of download/processing
   - Progress is displayed to user

5. **File Serving**:
   - When processing completes, a download link is provided
   - User clicks to download from `/download_file/<filename>` endpoint
   - File is served from the server's temporary storage

## Key Functions

### `get_video_info(url)`
- Extracts video metadata using yt-dlp
- Processes available formats
- Cleans and organizes format information
- Attempts to extract transcript
- Returns structured data as JSON

### `download_and_merge(session_id, url, video_format_id, audio_format_id, output_ext, download_type)`
- Manages download process based on selected type
- Downloads video/audio streams as needed
- Merges streams for combined downloads
- Cleans transcript if available
- Updates progress indicators
- Returns completed file info

### `clean_transcript(transcript)`
- Removes formatting markers from subtitles
- Cleans timestamps and alignment tags
- Makes transcript human-readable

## Data Flow Diagram

```
URL Input ──► Video Info Fetch ──► Format Selection
                                        │
                                        ▼
Download Request ◄── User Selection ◄── UI Update
      │
      ▼
Download Process ──► Progress Updates ──► User Interface
      │
      ▼
FFmpeg Processing ──► File Creation ──► Download Link
      │
      ▼
Transcript Extraction ──────────────► Transcript Display
```

## Extension Points

For developers looking to extend this application:

1. **Adding new platforms**:
   - yt-dlp handles most platforms automatically
   - For unsupported sites, add custom extractors

2. **Custom format processing**:
   - Modify `get_video_info()` to support additional format filtering
   - Add custom processing logic to `download_and_merge()`

3. **Enhanced transcript processing**:
   - Extend `clean_transcript()` with additional formatting options
   - Add language detection/translation capabilities

4. **UI Enhancements**:
   - The frontend is built with Bootstrap and vanilla JavaScript
   - Components can be modified in templates/index.html
   - Styles can be added to static/css/

## Performance Considerations

- Downloads happen in background threads to prevent blocking
- Temporary files are used during processing
- Files are cleaned up after serving
- Progress monitoring uses polling with a 1-second interval