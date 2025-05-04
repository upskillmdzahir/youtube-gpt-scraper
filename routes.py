import logging
import json
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from flask import render_template, request, redirect, url_for, flash, session, jsonify, send_file, make_response
import io
import os
import tempfile

from app import app, db
from models import VideoAnalysis
from youtube_service import get_video_info, get_video_transcript, get_video_description, download_video, get_video_formats
from utils import generate_embed_code, format_timestamp, format_duration, format_view_count

# Define placeholder functions to replace the GPT service functionality
def analyze_transcript(transcript):
    """Simple placeholder function that returns empty values"""
    return {"key_points": "", "sentiment": 0}

def summarize_transcript(transcript):
    """Simple placeholder function that returns an empty summary"""
    return "Transcript summary is not available without OpenAI API."

def analyze_dev_content(transcript):
    """Simple placeholder function that returns empty developer content"""
    return {
        "is_dev_content": False,
        "code_snippets": [],
        "dev_tools": [],
        "key_timestamps": []
    }

def analyze_creator_content(transcript, title="", duration_seconds=0):
    """Simple placeholder function that returns empty creator content"""
    return {
        "chapters": [],
        "quotable_moments": [],
        "short_form_ideas": [],
        "social_media_captions": {},
        "recommended_hashtags": [],
        "voiceover_script": ""
    }

