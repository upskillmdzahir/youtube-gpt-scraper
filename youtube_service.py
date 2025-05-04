import logging
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import requests
import os
import tempfile
import time
from pytube import YouTube

import logging
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import string


def get_video_transcript(video_id):
    """
    Advanced transcript cleaning with:
    - Multi-line merging
    - Split-line duplicate detection
    - Context-aware normalization
    - Progressive deduplication
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id,
                                                         languages=['en'])
        if not transcript:
            return "No transcript available"

        cleaned = []
        buffer = []
        prev_normalized = ""
        punctuation = str.maketrans('', '',
                                    string.punctuation.replace("'", ""))

        def normalize(t):
            """Context-aware normalization"""
            return t.translate(punctuation).lower().replace(" ", "").strip()

        def is_continuation(current, previous):
            """Check if current line continues previous text"""
            return current.startswith(
                previous.split()[-1]) if previous else False

        for entry in transcript:
            text = entry['text'].strip()
            if not text:
                continue

            # Buffer management for split lines
            if buffer and (len(buffer[-1].split()) < 4
                           or is_continuation(text, buffer[-1])):
                buffer[-1] += " " + text
            else:
                buffer.append(text)

        # Process buffered lines
        for line in buffer:
            line_normalized = normalize(line)

            if not line_normalized:
                continue

            # Split-line duplicate check
            is_duplicate = any(
                line_normalized.startswith(n) or n.startswith(line_normalized)
                for n in [prev_normalized])

            if not is_duplicate and line_normalized != prev_normalized:
                cleaned.append(line)
                prev_normalized = line_normalized

        return "\n".join(cleaned) or "No meaningful transcript found"

    except (NoTranscriptFound, TranscriptsDisabled):
        return "Captions unavailable"
    except Exception as e:
        logging.error(f"Transcript error: {str(e)}")
        return "Error retrieving transcript"


def get_video_info(video_id):
    """
    Get basic information about a YouTube video like title, duration, etc.
    
    Args:
        video_id: The YouTube video ID
        
    Returns:
        A dictionary with video information or None if unavailable
    """

    try:
        # Add a user-agent header to avoid being blocked
        from pytube import YouTube
        import time

        # Sleep briefly to avoid rate limiting
        time.sleep(1)

        # Create a YouTube object with an improved request strategy
        yt = YouTube(f"https://www.youtube.com/watch?v={video_id}",
                     use_oauth=False,
                     allow_oauth_cache=False)

        # Force initial data fetch to validate connection
        yt.check_availability()

        # Extract relevant information with fallbacks
        title = yt.title if hasattr(yt, 'title') else f"Video {video_id}"
        author = yt.author if hasattr(yt, 'author') else "Unknown Creator"
        duration = yt.length if hasattr(yt, 'length') else 0
        thumbnail = yt.thumbnail_url if hasattr(yt, 'thumbnail_url') else ""
        publish_date = yt.publish_date.strftime('%Y-%m-%d') if hasattr(
            yt, 'publish_date') and yt.publish_date else None
        views = yt.views if hasattr(yt, 'views') else 0
        description = yt.description if hasattr(yt, 'description') else ""

        video_info = {
            'title': title,
            'author': author,
            'duration_seconds': duration,
            'thumbnail_url': thumbnail,
            'publish_date': publish_date,
            'views': views,
            'description': description
        }

        return video_info

    except Exception as e:
        logging.error(f"Error retrieving video info for {video_id}: {str(e)}")

        # Fallback with minimal info if YouTube API fails
        return {
            'title':
            f"Video {video_id}",
            'author':
            "Unknown Creator",
            'duration_seconds':
            0,
            'thumbnail_url':
            f"https://img.youtube.com/vi/{video_id}/0.jpg",
            'publish_date':
            None,
            'views':
            0,
            'description':
            "Unable to retrieve video description due to YouTube API limitations."
        }


def get_video_description(video_id):
    """
    Get the description of a YouTube video.
    
    Args:
        video_id: The YouTube video ID
        
    Returns:
        A string containing the video description, or None if unavailable
    """
    try:
        # Get description from the video_info function to avoid duplicate requests
        video_info = get_video_info(video_id)
        return video_info.get('description', "No description available")

    except Exception as e:
        logging.error(
            f"Error retrieving video description for {video_id}: {str(e)}")
        return "Unable to retrieve video description due to YouTube API limitations."


def get_video_formats(video_id):
    """
    Get all available formats for a YouTube video using yt-dlp
    
    Args:
        video_id: The YouTube video ID
        
    Returns:
        A dictionary containing video info and available formats categorized
    """
    try:
        import yt_dlp

        url = f"https://www.youtube.com/watch?v={video_id}"

        # Options to extract all available formats
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'format': 'best'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info:
                logging.error(
                    f"Could not retrieve formats for video {video_id}")
                return None

            # Basic video info
            basic_info = {
                'id': info.get('id'),
                'title': info.get('title', f'Video {video_id}'),
                'duration': info.get('duration'),
                'thumbnail': info.get('thumbnail'),
                'uploader': info.get('uploader'),
                'view_count': info.get('view_count', 0)
            }

            # Process formats
            formats = info.get('formats', [])

            # Categorize formats
            video_formats = []
            audio_formats = []
            combined_formats = []

            for f in formats:
                format_id = f.get('format_id', '')
                ext = f.get('ext', '')

                # Skip formats with no id or extension
                if not format_id or not ext:
                    continue

                format_info = {
                    'format_id': format_id,
                    'ext': ext,
                    'format_note': f.get('format_note', ''),
                    'filesize': f.get('filesize'),
                    'tbr': f.get('tbr'),  # Total bitrate
                    'url': f.get('url'),
                }

                # Video only formats
                if f.get('vcodec', 'none') != 'none' and f.get(
                        'acodec', 'none') == 'none':
                    if f.get('width') and f.get('height'):
                        format_info[
                            'resolution'] = f"{f.get('width')}x{f.get('height')}"
                        format_info['height'] = f.get('height')
                        format_info['width'] = f.get('width')
                        format_info['fps'] = f.get('fps')
                        format_info['vcodec'] = f.get('vcodec')
                        video_formats.append(format_info)

                # Audio only formats
                elif f.get('vcodec', 'none') == 'none' and f.get(
                        'acodec', 'none') != 'none':
                    format_info['acodec'] = f.get('acodec')
                    format_info['abr'] = f.get('abr')  # Audio bitrate
                    audio_formats.append(format_info)

                # Combined formats (video and audio)
                elif f.get('vcodec', 'none') != 'none' and f.get(
                        'acodec', 'none') != 'none':
                    if f.get('width') and f.get('height'):
                        format_info[
                            'resolution'] = f"{f.get('width')}x{f.get('height')}"
                        format_info['height'] = f.get('height')
                        format_info['width'] = f.get('width')
                        format_info['fps'] = f.get('fps')
                        format_info['vcodec'] = f.get('vcodec')
                        format_info['acodec'] = f.get('acodec')
                        combined_formats.append(format_info)

            # Sort formats by quality (resolution/bitrate)
            video_formats.sort(key=lambda x:
                               (x.get('height', 0) or 0, x.get('tbr', 0) or 0),
                               reverse=True)
            audio_formats.sort(key=lambda x: x.get('abr', 0) or 0,
                               reverse=True)
            combined_formats.sort(
                key=lambda x: (x.get('height', 0) or 0, x.get('tbr', 0) or 0),
                reverse=True)

            # Generate convenient format lists for the UI
            video_quality_options = []
            for vf in video_formats:
                if vf.get('height'):
                    label = f"{vf.get('height')}p"
                    if vf.get('fps') and vf.get('fps') > 30:
                        label += f" {vf.get('fps')}fps"
                    if not any(opt['label'] == label
                               for opt in video_quality_options):
                        video_quality_options.append({
                            'label':
                            label,
                            'format_id':
                            vf.get('format_id'),
                            'height':
                            vf.get('height'),
                            'ext':
                            vf.get('ext')
                        })

            audio_quality_options = []
            for af in audio_formats:
                if af.get('abr'):
                    label = f"{int(af.get('abr'))}kbps {af.get('ext').upper()}"
                    if not any(opt['label'] == label
                               for opt in audio_quality_options):
                        audio_quality_options.append({
                            'label':
                            label,
                            'format_id':
                            af.get('format_id'),
                            'abr':
                            af.get('abr'),
                            'ext':
                            af.get('ext')
                        })

            preset_formats = []
            # 4K
            if any(vf.get('height', 0) >= 2160 for vf in video_formats):
                preset_formats.append({'label': '4K (2160p)', 'value': '2160'})
            # 2K/1440p
            if any(vf.get('height', 0) >= 1440 for vf in video_formats):
                preset_formats.append({'label': '2K (1440p)', 'value': '1440'})
            # 1080p
            if any(vf.get('height', 0) >= 1080 for vf in video_formats):
                preset_formats.append({
                    'label': 'Full HD (1080p)',
                    'value': '1080'
                })
            # 720p
            if any(vf.get('height', 0) >= 720 for vf in video_formats):
                preset_formats.append({'label': 'HD (720p)', 'value': '720'})
            # 480p
            if any(vf.get('height', 0) >= 480 for vf in video_formats):
                preset_formats.append({'label': 'SD (480p)', 'value': '480'})
            # 360p
            if any(vf.get('height', 0) >= 360 for vf in video_formats):
                preset_formats.append({'label': '360p', 'value': '360'})

            # Add audio options
            preset_formats.append({
                'label': 'Audio only (High Quality)',
                'value': 'audio_high'
            })
            preset_formats.append({
                'label': 'Audio only (MP3)',
                'value': 'mp3'
            })

            return {
                'info': basic_info,
                'video_formats': video_formats,
                'audio_formats': audio_formats,
                'combined_formats': combined_formats,
                'video_quality_options': video_quality_options,
                'audio_quality_options': audio_quality_options,
                'preset_formats': preset_formats
            }

    except Exception as e:
        logging.error(f"Error getting video formats for {video_id}: {str(e)}")
        return None


def download_video(video_id,
                   format_type="mp4",
                   resolution="720p",
                   video_format_id=None,
                   audio_format_id=None,
                   progress_callback=None):
    """
    Download a YouTube video in the specified format and resolution using yt-dlp
    
    Args:
        video_id: The YouTube video ID
        format_type: The format to download ('mp4', 'mp3', 'webm', etc.)
        resolution: The resolution for video ('720p', '360p', etc.), ignored for audio
        video_format_id: Optional specific format ID for video stream
        audio_format_id: Optional specific format ID for audio stream
        progress_callback: Optional callback function for progress updates
        
    Returns:
        A tuple of (file_path, file_name, mime_type) or None if download failed
    """
    try:
        import yt_dlp

        # Create a temp directory for downloading
        temp_dir = tempfile.mkdtemp()
        url = f"https://www.youtube.com/watch?v={video_id}"

        # Get video info to use for filename
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', f'video_{video_id}')

        # Clean up file name
        file_name = "".join(c for c in title
                            if c.isalnum() or c in ' _-')[:50].strip().replace(
                                ' ', '_')

        class MyProgressHook:

            def __init__(self):
                self.downloaded_bytes = 0
                self.total_bytes = 0
                self.start_time = time.time()

            def __call__(self, d):
                if d['status'] == 'downloading':
                    self.downloaded_bytes = d.get('downloaded_bytes', 0)
                    self.total_bytes = d.get('total_bytes') or d.get(
                        'total_bytes_estimate', 0)

                    if self.total_bytes > 0:
                        progress = (self.downloaded_bytes /
                                    self.total_bytes) * 100
                        elapsed = time.time() - self.start_time
                        speed = self.downloaded_bytes / elapsed if elapsed > 0 else 0
                        eta = (self.total_bytes - self.downloaded_bytes
                               ) / speed if speed > 0 else 0

                        if progress_callback:
                            progress_callback({
                                'progress': progress,
                                'downloaded_bytes': self.downloaded_bytes,
                                'total_bytes': self.total_bytes,
                                'speed': speed,
                                'eta': eta
                            })

                elif d['status'] == 'finished':
                    if progress_callback:
                        progress_callback({
                            'progress': 100,
                            'downloaded_bytes': self.total_bytes,
                            'total_bytes': self.total_bytes,
                            'status': 'finished'
                        })

                elif d['status'] == 'error':
                    if progress_callback:
                        progress_callback({
                            'status':
                            'error',
                            'error':
                            d.get('error', 'Unknown error')
                        })

        progress_hook = MyProgressHook()

        # Set base options for all formats
        base_ydl_opts = {
            'quiet': True,
            'progress_hooks': [progress_hook],
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s')
        }

        # Set options based on format type
        if format_type.lower() in ["mp3", "audio"]:
            # Audio download
            output_file = os.path.join(temp_dir, f"{file_name}.mp3")
            mime_type = "audio/mpeg"
            file_name_with_ext = f"{file_name}.mp3"

            # If specific audio format requested
            if audio_format_id:
                format_spec = audio_format_id
                if format_type.lower() == "mp3":
                    base_ydl_opts['postprocessors'] = [{
                        'key':
                        'FFmpegExtractAudio',
                        'preferredcodec':
                        'mp3',
                        'preferredquality':
                        '192',
                    }]
            else:
                # Audio-only settings with best quality
                format_spec = 'bestaudio/best'
                if format_type.lower() == "mp3":
                    base_ydl_opts['postprocessors'] = [{
                        'key':
                        'FFmpegExtractAudio',
                        'preferredcodec':
                        'mp3',
                        'preferredquality':
                        '192',
                    }]

            ydl_opts = {**base_ydl_opts, 'format': format_spec}

        elif format_type.lower() == "webm":
            # WebM video download
            output_file = os.path.join(temp_dir, f"{file_name}.webm")
            mime_type = "video/webm"
            file_name_with_ext = f"{file_name}.webm"

            # If specific formats requested
            if video_format_id and audio_format_id:
                format_spec = f"{video_format_id}+{audio_format_id}/best"
            else:
                # WebM format with best quality
                format_spec = 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]/best'

            ydl_opts = {**base_ydl_opts, 'format': format_spec}

        else:  # Default to mp4
            # MP4 video download
            output_file = os.path.join(temp_dir, f"{file_name}.mp4")
            mime_type = "video/mp4"
            file_name_with_ext = f"{file_name}.mp4"

            # If specific formats requested
            if video_format_id and audio_format_id:
                format_spec = f"{video_format_id}+{audio_format_id}/best"
            else:
                # Select format based on resolution
                if resolution == "360p":
                    format_spec = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best[ext=mp4]/best'
                elif resolution == "480p":
                    format_spec = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[ext=mp4]/best'
                elif resolution == "720p":
                    format_spec = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[ext=mp4]/best'
                elif resolution == "1080p":
                    format_spec = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[ext=mp4]/best'
                elif resolution == "1440p":
                    format_spec = 'bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[height<=1440][ext=mp4]/best[ext=mp4]/best'
                elif resolution == "2160p":
                    format_spec = 'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160][ext=mp4]/best[ext=mp4]/best'
                else:
                    format_spec = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

            ydl_opts = {
                **base_ydl_opts, 'format': format_spec,
                'merge_output_format': 'mp4'
            }

        # Download the file
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the downloaded file
        downloaded_files = os.listdir(temp_dir)
        if not downloaded_files:
            logging.error(f"No files were downloaded to {temp_dir}")
            return None

        # Get the first file (should be the only one)
        actual_filename = downloaded_files[0]
        output_file = os.path.join(temp_dir, actual_filename)

        # Return the file info
        return (output_file, actual_filename, mime_type)

    except Exception as e:
        logging.error(
            f"Error downloading video {video_id} with yt-dlp: {str(e)}")

        # Fallback to pytube if yt-dlp fails
        try:
            # Create a YouTube object
            url = f"https://www.youtube.com/watch?v={video_id}"
            yt = YouTube(url)

            # Create a temp directory for downloading
            temp_dir = tempfile.mkdtemp()
            file_name = f"{yt.title.replace(' ', '_')[:50]}"  # Truncate and remove spaces

            # Handle different format types
            if format_type.lower() in ["mp3", "audio"]:
                # Get the audio stream
                stream = yt.streams.filter(only_audio=True).first()
                if not stream:
                    return None

                # Download to temp location
                file_path = stream.download(output_path=temp_dir,
                                            filename=f"{file_name}.mp3")
                mime_type = "audio/mpeg"
                file_name = f"{file_name}.mp3"

            elif format_type.lower() == "webm":
                # Get the video stream in webm format
                stream = yt.streams.filter(
                    file_extension="webm").get_highest_resolution()
                if not stream:
                    stream = yt.streams.filter(file_extension="webm").first()
                if not stream:
                    return None

                file_path = stream.download(output_path=temp_dir,
                                            filename=f"{file_name}.webm")
                mime_type = "video/webm"
                file_name = f"{file_name}.webm"

            else:  # Default to mp4
                # Try to get the requested resolution
                stream = yt.streams.filter(file_extension="mp4",
                                           resolution=resolution).first()

                # If not available, get the highest resolution
                if not stream:
                    stream = yt.streams.filter(
                        file_extension="mp4").get_highest_resolution()

                # If still no stream, get any mp4 stream
                if not stream:
                    stream = yt.streams.filter(file_extension="mp4").first()

                if not stream:
                    return None

                file_path = stream.download(output_path=temp_dir,
                                            filename=f"{file_name}.mp4")
                mime_type = "video/mp4"
                file_name = f"{file_name}.mp4"

            return (file_path, file_name, mime_type)

        except Exception as fallback_error:
            logging.error(
                f"Fallback download with pytube also failed: {str(fallback_error)}"
            )
            return None
