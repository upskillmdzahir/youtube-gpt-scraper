import os
import json
import tempfile
import subprocess
import re
from threading import Thread
from flask import Flask, render_template, request, jsonify, session, Response, send_file
import yt_dlp
import ffmpeg

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key")

# Store download progress globally (in production, use a proper database)
download_progress = {}
video_info_cache = {}

def get_video_info(url):
    """Get video information using yt-dlp."""
    if url in video_info_cache:
        return video_info_cache[url]
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Process formats to make them more readable
            video_formats = []
            audio_formats = []
            
            for f in info.get('formats', []):
                format_note = f.get('format_note', '')
                file_size = f.get('filesize') or f.get('filesize_approx')
                
                if file_size:
                    file_size_mb = round(file_size / (1024 * 1024), 2)
                    size_str = f"{file_size_mb} MB"
                else:
                    size_str = "Unknown size"
                
                format_id = f.get('format_id', '')
                ext = f.get('ext', '')
                
                if f.get('vcodec') != 'none' and f.get('acodec') == 'none':
                    # Video-only format
                    height = f.get('height')
                    width = f.get('width')
                    
                    if height and width:
                        resolution = f"{width}x{height}"
                        quality = f"{height}p" if height else format_note
                        
                        # Only include formats 480p and above
                        if height and height >= 480:
                            # Create clean display text that shows resolution and size
                            display_text = f"{quality} ({ext})"
                            if size_str != "Unknown size":
                                display_text += f" - {size_str}"
                                
                            video_formats.append({
                                'format_id': format_id,
                                'ext': ext,
                                'quality': quality,
                                'resolution': resolution,
                                'size': size_str,
                                'display_text': display_text
                            })
                    else:
                        # Include formats where we can't determine height
                        # but have a format note that might indicate high quality
                        if format_note and any(q in format_note.lower() for q in ['720', '1080', 'hd', '4k']):
                            resolution = format_note
                            quality = format_note
                            
                            # Create clean display text
                            display_text = f"{quality} ({ext})"
                            if size_str != "Unknown size":
                                display_text += f" - {size_str}"
                                
                            video_formats.append({
                                'format_id': format_id,
                                'ext': ext,
                                'quality': quality,
                                'resolution': resolution,
                                'size': size_str,
                                'display_text': display_text
                            })
                
                elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    # Audio-only format
                    abr = f.get('abr')
                    asr = f.get('asr')  # Audio sampling rate (Hz)
                    quality_str = ""
                    
                    # Determine quality string, preferring bitrate
                    if abr:
                        quality_str = f"{int(abr)}kbps"
                        # Store raw bitrate for prioritization
                        raw_bitrate = float(abr)
                    elif format_note and 'kbps' in format_note.lower():
                        quality_str = format_note
                        # Try to extract bitrate from format note
                        try:
                            bitrate_part = format_note.lower().split('kbps')[0].strip()
                            if bitrate_part.isdigit():
                                raw_bitrate = float(bitrate_part)
                            else:
                                raw_bitrate = 0
                        except:
                            raw_bitrate = 0
                    elif asr:
                        # Approximate bitrate from sampling rate
                        # Higher sampling rates usually have higher quality
                        if asr >= 44100:
                            approx_bitrate = 192
                        elif asr >= 32000:
                            approx_bitrate = 128
                        else:
                            approx_bitrate = 96
                        quality_str = f"{approx_bitrate}kbps"
                        raw_bitrate = float(approx_bitrate)
                    else:
                        quality_str = format_note or "Unknown"
                        raw_bitrate = 0
                    
                    # Only add the audio format if it's a common format or high quality
                    # Prioritize high-quality formats (320kbps, 256kbps, 192kbps)
                    is_high_quality = raw_bitrate >= 192
                    is_preferred_format = ext in ['m4a', 'mp3', 'aac', 'opus']
                    
                    if is_high_quality or is_preferred_format:
                        audio_formats.append({
                            'format_id': format_id,
                            'ext': ext,
                            'quality': quality_str,
                            'raw_bitrate': raw_bitrate,
                            'size': size_str,
                            'display_text': f"{quality_str} ({ext})"  # Clean display text
                        })
            
            # Sort formats by quality (higher resolution/bitrate first)
            video_formats.sort(key=lambda x: int(x['quality'].replace('p', '')) if x['quality'].replace('p', '').isdigit() else 0, reverse=True)
            
            # Custom sorting for audio formats to prioritize high quality options
            def audio_format_quality_score(format_item):
                # First, try to use raw bitrate directly
                if 'raw_bitrate' in format_item and format_item['raw_bitrate']:
                    bitrate = float(format_item['raw_bitrate'])
                    
                    # Give higher priority to specific high-quality bitrates
                    if bitrate >= 320:  # 320kbps is highest priority
                        return 10000 + bitrate
                    elif bitrate >= 256:  # 256kbps is second priority
                        return 9000 + bitrate
                    elif bitrate >= 192:  # 192kbps is third priority
                        return 8000 + bitrate
                    else:
                        return bitrate
                
                # Fallback for formats where we can't determine bitrate
                # Give preference to high-quality formats
                if format_item['ext'] in ['m4a', 'aac']:
                    return 500  # Higher score for preferred formats
                elif format_item['ext'] in ['mp3', 'opus']:
                    return 400  # Good score for common formats
                
                return 0  # Lowest priority for unknown/unrated formats
            
            # Sort by our custom quality score
            audio_formats.sort(key=audio_format_quality_score, reverse=True)
            
            result = {
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'video_formats': video_formats,
                'audio_formats': audio_formats,
                'description': info.get('description', ''),
                'webpage_url': info.get('webpage_url'),
            }
            
            # Try to get transcript if available
            try:
                subtitles = info.get('subtitles', {})
                captions = info.get('automatic_captions', {})
                
                # Prefer manually created subtitles over automatic captions
                transcript_sources = subtitles or captions
                
                if transcript_sources:
                    # Prefer English, but take any language if English is not available
                    lang_keys = list(transcript_sources.keys())
                    lang_pref = 'en' if 'en' in lang_keys else lang_keys[0]
                    
                    transcript_formats = transcript_sources[lang_pref]
                    
                    # Prefer text formats
                    for fmt in transcript_formats:
                        if fmt.get('ext') in ['txt', 'vtt', 'srt']:
                            transcript_url = fmt.get('url')
                            if transcript_url:
                                import requests
                                transcript_text = requests.get(transcript_url).text
                                
                                # Simple cleaning for common subtitle formats
                                if fmt.get('ext') in ['vtt', 'srt']:
                                    import re
                                    # Remove timestamps and other non-text elements
                                    clean_text = re.sub(r'\d+:\d+:\d+.\d+ --> \d+:\d+:\d+.\d+', '', transcript_text)
                                    clean_text = re.sub(r'^\d+$', '', clean_text, flags=re.MULTILINE)
                                    clean_text = re.sub(r'<[^>]+>', '', clean_text)
                                    clean_text = '\n'.join(line for line in clean_text.split('\n') if line.strip())
                                    
                                    result['transcript'] = clean_text
                                    break
                                else:
                                    result['transcript'] = transcript_text
                                    break
            except Exception as e:
                print(f"Error extracting transcript: {str(e)}")
                result['transcript'] = None
            
            # Cache the result
            video_info_cache[url] = result
            return result
            
    except Exception as e:
        print(f"Error extracting video info: {str(e)}")
        return {'error': str(e)}