# Add template context processors
@app.context_processor
def utility_processor():
    def now():
        return datetime.now()
    
    # Add utility functions to be used in templates
    from utils import format_duration, format_view_count, format_timestamp, generate_embed_code
    
    return {
        'now': now,
        'format_duration': format_duration,
        'format_view_count': format_view_count,
        'format_timestamp': format_timestamp,
        'generate_embed_code': generate_embed_code
    }

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/api/docs')
def api_docs():
    """
    Render the API documentation page
    """
    return render_template('api_docs.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    video_url = request.form.get('video_url')
    # Get the analysis type from the form
    analysis_type = request.form.get('analysis_type', 'general')
    
    if not video_url:
        flash('Please enter a YouTube video URL', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Extract video ID from the URL
        parsed_url = urlparse(video_url)
        
        if 'youtube.com' in parsed_url.netloc:
            video_id = parse_qs(parsed_url.query).get('v', [None])[0]
        elif 'youtu.be' in parsed_url.netloc:
            video_id = parsed_url.path.strip('/')
        else:
            flash('Invalid YouTube URL format', 'danger')
            return redirect(url_for('index'))
        
        if not video_id:
            flash('Could not extract video ID from URL', 'danger')
            return redirect(url_for('index'))
        
        # Check if video has already been analyzed
        existing_analysis = VideoAnalysis.query.filter_by(video_id=video_id).first()
        if existing_analysis:
            # Redirect based on analysis type
            if analysis_type == 'creator':
                return redirect(url_for('creator_result', analysis_id=existing_analysis.id))
            else:
                return redirect(url_for('result', analysis_id=existing_analysis.id))
        
        # Get video info
        video_info = get_video_info(video_id)
        if not video_info:
            flash('Failed to retrieve video information', 'danger')
            return redirect(url_for('index'))
        
        # Get video transcript
        transcript = get_video_transcript(video_id)
        
        # Check if transcript is an error message (rather than None)
        is_error_message = transcript and transcript.startswith(("No transcript", "Unable to retrieve"))
        
        # Only proceed with analysis if we have a real transcript
        if not transcript or is_error_message:
            # Store basic info anyway, with the error message as transcript
            video_info = get_video_info(video_id)
            description = video_info.get('description', '')
            
            new_analysis = VideoAnalysis(
                video_id=video_id,
                title=video_info.get('title', f'Video {video_id}'),
                url=video_url,
                summary="Transcript analysis not available for this video.",
                key_points="No key points could be extracted without a transcript.",
                sentiment=0,
                duration_seconds=video_info.get('duration_seconds', 0),
                description=description,
                transcript=transcript or "No transcript available"
            )
            
            db.session.add(new_analysis)
            db.session.commit()
            
            flash('Transcript not available, but basic video information has been stored.', 'warning')
            return redirect(url_for('result', analysis_id=new_analysis.id))
        
        # Get video description
        description = video_info.get('description', '')
        
        # Analyze transcript with GPT for basic analysis
        analysis_result = analyze_transcript(transcript)
        summary = summarize_transcript(transcript)
        
        # Create base analysis object
        new_analysis = VideoAnalysis(
            video_id=video_id,
            title=video_info.get('title', 'Unknown Title'),
            url=video_url,
            summary=summary,
            key_points=analysis_result.get('key_points', ''),
            sentiment=analysis_result.get('sentiment', 0),
            duration_seconds=video_info.get('duration_seconds', 0),
            description=description,
            transcript=transcript
        )
        
        # Add specialized analysis based on the selected type
        if analysis_type == 'creator':
            # Analyze content creator focused content
            creator_analysis = analyze_creator_content(
                transcript=transcript,
                title=new_analysis.title,
                duration_seconds=new_analysis.duration_seconds
            )
            
            # Add creator data to the analysis object
            new_analysis.chapters = json.dumps(creator_analysis.get('chapters', []))
            new_analysis.quotable_moments = json.dumps(creator_analysis.get('quotable_moments', []))
            new_analysis.short_form_ideas = json.dumps(creator_analysis.get('short_form_ideas', []))
            new_analysis.social_media_captions = json.dumps(creator_analysis.get('social_media_captions', {}))
            new_analysis.recommended_hashtags = json.dumps(creator_analysis.get('recommended_hashtags', []))
            new_analysis.voiceover_script = creator_analysis.get('voiceover_script', '')
        
        # Save the analysis to the database
        db.session.add(new_analysis)
        db.session.commit()
        
        # Redirect based on analysis type
        if analysis_type == 'creator':
            return redirect(url_for('creator_result', analysis_id=new_analysis.id))
        else:
            return redirect(url_for('result', analysis_id=new_analysis.id))
        
    except Exception as e:
        logging.error(f"Error processing video: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/result/<int:analysis_id>')
def result(analysis_id):
    analysis = VideoAnalysis.query.get_or_404(analysis_id)
    return render_template('result.html', analysis=analysis)

@app.route('/dev/<int:analysis_id>')
def dev_result(analysis_id):
    """
    Render the developer-focused results page
    """
    analysis = VideoAnalysis.query.get_or_404(analysis_id)
    
    # Check if dev analysis has been performed
    if analysis.transcript and not analysis.code_snippets:
        # Perform dev analysis if not already done
        dev_analysis = analyze_dev_content(analysis.transcript)
        
        # Update the analysis record with the dev data
        analysis.is_dev_content = dev_analysis.get('is_dev_content', False)
        analysis.code_snippets = json.dumps(dev_analysis.get('code_snippets', []))
        analysis.dev_tools = json.dumps(dev_analysis.get('dev_tools', []))
        analysis.key_timestamps = json.dumps(dev_analysis.get('key_timestamps', []))
        
        db.session.commit()
        
    # Determine if this should display dev mode based on content
    is_dev_content = analysis.is_dev_content
    
    return render_template('dev_result.html', 
                          analysis=analysis,
                          is_dev_content=is_dev_content,
                          code_snippets=analysis.get_code_snippets(),
                          dev_tools=analysis.get_dev_tools(),
                          key_timestamps=analysis.get_key_timestamps())
                          
@app.route('/creator/<int:analysis_id>')
def creator_result(analysis_id):
    """
    Render the content creator focused results page
    """
    try:
        analysis = VideoAnalysis.query.get_or_404(analysis_id)
        
        # Check if creator analysis has been performed
        if analysis.transcript and not analysis.chapters:
            # Perform creator content analysis if not already done
            creator_analysis = analyze_creator_content(
                transcript=analysis.transcript, 
                title=analysis.title,
                duration_seconds=analysis.duration_seconds
            )
            
            # Update the analysis record with creator data
            analysis.chapters = json.dumps(creator_analysis.get('chapters', []))
            analysis.quotable_moments = json.dumps(creator_analysis.get('quotable_moments', []))
            analysis.short_form_ideas = json.dumps(creator_analysis.get('short_form_ideas', []))
            analysis.social_media_captions = json.dumps(creator_analysis.get('social_media_captions', {}))
            analysis.recommended_hashtags = json.dumps(creator_analysis.get('recommended_hashtags', []))
            analysis.voiceover_script = creator_analysis.get('voiceover_script', '')
            
            db.session.commit()
        
        # Get all data with proper error handling
        chapters = analysis.get_chapters() or []
        quotable_moments = analysis.get_quotable_moments() or []
        short_form_ideas = analysis.get_short_form_ideas() or []
        social_media_captions = analysis.get_social_media_captions() or {}
        hashtags = analysis.get_recommended_hashtags() or []
        
        return render_template('creator_result.html',
                            analysis=analysis,
                            chapters=chapters,
                            quotable_moments=quotable_moments,
                            short_form_ideas=short_form_ideas,
                            social_media_captions=social_media_captions,
                            hashtags=hashtags)
    except Exception as e:
        logging.error(f"Error in creator_result route: {str(e)}")
        return render_template('error.html', 
                            error_title="Creator Analysis Error", 
                            error_message=f"An error occurred while processing the creator analysis: {str(e)}")
                          
@app.route('/search/<int:analysis_id>')
def search_transcript(analysis_id):
    """
    Search within a video transcript
    """
    analysis = VideoAnalysis.query.get_or_404(analysis_id)
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('result', analysis_id=analysis_id))
    
    # Perform simple text search
    transcript = analysis.transcript or ""
    results = []
    
    if query and transcript:
        # Find all occurrences (case insensitive)
        import re
        matches = list(re.finditer(re.escape(query), transcript, re.IGNORECASE))
        
        # Create snippets around each match
        for match in matches:
            start = max(0, match.start() - 50)
            end = min(len(transcript), match.end() + 50)
            
            # Extract the snippet and highlight the match
            snippet = transcript[start:end]
            snippet = re.sub(
                f'({re.escape(query)})', 
                r'<mark>\1</mark>', 
                snippet, 
                flags=re.IGNORECASE
            )
            
            # Estimate timestamp based on position in transcript
            # This is approximate since we don't have actual timestamps
            position_ratio = match.start() / len(transcript)
            estimated_seconds = int(position_ratio * (analysis.duration_seconds or 0))
            
            results.append({
                'snippet': snippet,
                'timestamp': estimated_seconds
            })
    
    return render_template('search_results.html', 
                          analysis=analysis, 
                          query=query, 
                          results=results,
                          result_count=len(results))

@app.route('/export/<int:analysis_id>/<format>')
def export_analysis(analysis_id, format):
    """
    Export analysis in various formats
    """
    analysis = VideoAnalysis.query.get_or_404(analysis_id)
    
    # Determine what kind of content to export based on referer
    referer = request.headers.get('Referer', '')
    
    is_developer_content = '/dev/' in referer
    is_creator_content = '/creator/' in referer
    
    if format == 'markdown':
        # Generate markdown content
        from utils import generate_markdown
        
        # Generate markdown depending on content type
        if is_creator_content:
            markdown_content = generate_markdown(analysis, content_type='creator')
        elif is_developer_content:
            markdown_content = generate_markdown(analysis, content_type='developer')
        else:
            markdown_content = generate_markdown(analysis)
        
        # Create a text file to download
        buffer = io.BytesIO()
        buffer.write(markdown_content.encode('utf-8'))
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{analysis.video_id}_analysis.md",
            mimetype="text/markdown"
        )
        
    elif format == 'txt':
        # Generate plain text content
        from utils import generate_text
        
        # Generate text depending on content type
        if is_creator_content:
            text_content = generate_text(analysis, content_type='creator')
        elif is_developer_content:
            text_content = generate_text(analysis, content_type='developer')
        else:
            text_content = generate_text(analysis)
        
        # Create a text file to download
        buffer = io.BytesIO()
        buffer.write(text_content.encode('utf-8'))
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{analysis.video_id}_analysis.txt",
            mimetype="text/plain"
        )
        
    elif format == 'docx':
        # Generate Word document
        try:
            from utils import generate_docx
            
            # Generate docx depending on content type
            if is_creator_content:
                docx_buffer = generate_docx(analysis, content_type='creator')
            elif is_developer_content:
                docx_buffer = generate_docx(analysis, content_type='developer')
            else:
                docx_buffer = generate_docx(analysis)
            
            return send_file(
                docx_buffer,
                as_attachment=True,
                download_name=f"{analysis.video_id}_analysis.docx",
                mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except ImportError:
            # If python-docx is not installed
            flash('Word document export is not available. Please install the required dependencies.', 'warning')
            if is_creator_content:
                return redirect(url_for('creator_result', analysis_id=analysis_id))
            elif is_developer_content:
                return redirect(url_for('dev_result', analysis_id=analysis_id))
            else:
                return redirect(url_for('result', analysis_id=analysis_id))
        
    elif format == 'pdf':
        # For now, we'll implement a simplified PDF export
        # In a full implementation, you'd want to use a proper PDF library
        flash('PDF export is not yet implemented. Please use Markdown format.', 'warning')
        if is_creator_content:
            return redirect(url_for('creator_result', analysis_id=analysis_id))
        elif is_developer_content:
            return redirect(url_for('dev_result', analysis_id=analysis_id))
        else:
            return redirect(url_for('result', analysis_id=analysis_id))
            
    # Video download formats
    elif format in ['mp4', 'mp3', 'webm', 'audio']:
        resolution = request.args.get('resolution', '720p')
        video_format_id = request.args.get('video_format_id')
        audio_format_id = request.args.get('audio_format_id')
        
        # Basic progress tracking function to log progress (not used in this route)
        def progress_callback(progress_data):
            logging.debug(f"Download progress: {progress_data}")
        
        # Use the enhanced download_video function to get the video/audio
        download_info = download_video(
            analysis.video_id, 
            format_type=format, 
            resolution=resolution,
            video_format_id=video_format_id,
            audio_format_id=audio_format_id,
            progress_callback=progress_callback
        )
        
        if not download_info:
            flash(f'Failed to download video in {format} format', 'danger')
            if is_creator_content:
                return redirect(url_for('creator_result', analysis_id=analysis_id))
            else:
                return redirect(url_for('result', analysis_id=analysis_id))
        
        file_path, file_name, mime_type = download_info
        
        # Send the file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file_name,
            mimetype=mime_type
        )
        
    else:
        # Default redirect based on content type
        if is_creator_content:
            return redirect(url_for('creator_result', analysis_id=analysis_id))
        elif is_developer_content:
            return redirect(url_for('dev_result', analysis_id=analysis_id))
        else:
            return redirect(url_for('result', analysis_id=analysis_id))

