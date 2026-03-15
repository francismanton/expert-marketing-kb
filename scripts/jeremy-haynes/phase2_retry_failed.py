#!/usr/bin/env python3
"""
PHASE 2 RETRY: Re-attempt failed transcript downloads.
Reads failed_videos.txt and video_list_filtered.csv to retry only the failed videos.
Includes a 3-second delay between requests to avoid rate limiting.

Usage: python3 phase2_retry_failed.py
"""

import csv
import re
import sys
import time
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi

# Configuration
OUTPUT_DIR = Path("./jeremy_haynes_transcripts")
FAILED_FILE = OUTPUT_DIR / "failed_videos.txt"
VIDEO_LIST = OUTPUT_DIR / "video_list_filtered.csv"
DELAY_SECONDS = 5


def clean_transcript(transcript_data):
    """Convert transcript data to clean readable text."""
    raw_text = ' '.join([entry['text'] for entry in transcript_data])
    text = raw_text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    sentences = text.split('. ')
    sentences = [s.capitalize() for s in sentences]
    text = '. '.join(sentences)

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


def get_transcript(video_id):
    """Fetch and clean transcript for a video."""
    try:
        api = YouTubeTranscriptApi()
        result = api.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
        transcript_data = result.to_raw_data()
        return clean_transcript(transcript_data)
    except Exception as e:
        return None, str(e)


def sanitize_filename(title):
    """Convert title to safe filename."""
    safe = re.sub(r'[<>:"/\\|?*]', '', title)
    safe = re.sub(r'\s+', '_', safe)
    safe = safe[:80]
    return safe


def load_failed_titles():
    """Parse failed_videos.txt to extract video titles."""
    titles = set()
    with open(FAILED_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Skip error message continuation lines
            if line.startswith(('YouTube is', 'Ways to work', '- You', 'If you are sure',
                                'Could not retrieve')):
                continue
            if ':' in line and len(line.split(':')[0]) > 10:
                title = line.split(': ')[0].rstrip(':')
                if len(title) > 10:
                    titles.add(title)
    return titles


def load_video_data_for_titles(failed_titles):
    """Load full video data from CSV for the failed titles."""
    videos = []
    with open(VIDEO_LIST, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['title'].rstrip(':') in failed_titles or row['title'] in failed_titles:
                videos.append({
                    'video_id': row['video_id'],
                    'title': row['title'],
                    'category': row.get('category', '').strip(),
                })
    return videos


def main():
    print("=" * 60)
    print("PHASE 2 RETRY: RE-ATTEMPT FAILED TRANSCRIPTS")
    print("=" * 60)

    if not FAILED_FILE.exists():
        print(f"\n❌ Error: {FAILED_FILE} not found!")
        print("No failed videos to retry.")
        sys.exit(1)

    # Load failed titles and match to video data
    failed_titles = load_failed_titles()
    print(f"\n✓ Found {len(failed_titles)} failed titles in failed_videos.txt")

    videos = load_video_data_for_titles(failed_titles)
    print(f"✓ Matched {len(videos)} videos from CSV")

    if not videos:
        print("\n❌ Could not match any failed titles to CSV entries.")
        print("Try running phase2_get_transcripts.py again instead.")
        sys.exit(1)

    # Setup directories
    transcripts_dir = OUTPUT_DIR / "transcripts"
    transcripts_dir.mkdir(exist_ok=True)

    success_count = 0
    still_failed = []

    est_minutes = round(len(videos) * DELAY_SECONDS / 60, 1)
    print(f"\nRetrying {len(videos)} videos with {DELAY_SECONDS}s delay (~{est_minutes} min)...")
    print("-" * 60)

    for i, video in enumerate(videos, 1):
        video_id = video['video_id']
        title = video['title']
        category = video['category'] or 'Uncategorized'

        print(f"[{i}/{len(videos)}] {title[:50]}...", end=" ", flush=True)

        result = get_transcript(video_id)

        if isinstance(result, tuple):
            print(f"❌ {result[1][:80]}")
            still_failed.append({'title': title, 'video_id': video_id, 'reason': result[1]})
            time.sleep(DELAY_SECONDS)
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

        success_count += 1
        print("✓")

        time.sleep(DELAY_SECONDS)

    # Rebuild ALL_TRANSCRIPTS.txt by reading all individual transcript files
    print("\nRebuilding master compilation from all transcript files...")
    all_transcripts = []
    for txt_file in sorted(transcripts_dir.glob("*.txt")):
        content = txt_file.read_text(encoding='utf-8')
        all_transcripts.append(content)

    master_file = OUTPUT_DIR / "ALL_TRANSCRIPTS.txt"
    with open(master_file, 'w', encoding='utf-8') as f:
        f.write("JEREMY HAYNES - COMPLETE TRANSCRIPT LIBRARY\n")
        f.write(f"Total videos: {len(all_transcripts)}\n")
        f.write("=" * 60 + "\n\n")
        for content in all_transcripts:
            f.write(f"\n{'-' * 60}\n")
            f.write(content)
            f.write("\n\n")

    # Summary
    print(f"\n{'=' * 60}")
    print("RETRY COMPLETE!")
    print("=" * 60)
    print(f"  ✓ Newly extracted: {success_count}")
    print(f"  ✗ Still failed: {len(still_failed)}")
    print(f"  📄 Total transcripts on disk: {len(all_transcripts)}")

    if still_failed:
        still_failed_file = OUTPUT_DIR / "failed_videos.txt"
        with open(still_failed_file, 'w', encoding='utf-8') as f:
            for item in still_failed:
                f.write(f"{item['title']}|{item['video_id']}\n")
        print(f"\n  Updated failed_videos.txt ({len(still_failed)} remaining)")
    else:
        # All succeeded - remove failed file
        if FAILED_FILE.exists():
            FAILED_FILE.unlink()
        print("\n  🎉 All videos successfully transcribed!")

    # Word count
    master_text = master_file.read_text(encoding='utf-8')
    word_count = len(master_text.split())
    print(f"\n  📊 ALL_TRANSCRIPTS.txt: {word_count:,} words")
    print(f"\n{'=' * 60}")


if __name__ == "__main__":
    main()