def download_and_merge(session_id, url, video_format_id, audio_format_id, output_ext='mp4', download_type='combined'):
    """Download video and audio based on the download type."""
    download_progress[session_id] = {
        'status': 'downloading',
        'progress': 0,
        'video_progress': 0 if download_type != 'audio_only' else 100,
        'audio_progress': 0 if download_type != 'video_only' else 100,
        'message': 'Starting download...',
        'download_type': download_type
    }
    
    try:
        # Create a temp directory to store downloaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get video info for title
            video_info = get_video_info(url)
            safe_title = "".join([c for c in video_info.get('title', 'download') if c.isalnum() or c in ' ._-']).strip()
            
            # Define different output paths based on download type
            output_dir = os.path.join('static', 'downloads')
            os.makedirs(output_dir, exist_ok=True)
            
            if download_type == 'audio_only':
                # For audio-only, use m4a extension
                output_filename = f'{safe_title}_audio.m4a'
                audio_file = os.path.join(temp_dir, 'audio.m4a')
                output_path = os.path.join(output_dir, output_filename)
                
                # Download audio only
                download_progress[session_id]['message'] = 'Downloading audio...'
                audio_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': audio_format_id,
                    'outtmpl': audio_file,
                    'progress_hooks': [lambda d: update_audio_progress(session_id, d)],
                }
                
                with yt_dlp.YoutubeDL(audio_opts) as ydl:
                    ydl.download([url])
                
                download_progress[session_id]['audio_progress'] = 100
                download_progress[session_id]['progress'] = 100
                
                # Just copy the audio file to the output location
                import shutil
                shutil.copy2(audio_file, output_path)
                
                # Complete the download
                download_progress[session_id] = {
                    'status': 'complete',
                    'progress': 100,
                    'message': 'Audio download complete',
                    'output_path': output_path,
                    'filename': os.path.basename(output_path),
                    'download_type': download_type
                }
                print(f"Successfully downloaded audio only for {video_info['title']}")
                
            elif download_type == 'video_only':
                # For video-only
                output_filename = f'{safe_title}_video.{output_ext}'
                video_file = os.path.join(temp_dir, f'video.{output_ext}')
                output_path = os.path.join(output_dir, output_filename)
                
                # Download video only
                download_progress[session_id]['message'] = 'Downloading video...'
                video_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': video_format_id,
                    'outtmpl': video_file,
                    'progress_hooks': [lambda d: update_video_progress(session_id, d)],
                }
                
                with yt_dlp.YoutubeDL(video_opts) as ydl:
                    ydl.download([url])
                
                download_progress[session_id]['video_progress'] = 100
                download_progress[session_id]['progress'] = 100
                
                # Just copy the video file to the output location
                import shutil
                shutil.copy2(video_file, output_path)
                
                # Clean and add transcript if available
                transcript = ''
                if video_info.get('transcript'):
                    transcript = clean_transcript(video_info.get('transcript', ''))
                
                # Complete the download
                download_progress[session_id] = {
                    'status': 'complete',
                    'progress': 100,
                    'message': 'Video-only download complete',
                    'output_path': output_path,
                    'filename': os.path.basename(output_path),
                    'transcript': transcript,
                    'download_type': download_type
                }
                print(f"Successfully downloaded video only for {video_info['title']}")
                
            else:
                # For combined video and audio
                output_filename = f'{safe_title}.{output_ext}'
                video_file = os.path.join(temp_dir, f'video.{output_ext}')
                audio_file = os.path.join(temp_dir, 'audio.m4a')
                output_path = os.path.join(output_dir, output_filename)
                
                # Download video
                download_progress[session_id]['message'] = 'Downloading video...'
                video_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': video_format_id,
                    'outtmpl': video_file,
                    'progress_hooks': [lambda d: update_video_progress(session_id, d)],
                }
                
                with yt_dlp.YoutubeDL(video_opts) as ydl:
                    ydl.download([url])
                
                download_progress[session_id]['video_progress'] = 100
                download_progress[session_id]['message'] = 'Downloading audio...'
                
                # Download audio
                audio_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'format': audio_format_id,
                    'outtmpl': audio_file,
                    'progress_hooks': [lambda d: update_audio_progress(session_id, d)],
                }
                
                with yt_dlp.YoutubeDL(audio_opts) as ydl:
                    ydl.download([url])
                
                download_progress[session_id]['audio_progress'] = 100
                download_progress[session_id]['message'] = 'Merging video and audio...'
                
                # Merge video and audio using ffmpeg
                try:
                    ffmpeg.input(video_file).output(
                        ffmpeg.input(audio_file),
                        output_path,
                        vcodec='copy',
                        acodec='aac',
                        strict='experimental'
                    ).run(quiet=True, overwrite_output=True)
                    
                    # Clean and add transcript if available
                    transcript = ''
                    if video_info.get('transcript'):
                        transcript = clean_transcript(video_info.get('transcript', ''))
                    
                    # Complete the download
                    download_progress[session_id] = {
                        'status': 'complete',
                        'progress': 100,
                        'message': 'Download complete',
                        'output_path': output_path,
                        'filename': os.path.basename(output_path),
                        'transcript': transcript,
                        'download_type': download_type
                    }
                    print(f"Successfully processed video content for {video_info['title']}")
                    
                except Exception as e:
                    print(f"Error merging files: {str(e)}")
                    download_progress[session_id] = {
                        'status': 'error',
                        'message': f'Error merging files: {str(e)}',
                        'download_type': download_type
                    }
    
    except Exception as e:
        print(f"Download error: {str(e)}")
        download_progress[session_id] = {
            'status': 'error',
            'message': f'Download error: {str(e)}',
            'download_type': download_type
        }