# Define a function to clean transcript text
def clean_transcript(transcript):
    """
    Clean transcript text by removing WEBVTT markers, timestamps, and formatting
    
    Args:
        transcript: Raw transcript text
        
    Returns:
        Cleaned transcript text
    """
    if not transcript:
        return ""
    
    # Dictionary to track unique content
    unique_content = {}
    
    # Remove WEBVTT header and metadata
    lines = transcript.split('\n')
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

@app.route('/api/video/<video_id>', methods=['GET'])
def api_video(video_id):
    """
    API endpoint to get video information and transcript
    Returns JSON with title, views, and transcript (no AI analysis)
    """
    # Log the request
    logging.info(f"API request received for video ID: {video_id}")
    
    try:
        # Validate the video ID format
        if not video_id or len(video_id) != 11:
            logging.warning(f"Invalid video ID format: {video_id}")
            return jsonify({
                'error': 'Invalid YouTube video ID. Must be 11 characters.',
                'video_id': video_id
            }), 400
        
        # Check if video data exists in database
        existing_analysis = VideoAnalysis.query.filter_by(video_id=video_id).first()
        
        if existing_analysis and existing_analysis.transcript:
            # Return existing transcript data without any analysis
            return jsonify({
                'title': existing_analysis.title,
                'views': 0,  # Default to 0 if not available in the database
                'transcript': existing_analysis.transcript
            }), 200
            
        # Get video info
        video_info = get_video_info(video_id)
        if not video_info:
            return jsonify({
                'error': 'Failed to retrieve video information',
                'video_id': video_id
            }), 404
        
        # Get video transcript
        transcript = get_video_transcript(video_id)
        
        # Clean the transcript
        if transcript:
            transcript = clean_transcript(transcript)
        
        # Return simple response with just the transcript
        return jsonify({
            'title': video_info.get('title', f'Video {video_id}'),
            'views': video_info.get('views', 0),
            'transcript': transcript or "No transcript available"
        }), 200
            
    except Exception as e:
        logging.error(f"API Error processing video {video_id}: {str(e)}")
        return jsonify({
            'error': str(e),
            'title': f'Error processing video {video_id}',
            'views': 0,
            'transcript': 'Error retrieving transcript',
            'summary': f'Error: {str(e)}'
        }), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message='Page not found'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500

