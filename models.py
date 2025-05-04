from datetime import datetime
import json
from app import db

class VideoAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(20), nullable=False, index=True)
    title = db.Column(db.String(255))
    url = db.Column(db.String(255), nullable=False)
    summary = db.Column(db.Text)
    key_points = db.Column(db.Text)
    sentiment = db.Column(db.Float)
    duration_seconds = db.Column(db.Integer)
    description = db.Column(db.Text)
    transcript = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Developer-focused fields
    code_snippets = db.Column(db.Text)  # Stored as JSON string of {language, code, timestamp} objects
    dev_tools = db.Column(db.Text)  # Stored as JSON string of {tool, mentions, timestamps} objects
    key_timestamps = db.Column(db.Text)  # Stored as JSON string of {action, timestamp, description} objects
    is_dev_content = db.Column(db.Boolean, default=False)  # Flag if content is dev-related
    
    # Content creator fields
    chapters = db.Column(db.Text)  # Stored as JSON string of {title, timestamp, content} objects
    quotable_moments = db.Column(db.Text)  # Stored as JSON string of {quote, timestamp, emotion} objects
    short_form_ideas = db.Column(db.Text)  # Stored as JSON string of {title, hook, description, timestamp} objects
    social_media_captions = db.Column(db.Text)  # Stored as JSON string with different platform captions
    recommended_hashtags = db.Column(db.Text)  # Stored as JSON array of hashtag strings
    voiceover_script = db.Column(db.Text)  # Clean script suitable for voiceover recording
    translations = db.Column(db.Text)  # Stored as JSON object with language codes as keys
    
    def __repr__(self):
        return f'<VideoAnalysis {self.video_id}>'
        
    def get_code_snippets(self):
        """Return code snippets as Python objects"""
        if not self.code_snippets:
            return []
        try:
            return json.loads(self.code_snippets)
        except:
            return []
            
    def get_dev_tools(self):
        """Return dev tools as Python objects"""
        if not self.dev_tools:
            return []
        try:
            return json.loads(self.dev_tools)
        except:
            return []
            
    def get_key_timestamps(self):
        """Return key timestamps as Python objects"""
        if not self.key_timestamps:
            return []
        try:
            return json.loads(self.key_timestamps)
        except:
            return []
    
    def get_chapters(self):
        """Return chapters as Python objects"""
        if not self.chapters:
            return []
        try:
            return json.loads(self.chapters)
        except:
            return []
    
    def get_quotable_moments(self):
        """Return quotable moments as Python objects"""
        if not self.quotable_moments:
            return []
        try:
            return json.loads(self.quotable_moments)
        except:
            return []
    
    def get_short_form_ideas(self):
        """Return short-form content ideas as Python objects"""
        if not self.short_form_ideas:
            return []
        try:
            return json.loads(self.short_form_ideas)
        except:
            return []
    
    def get_social_media_captions(self):
        """Return social media captions as Python objects"""
        if not self.social_media_captions:
            return {}
        try:
            return json.loads(self.social_media_captions)
        except:
            return {}
    
    def get_recommended_hashtags(self):
        """Return recommended hashtags as Python list"""
        if not self.recommended_hashtags:
            return []
        try:
            return json.loads(self.recommended_hashtags)
        except:
            return []
    
    def get_translations(self):
        """Return translations as Python dict"""
        if not self.translations:
            return {}
        try:
            return json.loads(self.translations)
        except:
            return {}
            
    def to_dev_json(self):
        """Convert to developer-focused JSON representation"""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'title': self.title,
            'url': self.url,
            'summary': self.summary,
            'duration_seconds': self.duration_seconds,
            'code_snippets': self.get_code_snippets(),
            'dev_tools': self.get_dev_tools(),
            'key_timestamps': self.get_key_timestamps(),
            'is_dev_content': self.is_dev_content
        }
        
    def to_creator_json(self):
        """Convert to content creator-focused JSON representation"""
        return {
            'id': self.id,
            'video_id': self.video_id,
            'title': self.title,
            'url': self.url,
            'summary': self.summary,
            'duration_seconds': self.duration_seconds,
            'chapters': self.get_chapters(),
            'quotable_moments': self.get_quotable_moments(),
            'short_form_ideas': self.get_short_form_ideas(),
            'social_media_captions': self.get_social_media_captions(),
            'recommended_hashtags': self.get_recommended_hashtags(),
            'voiceover_script': self.voiceover_script
        }