def clean_transcript(transcript):
    """Clean transcript text by removing WEBVTT markers, timestamps, and formatting"""
    # Make sure transcript is a string
    if not transcript:
        return ""
    
    # Dictionary to track unique content
    unique_content = {}
    
    # Remove WEBVTT header and metadata
    lines = str(transcript).split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip WEBVTT headers and metadata
        if any(keyword in line for keyword in ['WEBVTT', 'Kind:', 'Language:']):
            continue
            
        # Skip timestamp lines (they contain --> format)
        if '-->' in line:
            continue
            
        # Skip empty numeric lines (usually indices)
        if line.strip().isdigit():
            continue
            
        # Skip any line with line percentage format (like line:76%)
        if re.search(r'line:\d+%', line):
            continue
            
        # Skip alignment and position markers
        if any(marker in line for marker in ['align:', 'position:']):
            continue
        
        # Clean HTML entities and special formatting
        cleaned_line = line
        
        # Replace HTML entities
        cleaned_line = cleaned_line.replace('&gt;', '>')
        cleaned_line = cleaned_line.replace('&lt;', '<')
        cleaned_line = cleaned_line.replace('&amp;', '&')
        
        # Remove angle brackets (often used for speaker identification)
        cleaned_line = re.sub(r'>>>|>>|\[\[.*?\]\]|\[.*?\]', '', cleaned_line)
        
        # Remove Reporter: and similar tags
        cleaned_line = re.sub(r'(Reporter|Speaker|Host|Narrator):\s*', '', cleaned_line)
        
        # Remove timestamp markers and caption markers
        cleaned_line = re.sub(r'<\d{2}:\d{2}:\d{2}\.\d{3}>', '', cleaned_line)
        cleaned_line = re.sub(r'<c>', '', cleaned_line) 
        cleaned_line = re.sub(r'</c>', '', cleaned_line)
        
        # Trim whitespace
        cleaned_line = cleaned_line.strip()
        
        # Only add non-empty lines that we haven't seen before
        if cleaned_line and cleaned_line not in unique_content:
            unique_content[cleaned_line] = True
            cleaned_lines.append(cleaned_line)
    
    # Join the unique lines
    cleaned_text = '\n'.join(cleaned_lines)
    
    # Add paragraph breaks for readability (after sentence-ending punctuation)
    cleaned_text = re.sub(r'([.!?])\s+', r'\1\n\n', cleaned_text)
    
    # Clean up any remaining multiple newlines
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    return cleaned_text.strip()