@app.route('/api/dev-summary/<video_id>', methods=['GET'])
def api_dev_summary(video_id):
    """
    API endpoint for developer-focused video analysis
    Returns JSON with title, code snippets, dev tools, and key timestamps
    """
    # Log the request
    logging.info(f"Developer API request received for video ID: {video_id}")
    
    try:
        # Validate the video ID format
        if not video_id or len(video_id) != 11:
            logging.warning(f"Invalid video ID format: {video_id}")
            return jsonify({
                'error': 'Invalid YouTube video ID. Must be 11 characters.',
                'video_id': video_id
            }), 400
        
        # Check if video has already been analyzed
        existing_analysis = VideoAnalysis.query.filter_by(video_id=video_id).first()
        
        if existing_analysis:
            # If developer analysis wasn't performed, do it now
            if existing_analysis.transcript and not existing_analysis.code_snippets:
                dev_analysis = analyze_dev_content(existing_analysis.transcript)
                
                # Update the record
                existing_analysis.is_dev_content = dev_analysis.get('is_dev_content', False)
                existing_analysis.code_snippets = json.dumps(dev_analysis.get('code_snippets', []))
                existing_analysis.dev_tools = json.dumps(dev_analysis.get('dev_tools', []))
                existing_analysis.key_timestamps = json.dumps(dev_analysis.get('key_timestamps', []))
                
                db.session.commit()
            
            # Return developer-focused analysis
            return jsonify({
                'title': existing_analysis.title,
                'is_dev_content': existing_analysis.is_dev_content,
                'code_snippets': existing_analysis.get_code_snippets(),
                'dev_tools': existing_analysis.get_dev_tools(),
                'key_timestamps': existing_analysis.get_key_timestamps()
            }), 200
            
        # If no existing analysis, get and analyze the video
        video_info = get_video_info(video_id)
        if not video_info:
            return jsonify({
                'error': 'Failed to retrieve video information',
                'video_id': video_id
            }), 404
        
        # Get video transcript
        transcript = get_video_transcript(video_id)
        
        # Check if transcript is an error message
        is_error_message = transcript and transcript.startswith(("No transcript", "Unable to retrieve"))
        
        # If no valid transcript, return error
        if not transcript or is_error_message:
            return jsonify({
                'title': video_info.get('title', f'Video {video_id}'),
                'is_dev_content': False,
                'code_snippets': [],
                'dev_tools': [],
                'key_timestamps': [],
                'error': 'No valid transcript available for analysis'
            }), 200
        
        # Basic analysis 
        summary = summarize_transcript(transcript)
        analysis_result = analyze_transcript(transcript)
        
        # Developer-focused analysis
        dev_analysis = analyze_dev_content(transcript)
        
        # Save to database
        new_analysis = VideoAnalysis(
            video_id=video_id,
            title=video_info.get('title', 'Unknown Title'),
            url=f"https://www.youtube.com/watch?v={video_id}",
            summary=summary,
            key_points=analysis_result.get('key_points', ''),
            sentiment=analysis_result.get('sentiment', 0),
            duration_seconds=video_info.get('duration_seconds', 0),
            description=video_info.get('description', ''),
            transcript=transcript,
            is_dev_content=dev_analysis.get('is_dev_content', False),
            code_snippets=json.dumps(dev_analysis.get('code_snippets', [])),
            dev_tools=json.dumps(dev_analysis.get('dev_tools', [])),
            key_timestamps=json.dumps(dev_analysis.get('key_timestamps', []))
        )
        
        db.session.add(new_analysis)
        db.session.commit()
        
        # Return dev-focused response
        return jsonify({
            'title': new_analysis.title,
            'is_dev_content': new_analysis.is_dev_content,
            'code_snippets': new_analysis.get_code_snippets(),
            'dev_tools': new_analysis.get_dev_tools(),
            'key_timestamps': new_analysis.get_key_timestamps()
        }), 200
            
    except Exception as e:
        logging.error(f"API Error processing dev summary for video {video_id}: {str(e)}")
        return jsonify({
            'error': str(e),
            'title': f'Error processing video {video_id}',
            'is_dev_content': False,
            'code_snippets': [],
            'dev_tools': [],
            'key_timestamps': []
        }), 500

