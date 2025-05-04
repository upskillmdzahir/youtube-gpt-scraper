import logging
from app import app, db
from models import VideoAnalysis

def add_column(column_name, column_type):
    """Add a column to the video_analysis table if it doesn't exist"""
    try:
        with db.engine.connect() as connection:
            connection.execute(db.text(
                f"ALTER TABLE video_analysis ADD COLUMN IF NOT EXISTS {column_name} {column_type}"
            ))
            connection.commit()
            print(f"Added column {column_name} with type {column_type}")
    except Exception as e:
        print(f"Error adding column {column_name}: {str(e)}")
        
def update_database():
    """Update database schema to include all required columns"""
    print("Updating database schema...")
    
    # Developer-focused columns
    add_column("code_snippets", "TEXT")
    add_column("dev_tools", "TEXT")
    add_column("key_timestamps", "TEXT")
    add_column("is_dev_content", "BOOLEAN DEFAULT FALSE")
    
    # Content creator columns
    add_column("chapters", "TEXT")
    add_column("quotable_moments", "TEXT")
    add_column("short_form_ideas", "TEXT")
    add_column("social_media_captions", "TEXT")
    add_column("recommended_hashtags", "TEXT")
    add_column("voiceover_script", "TEXT")
    add_column("translations", "TEXT")
    
    print("Database schema update completed!")

if __name__ == "__main__":
    with app.app_context():
        update_database()