@app.route('/test-transcript', methods=['GET', 'POST'])
def test_transcript_cleaning():
    """
    Test page for the transcript cleaning function
    """
    raw_transcript = ""
    cleaned_transcript = ""
    original_count = 0
    cleaned_count = 0
    original_chars = 0
    cleaned_chars = 0
    reduction = 0
    
    if request.method == 'POST':
        raw_transcript = request.form.get('raw_transcript', '')
        
        if raw_transcript:
            cleaned_transcript = clean_transcript(raw_transcript)
            
            # Calculate stats
            original_count = len(raw_transcript.split())
            cleaned_count = len(cleaned_transcript.split())
            original_chars = len(raw_transcript)
            cleaned_chars = len(cleaned_transcript)
            
            if original_chars > 0:
                reduction = round((1 - (cleaned_chars / original_chars)) * 100, 1)
    
    return render_template('test_transcript.html', 
                          raw_transcript=raw_transcript,
                          cleaned_transcript=cleaned_transcript,
                          original_count=original_count,
                          cleaned_count=cleaned_count, 
                          original_chars=original_chars,
                          cleaned_chars=cleaned_chars,
                          reduction=reduction)

def update_video_progress(session_id, d):
    """Update video download progress."""
    if d['status'] == 'downloading':
        try:
            if 'total_bytes' in d and d['total_bytes'] > 0:
                percentage = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                percentage = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            else:
                percentage = 0
                
            download_progress[session_id]['video_progress'] = percentage
            # Overall progress is average of video and audio progress
            download_progress[session_id]['progress'] = (
                download_progress[session_id]['video_progress'] + 
                download_progress[session_id]['audio_progress']
            ) / 2
        except Exception as e:
            print(f"Error updating video progress: {str(e)}")