@app.route('/api/creator-summary/<video_id>', methods=['GET'])
def api_creator_summary(video_id):
    """
    API endpoint for content creator tools
    Returns JSON with chapters, quotes, short-form ideas, etc.
    """
    logging.info(f"Creator API request received for video ID: {video_id}")
    
    try:
        # Validate the video ID format
        if not video_id or len(video_id) != 11:
            logging.warning(f"Invalid video ID format: {video_id}")
            return jsonify({
                'error': 'Invalid YouTube video ID. Must be 11 characters.',
                'video_id': video_id
            }), 400
        
        # Check if video has already been analyzed
        existing_analysis = VideoAnalysis.query.filter_by(video_id=video_id).first()
        
        if existing_analysis:
            # If creator analysis wasn't performed, do it now
            if existing_analysis.transcript and not existing_analysis.chapters:
                creator_analysis = analyze_creator_content(
                    transcript=existing_analysis.transcript,
                    title=existing_analysis.title,
                    duration_seconds=existing_analysis.duration_seconds
                )
                
                # Update the record
                existing_analysis.chapters = json.dumps(creator_analysis.get('chapters', []))
                existing_analysis.quotable_moments = json.dumps(creator_analysis.get('quotable_moments', []))
                existing_analysis.short_form_ideas = json.dumps(creator_analysis.get('short_form_ideas', []))
                existing_analysis.social_media_captions = json.dumps(creator_analysis.get('social_media_captions', {}))
                existing_analysis.recommended_hashtags = json.dumps(creator_analysis.get('recommended_hashtags', []))
                existing_analysis.voiceover_script = creator_analysis.get('voiceover_script', '')
                
                db.session.commit()
            
            # Return creator-focused analysis
            return jsonify({
                'title': existing_analysis.title,
                'chapters': existing_analysis.get_chapters(),
                'quotable_moments': existing_analysis.get_quotable_moments(),
                'short_form_ideas': existing_analysis.get_short_form_ideas(),
                'social_media_captions': existing_analysis.get_social_media_captions(),
                'recommended_hashtags': existing_analysis.get_recommended_hashtags(),
                'voiceover_script': existing_analysis.voiceover_script
            }), 200
            
        # If no existing analysis, get and analyze the video
        video_info = get_video_info(video_id)
        if not video_info:
            return jsonify({
                'error': 'Failed to retrieve video information',
                'video_id': video_id
            }), 404
        
        # Get video transcript
        transcript = get_video_transcript(video_id)
        
        # Check if transcript is an error message
        is_error_message = transcript and transcript.startswith(("No transcript", "Unable to retrieve"))
        
        # If no valid transcript, return error
        if not transcript or is_error_message:
            return jsonify({
                'title': video_info.get('title', f'Video {video_id}'),
                'chapters': [],
                'quotable_moments': [],
                'short_form_ideas': [],
                'social_media_captions': {},
                'recommended_hashtags': [],
                'voiceover_script': '',
                'error': 'No valid transcript available for analysis'
            }), 200
        
        # Basic analysis 
        summary = summarize_transcript(transcript)
        analysis_result = analyze_transcript(transcript)
        
        # Create a new analysis object to store in DB
        new_analysis = VideoAnalysis(
            video_id=video_id,
            title=video_info.get('title', 'Unknown Title'),
            url=f"https://www.youtube.com/watch?v={video_id}",
            summary=summary,
            key_points=analysis_result.get('key_points', ''),
            sentiment=analysis_result.get('sentiment', 0),
            duration_seconds=video_info.get('duration_seconds', 0),
            description=video_info.get('description', ''),
            transcript=transcript
        )
        
        # Creator-focused analysis
        creator_analysis = analyze_creator_content(
            transcript=transcript,
            title=new_analysis.title,
            duration_seconds=new_analysis.duration_seconds
        )
        
        # Update with creator data
        new_analysis.chapters = json.dumps(creator_analysis.get('chapters', []))
        new_analysis.quotable_moments = json.dumps(creator_analysis.get('quotable_moments', []))
        new_analysis.short_form_ideas = json.dumps(creator_analysis.get('short_form_ideas', []))
        new_analysis.social_media_captions = json.dumps(creator_analysis.get('social_media_captions', {}))
        new_analysis.recommended_hashtags = json.dumps(creator_analysis.get('recommended_hashtags', []))
        new_analysis.voiceover_script = creator_analysis.get('voiceover_script', '')
        
        db.session.add(new_analysis)
        db.session.commit()
        
        # Return creator-focused response
        return jsonify({
            'title': new_analysis.title,
            'chapters': new_analysis.get_chapters(),
            'quotable_moments': new_analysis.get_quotable_moments(),
            'short_form_ideas': new_analysis.get_short_form_ideas(),
            'social_media_captions': new_analysis.get_social_media_captions(),
            'recommended_hashtags': new_analysis.get_recommended_hashtags(),
            'voiceover_script': new_analysis.voiceover_script
        }), 200
            
    except Exception as e:
        logging.error(f"API Error processing creator summary for video {video_id}: {str(e)}")
        return jsonify({
            'error': str(e),
            'title': f'Error processing video {video_id}',
            'chapters': [],
            'quotable_moments': [],
            'short_form_ideas': [],
            'social_media_captions': {},
            'recommended_hashtags': [],
            'voiceover_script': ''
        }), 500
        
