#!/usr/bin/env python3
"""
PHASE 1: YouTube Channel Video List Extractor
Run this with Claude Code on your machine.

Usage: python3 phase1_get_videos.py
"""

import subprocess
import sys
import csv
from pathlib import Path

# Install required packages
def install_packages():
    print("Installing required packages...")
    packages = ['yt-dlp', 'youtube-transcript-api']
    for package in packages:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-q'])
    print("Done.\n")

install_packages()

from yt_dlp import YoutubeDL

# Configuration
CHANNEL_URL = "https://www.youtube.com/@JeremyHaynesTraining/videos"
OUTPUT_DIR = Path("./jeremy_haynes_transcripts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_channel_videos(channel_url):
    """Extract all video metadata from a YouTube channel."""
    print(f"Fetching video list from channel...")
    print("(This may take 1-2 minutes for 200+ videos)\n")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
    }
    
    videos = []
    
    with YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(channel_url, download=False)
        
        if 'entries' in result:
            for entry in result['entries']:
                if entry:
                    videos.append({
                        'video_id': entry.get('id', ''),
                        'title': entry.get('title', ''),
                        'url': f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                        'duration': entry.get('duration', 0),
                    })
    
    return videos

def save_video_list(videos, filename):
    """Save video list to CSV for review."""
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'include', 'video_id', 'title', 'duration_mins', 'url', 'category'
        ])
        writer.writeheader()
        
        for v in videos:
            duration_mins = round(v['duration'] / 60, 1) if v['duration'] else 0
            writer.writerow({
                'include': 'YES',  # Default YES - change to NO to skip
                'video_id': v['video_id'],
                'title': v['title'],
                'duration_mins': duration_mins,
                'url': v['url'],
                'category': ''  # Optional: Funnels, Ads, Sales, Agency, Offers, Mindset
            })
    
    return filepath

def main():
    print("=" * 60)
    print("PHASE 1: EXTRACT VIDEO LIST")
    print("=" * 60)
    
    videos = get_channel_videos(CHANNEL_URL)
    print(f"✓ Found {len(videos)} videos\n")
    
    csv_path = save_video_list(videos, "video_list.csv")
    print(f"✓ Saved to: {csv_path}")
    
    # Calculate total duration
    total_mins = sum(v['duration']/60 for v in videos if v['duration'])
    total_hours = round(total_mins / 60, 1)
    
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print("=" * 60)
    print(f"  Videos: {len(videos)}")
    print(f"  Total duration: ~{total_hours} hours")
    print(f"  Output file: {csv_path}")
    
    print(f"\n{'=' * 60}")
    print("NEXT STEPS")
    print("=" * 60)
    print("""
1. Open video_list.csv in Excel/Sheets/Numbers
2. Review titles - change 'include' to 'NO' for videos to skip
3. Optionally add categories (Funnels, Ads, Sales, Agency, etc.)
4. Save the file
5. Run phase2_get_transcripts.py
""")
    
    # Show sample
    print("Sample of videos found:")
    print("-" * 60)
    for v in videos[:15]:
        dur = f"{round(v['duration']/60)}min" if v['duration'] else "?"
        title = v['title'][:55] + "..." if len(v['title']) > 55 else v['title']
        print(f"  [{dur:>5}] {title}")
    
    if len(videos) > 15:
        print(f"\n  ... and {len(videos) - 15} more videos")

if __name__ == "__main__":
    main()