def update_audio_progress(session_id, d):
    """Update audio download progress."""
    if d['status'] == 'downloading':
        try:
            if 'total_bytes' in d and d['total_bytes'] > 0:
                percentage = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif 'total_bytes_estimate' in d and d['total_bytes_estimate'] > 0:
                percentage = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            else:
                percentage = 0
                
            download_progress[session_id]['audio_progress'] = percentage
            # Overall progress is average of video and audio progress
            download_progress[session_id]['progress'] = (
                download_progress[session_id]['video_progress'] + 
                download_progress[session_id]['audio_progress']
            ) / 2
        except Exception as e:
            print(f"Error updating audio progress: {str(e)}")

# Removed OpenAI analysis functions as they are not needed


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')

@app.route('/get_video_info', methods=['POST'])
def get_video_info_route():
    """API endpoint to get video information."""
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        info = get_video_info(url)
        if 'error' in info:
            return jsonify({'error': info['error']}), 400
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download_video():
    """API endpoint to start the download process."""
    url = request.form.get('url')
    video_format_id = request.form.get('video_format')
    audio_format_id = request.form.get('audio_format')
    output_ext = request.form.get('output_ext', 'mp4')
    download_type = request.form.get('download_type', 'combined')  # Default to combined
    
    # Generate a unique session ID if not exists
    if 'session_id' not in session:
        session['session_id'] = os.urandom(16).hex()
    
    session_id = session['session_id']
    
    # Validate depending on download type
    if download_type == 'video_only':
        if not all([url, video_format_id]):
            return jsonify({'error': 'URL and video format are required for video-only download'}), 400
        audio_format_id = None
    elif download_type == 'audio_only':
        if not all([url, audio_format_id]):
            return jsonify({'error': 'URL and audio format are required for audio-only download'}), 400
        video_format_id = None
        output_ext = 'm4a'  # Use m4a for audio-only downloads
    else:  # combined
        if not all([url, video_format_id, audio_format_id]):
            return jsonify({'error': 'URL, video format, and audio format are required for combined download'}), 400
    
    # Start download in background thread
    thread = Thread(target=download_and_merge, args=(session_id, url, video_format_id, audio_format_id, output_ext, download_type))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started', 'session_id': session_id, 'download_type': download_type})

@app.route('/download_progress')
def get_download_progress():
    """API endpoint to check download progress."""
    session_id = session.get('session_id')
    if not session_id or session_id not in download_progress:
        return jsonify({'status': 'not_started', 'progress': 0})
    
    # Filter the response to include only necessary fields
    progress_data = download_progress[session_id]
    response = {
        'status': progress_data.get('status', 'unknown'),
        'progress': progress_data.get('progress', 0),
        'message': progress_data.get('message', ''),
        'download_type': progress_data.get('download_type', 'combined')  # Include download type
    }
    
    # Include only filename and transcript if available
    if 'filename' in progress_data:
        response['filename'] = progress_data['filename']
    if 'transcript' in progress_data:
        response['transcript'] = progress_data['transcript']
    
    return jsonify(response)

@app.route('/download_file/<filename>')
def download_file(filename):
    """Download the processed file."""
    file_path = os.path.join('static', 'downloads', filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    # Create downloads directory if it doesn't exist
    os.makedirs(os.path.join('static', 'downloads'), exist_ok=True)
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)