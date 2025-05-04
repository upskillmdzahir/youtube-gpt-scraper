import re  # Required for regex operations

# Path to the file with the transcript
transcript_file = "attached_assets/Pasted-Kind-captions-Language-en-line-76-PRESIDENT-TRUMP-TO-AIR-TOMORROW-line-76-PRESIDENT-TR-1746374918353.txt"

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

# Read the transcript
with open(transcript_file, 'r') as f:
    transcript_text = f.read()

# Clean the transcript
cleaned_transcript = clean_transcript(transcript_text)

# Print the original and cleaned versions for comparison
print("=== ORIGINAL TRANSCRIPT (first 300 chars) ===")
print(transcript_text[:300])
print("\n\n=== CLEANED TRANSCRIPT ===")
print(cleaned_transcript)
print("\n\nWord count in original:", len(transcript_text.split()))
print("Word count in cleaned:", len(cleaned_transcript.split()))
print("Character count in original:", len(transcript_text))
print("Character count in cleaned:", len(cleaned_transcript))