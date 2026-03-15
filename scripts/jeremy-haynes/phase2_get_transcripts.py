#!/usr/bin/env python3
"""
PHASE 2: YouTube Transcript Extractor
Reads your edited video_list.csv and extracts transcripts for included videos.

Usage: python3 phase2_get_transcripts.py
"""

import csv
import re
import sys
import time
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi

# Configuration
OUTPUT_DIR = Path("./jeremy_haynes_transcripts")
VIDEO_LIST = OUTPUT_DIR / "video_list_filtered.csv"

def clean_transcript(transcript_data):
    """Convert transcript data to clean readable text."""
    # Join all text segments
    raw_text = ' '.join([entry['text'] for entry in transcript_data])
    
    # Clean up common issues
    text = raw_text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
    text = text.strip()
    
    # Add basic sentence structure (capitalize after periods)
    sentences = text.split('. ')
    sentences = [s.capitalize() for s in sentences]
    text = '. '.join(sentences)
    
    # Break into paragraphs (roughly every 4-5 sentences for readability)
    words = text.split()
    paragraphs = []
    current = []
    sentence_count = 0
    
    for word in words:
        current.append(word)
        if word.endswith('.') or word.endswith('?') or word.endswith('!'):
            sentence_count += 1
            if sentence_count >= 5:
                paragraphs.append(' '.join(current))
                current = []
                sentence_count = 0
    
    if current:
        paragraphs.append(' '.join(current))
    
    return '\n\n'.join(paragraphs)

def get_transcript(video_id, title):
    """Fetch and clean transcript for a video."""
    try:
        api = YouTubeTranscriptApi()
        result = api.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
        transcript_data = result.to_raw_data()
        return clean_transcript(transcript_data)
    except Exception as e:
        return None, str(e)

def load_video_list():
    """Load videos marked for inclusion from CSV."""
    videos = []
    
    with open(VIDEO_LIST, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['include'].strip().upper() == 'YES':
                videos.append({
                    'video_id': row['video_id'],
                    'title': row['title'],
                    'category': row.get('category', '').strip(),
                    'duration': row.get('duration_mins', '')
                })
    
    return videos

def sanitize_filename(title):
    """Convert title to safe filename."""
    # Remove/replace problematic characters
    safe = re.sub(r'[<>:"/\\|?*]', '', title)
    safe = re.sub(r'\s+', '_', safe)
    safe = safe[:80]  # Limit length
    return safe

def main():
    print("=" * 60)
    print("PHASE 2: EXTRACT TRANSCRIPTS")
    print("=" * 60)
    
    if not VIDEO_LIST.exists():
        print(f"\n❌ Error: {VIDEO_LIST} not found!")
        print("Run phase1_get_videos.py first.")
        sys.exit(1)
    
    videos = load_video_list()
    print(f"\n✓ Found {len(videos)} videos marked for inclusion\n")
    
    # Create output directories
    transcripts_dir = OUTPUT_DIR / "transcripts"
    transcripts_dir.mkdir(exist_ok=True)
    
    # Group by category
    by_category_dir = OUTPUT_DIR / "by_category"
    by_category_dir.mkdir(exist_ok=True)
    
    success_count = 0
    failed = []
    category_content = {}
    
    print("Extracting transcripts...")
    print("-" * 60)
    
    for i, video in enumerate(videos, 1):
        video_id = video['video_id']
        title = video['title']
        category = video['category'] or 'Uncategorized'
        
        print(f"[{i}/{len(videos)}] {title[:50]}...", end=" ")
        
        result = get_transcript(video_id, title)

        if isinstance(result, tuple):
            # Error case
            print(f"❌ {result[1][:80]}")
            failed.append({'title': title, 'reason': result[1]})
            time.sleep(3)
            continue

        # Success - save individual file
        filename = f"{sanitize_filename(title)}.txt"
        filepath = transcripts_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"TITLE: {title}\n")
            f.write(f"VIDEO: https://www.youtube.com/watch?v={video_id}\n")
            f.write(f"CATEGORY: {category}\n")
            f.write("=" * 60 + "\n\n")
            f.write(result)
        
        # Add to category compilation
        if category not in category_content:
            category_content[category] = []
        category_content[category].append({
            'title': title,
            'video_id': video_id,
            'transcript': result
        })
        
        success_count += 1
        print("✓")

        # Rate limit: wait 3 seconds between requests
        time.sleep(3)
    
    # Save category compilations
    print("\nCreating category compilations...")
    for category, items in category_content.items():
        safe_cat = sanitize_filename(category)
        cat_file = by_category_dir / f"{safe_cat}.txt"
        
        with open(cat_file, 'w', encoding='utf-8') as f:
            f.write(f"CATEGORY: {category}\n")
            f.write(f"Videos: {len(items)}\n")
            f.write("=" * 60 + "\n\n")
            
            for item in items:
                f.write(f"\n{'#' * 60}\n")
                f.write(f"# {item['title']}\n")
                f.write(f"# https://www.youtube.com/watch?v={item['video_id']}\n")
                f.write(f"{'#' * 60}\n\n")
                f.write(item['transcript'])
                f.write("\n\n")
        
        print(f"  ✓ {category}: {len(items)} videos")
    
    # Create master document
    print("\nCreating master compilation...")
    master_file = OUTPUT_DIR / "ALL_TRANSCRIPTS.txt"
    
    with open(master_file, 'w', encoding='utf-8') as f:
        f.write("JEREMY HAYNES - COMPLETE TRANSCRIPT LIBRARY\n")
        f.write(f"Total videos: {success_count}\n")
        f.write("=" * 60 + "\n\n")
        
        for category, items in sorted(category_content.items()):
            f.write(f"\n{'#' * 60}\n")
            f.write(f"# CATEGORY: {category.upper()}\n")
            f.write(f"{'#' * 60}\n\n")
            
            for item in items:
                f.write(f"\n{'-' * 60}\n")
                f.write(f"## {item['title']}\n")
                f.write(f"URL: https://www.youtube.com/watch?v={item['video_id']}\n")
                f.write(f"{'-' * 60}\n\n")
                f.write(item['transcript'])
                f.write("\n\n")
    
    # Summary
    print(f"\n{'=' * 60}")
    print("COMPLETE!")
    print("=" * 60)
    print(f"  ✓ Transcripts extracted: {success_count}")
    print(f"  ✗ Failed: {len(failed)}")
    print(f"\n  Output location: {OUTPUT_DIR.absolute()}")
    print(f"\n  Files created:")
    print(f"    - transcripts/         (individual files)")
    print(f"    - by_category/         (grouped by category)")
    print(f"    - ALL_TRANSCRIPTS.txt  (master document)")
    
    if failed:
        failed_file = OUTPUT_DIR / "failed_videos.txt"
        with open(failed_file, 'w', encoding='utf-8') as f:
            for item in failed:
                f.write(f"{item['title']}: {item['reason']}\n")
        print(f"    - failed_videos.txt    (list of failures)")
    
    print(f"\n{'=' * 60}")
    print("NEXT: Upload ALL_TRANSCRIPTS.txt to a Claude Project")
    print("=" * 60)

if __name__ == "__main__":
    main()