@app.route('/api/video_formats/<video_id>')
def api_video_formats(video_id):
    """
    API endpoint to get all available video formats
    Returns JSON with various format options
    """
    # Get all available formats
    formats = get_video_formats(video_id)
    
    if not formats:
        return jsonify({'error': 'Could not retrieve video formats'}), 404
        
    return jsonify(formats)
    
@app.route('/download/<video_id>')
def download_video_page(video_id):
    """
    Page to display advanced download options for a video
    """
    # Get video info
    video_info = get_video_info(video_id)
    if not video_info:
        flash('Could not retrieve video information', 'danger')
        return redirect(url_for('index'))
        
    # Get all available formats
    formats = get_video_formats(video_id)
    if not formats:
        flash('Could not retrieve video formats', 'warning')
        # Create a minimal format structure
        formats = {
            'info': video_info,
            'preset_formats': [
                {'label': 'HD (720p)', 'value': '720'},
                {'label': 'SD (480p)', 'value': '480'},
                {'label': '360p', 'value': '360'},
                {'label': 'Audio only (MP3)', 'value': 'mp3'}
            ]
        }
    
    return render_template('download.html', 
                           video_id=video_id,
                           video_info=video_info,
                           formats=formats)
                           
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

@app.route('/api/download/<video_id>', methods=['POST'])
def api_download_video(video_id):
    """
    API endpoint to download a video with specific format parameters
    """
    data = request.json
    
    format_type = data.get('format_type', 'mp4')
    resolution = data.get('resolution', '720p')
    video_format_id = data.get('video_format_id')
    audio_format_id = data.get('audio_format_id')
    
    # Download function does not include progress tracking yet
    download_info = download_video(
        video_id, 
        format_type=format_type, 
        resolution=resolution,
        video_format_id=video_format_id,
        audio_format_id=audio_format_id
    )
    
    if not download_info:
        return jsonify({
            'success': False,
            'message': f'Failed to download video in {format_type} format'
        }), 500
    
    file_path, file_name, mime_type = download_info
    
    # Return success with information about the download
    # The actual file will be served by a separate endpoint
    return jsonify({
        'success': True,
        'file_name': file_name,
        'mime_type': mime_type,
        'download_url': url_for('download_file', video_id=video_id, file_name=file_name)
    })
    
@app.route('/download/file/<video_id>/<file_name>')
def download_file(video_id, file_name):
    """
    Serve a downloaded file to the user
    """
    # This is a simplified version - in reality, we'd need to store the file path
    # Potentially in a database or a temporary session variable
    
    # For now, we'll re-download the file based on the format extension
    format_type = 'mp4'
    resolution = '720p'
    
    if file_name.endswith('.mp3'):
        format_type = 'mp3'
    elif file_name.endswith('.webm'):
        format_type = 'webm'
    
    # Extract resolution from query parameters if available
    if request.args.get('resolution'):
        resolution = request.args.get('resolution')
    
    # Download the file again (not ideal, but works for demo)
    download_info = download_video(video_id, format_type=format_type, resolution=resolution)
    
    if not download_info:
        flash(f'Failed to download video', 'danger')
        return redirect(url_for('result', analysis_id=request.args.get('analysis_id', 1)))
    
    file_path, _, mime_type = download_info
    
    # Send the file
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file_name,
        mimetype=mime_type
    )
