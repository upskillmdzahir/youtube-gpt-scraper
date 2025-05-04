# User Guide: Universal Video Downloader

This guide explains how to use the Universal Video Downloader application to download videos from various platforms with your preferred format settings.

**Note:** This application works without any API keys or paid services. You don't need to sign up for any external services to use all features.

## Getting Started

1. Open your web browser and navigate to the application URL (typically http://localhost:5000 if running locally)
2. You'll see the main interface with an input field for video URLs

## Basic Usage

### Step 1: Enter a Video URL

- Paste a valid video URL from supported platforms (YouTube, Vimeo, Dailymotion, etc.)
- Click the "Fetch Video" button
- The application will retrieve available formats and display them

### Step 2: Select Download Options

Once the video information is loaded, you'll see:

- **Video thumbnail** - Preview of the video
- **Video details** - Title, duration, and uploader information
- **Format selection** - Dropdown menus for selecting video and audio quality
- **Download type** - Options for combined, video-only, or audio-only downloads

#### Video Quality Selection

- Click the "Select quality" dropdown under Video Format
- Choose from available resolutions (480p and higher)
- Higher resolutions offer better video quality but larger file sizes

#### Audio Quality Selection

- Click the "Select quality" dropdown under Audio Format
- Choose from available audio bitrates
- Higher bitrates (like 320kbps, 256kbps) offer better audio quality
- Green highlighted options indicate high-quality audio

#### Download Type Selection

You can choose from three download types:

1. **Video + Audio** (default) - Downloads and combines both video and audio tracks
2. **Video Only** - Downloads just the video track without audio (useful for editing)
3. **Audio Only** - Downloads just the audio track (perfect for music or podcasts)

### Step 3: Download and Process

- Click the "Convert & Download" button
- The application will process your request, showing a progress bar
- Processing time depends on video length, selected quality, and network speed

### Step 4: Get Your Files

- When processing is complete, you'll see a "Download" button
- Click to save your file to your computer
- If available, the video transcript will be displayed on the right

## Tips and Advanced Features

### Transcript Extraction

- For videos with subtitles, the application automatically extracts and cleans the transcript
- The transcript appears on the right side after processing
- Use the "Copy Full Transcript" button to copy the text to your clipboard

### Format Selection Tips

- **For highest quality**: Select the highest resolution for video and highest bitrate for audio
- **For small file size**: Select lower resolutions and bitrates
- **For audio only**: Choose "Audio Only" download type and select your preferred audio quality
- **For video editing**: Choose "Video Only" download type and select your preferred resolution

### Supported Platforms

The application works with most major video platforms, including:

- YouTube
- Vimeo
- Dailymotion
- Facebook videos
- Twitter videos
- And many more!

## Troubleshooting

### Video Not Loading

- Ensure the URL is correct and from a supported platform
- Some videos may be private or region-restricted
- Try refreshing the page and entering the URL again

### Download Takes Too Long

- High-resolution videos take longer to process
- Large files require more time for download and conversion
- Consider selecting a lower quality option for faster processing

### Audio/Video Quality Issues

- Not all quality options are available for every video
- The application shows only formats that are actually available
- Some platforms may restrict certain high-quality formats

### Format Selection Not Working

- Ensure you've selected both a video and audio format (for combined downloads)
- For audio-only downloads, you only need to select an audio format
- For video-only downloads, you only need to select a video format

## Privacy Note

- All processing happens on the server running the application
- No data is shared with third parties
- Downloaded files and transcripts are not stored permanently