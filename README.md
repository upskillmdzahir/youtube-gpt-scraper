# Universal Video Downloader

A powerful web application that allows downloading videos and audio from multiple platforms (YouTube, Vimeo, Dailymotion, and more) with quality selection options and transcript extraction.

## Features

- **Multi-Platform Support**: Download from YouTube, Vimeo, Dailymotion, and many other video platforms
- **Format Selection**: Choose between video+audio, video-only, or audio-only downloads
- **Quality Control**: Select from available video resolutions (480p and above) and audio qualities
- **Transcript Extraction**: Get clean, formatted video transcripts automatically
- **Flexible Downloads**: Download audio files for music, video-only for editing, or complete videos

## Technical Details

This application is built with:

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Media Processing**: yt-dlp, ffmpeg
- **Transcript Extraction**: Built-in subtitle parsing

No API keys or external services required!

## Requirements

- Python 3.10 or higher
- FFmpeg installed on your system
- Required Python packages (listed in requirements.txt)

## Installation

### Local Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd video-downloader
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Ensure FFmpeg is installed on your system:
   - **Linux**: `sudo apt install ffmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH

5. Create a `static/downloads` directory:
   ```
   mkdir -p static/downloads
   ```

### Deployment on Hosting Platforms

#### Heroku Deployment

1. Make sure you have the Heroku CLI installed and are logged in
2. Add the necessary buildpacks:
   ```
   heroku buildpacks:add --index 1 heroku/python
   heroku buildpacks:add --index 2 https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
   ```
3. Deploy the application:
   ```
   git push heroku main
   ```

#### PythonAnywhere Deployment

1. Create a new web app with Flask
2. Set up a virtual environment and install dependencies from requirements.txt
3. Set the WSGI configuration to use main.py and the app variable
4. Install FFmpeg using the console (may require a paid account for full functionality)

#### Railway, Render, or Vercel

These platforms can deploy directly from your GitHub repository. Make sure your repository includes:
- requirements.txt
- Procfile
- runtime.txt

Most platforms will detect and build the application automatically.

## Usage

1. Start the application:
   ```
   gunicorn --bind 0.0.0.0:5000 main:app
   ```
   Or for development:
   ```
   python main.py
   ```

2. Open your browser and go to `http://localhost:5000`

3. Enter a video URL and click "Fetch Video"

4. Select your desired format options:
   - Choose a video quality from the dropdown
   - Choose an audio quality from the dropdown
   - Select download type (Combined, Video Only, or Audio Only)

5. Click "Convert & Download" to process the video

6. Once processing is complete, click the download button to save your file

## Download Types

- **Video + Audio**: Standard combined video with audio (default)
- **Video Only**: Video without audio track (useful for editing)
- **Audio Only**: Audio track only (useful for music)

## Troubleshooting

- **Downloads failing**: Ensure FFmpeg is correctly installed and available in your PATH
- **Format unavailable**: Some platforms may restrict certain formats or qualities
- **Slow downloads**: Large videos or high-resolution formats may take longer to process

## Monetization with Google AdSense

To monetize your deployed video downloader with Google AdSense:

1. **Register for Google AdSense**: Visit [AdSense](https://www.google.com/adsense) and create an account
   
2. **Get Your Site Approved**: AdSense requires review and approval of your website
   - Ensure your site has a privacy policy
   - Have sufficient original content
   - Follow all AdSense policies

3. **Adding AdSense to the Site**:
   - Add your AdSense code to the site templates. For example, in base.html:
   ```html
   <!-- Google AdSense -->
   <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-YOURID" crossorigin="anonymous"></script>
   ```
   
4. **Ad Placement**:
   - Consider adding ads in these strategic locations:
     - Sidebar ads on the main page
     - Banner ads before the download buttons
     - Responsive ads in the footer
     - Interstitial ads between downloading steps

5. **Compliance and Best Practices**:
   - Don't use deceptive ads or placements
   - Respect user experience when placing ads
   - Follow AdSense terms of service

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

A True creation of Raiinex