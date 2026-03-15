#!/usr/bin/env python3
"""
PHASE 3: Transcript Summarizer using Claude API
Reads individual transcripts and generates structured summaries.

Usage:
  export ANTHROPIC_API_KEY="sk-ant-..."
  python3 phase3_summarize.py
"""

import os
import re
import sys
import time
import glob
from pathlib import Path

try:
    from anthropic import Anthropic
except ImportError:
    print("Installing anthropic SDK...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'anthropic', '-q'])
    from anthropic import Anthropic

# Configuration
OUTPUT_DIR = Path("./jeremy_haynes_transcripts")
TRANSCRIPTS_DIR = OUTPUT_DIR / "transcripts"
SUMMARIES_DIR = OUTPUT_DIR / "summaries"
DELAY_SECONDS = 2
MODEL = "claude-sonnet-4-20250514"

SUMMARY_PROMPT = """You are summarizing a YouTube video transcript from Jeremy Haynes, a digital marketing expert who helps businesses scale to $1M+/month using paid advertising, funnels, and offer strategy.

Condense the following transcript into a structured summary of approximately 500 words. Use this exact format:

CORE CONCEPT:
[1-2 sentences describing the main idea, framework, or thesis of this video]

TACTICAL TAKEAWAYS:
- [Specific actionable advice point 1]
- [Specific actionable advice point 2]
- [Specific actionable advice point 3]
- [Specific actionable advice point 4 if applicable]
- [Specific actionable advice point 5 if applicable]

KEY QUOTES:
- "[Memorable phrase or concept in Jeremy's language]"
- "[Another key phrase or concept]"
- "[Another key phrase or concept if applicable]"

APPLY WHEN:
[1-2 sentences describing what client situation, business stage, or problem this content addresses. Be specific about when to reference this content.]

Important guidelines:
- Preserve Jeremy's specific terminology, frameworks, and naming conventions (e.g., "DSL strategy", "propaganda content marketing", "buyer types", "lump-sum actions")
- Focus on TACTICAL advice, not generic motivation
- The takeaways should be specific enough to act on, not vague platitudes
- For KEY QUOTES, capture phrases that sound distinctly like Jeremy's voice and teaching style
- Keep the total summary around 500 words

Here is the transcript:

"""


def summarize_transcript(client, title, transcript_text, category):
    """Send transcript to Claude for summarization."""
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": SUMMARY_PROMPT + transcript_text
            }
        ]
    )
    return message.content[0].text


def parse_transcript_file(filepath):
    """Read a transcript file and extract metadata + content."""
    text = filepath.read_text(encoding='utf-8')
    lines = text.split('\n')

    title = ""
    video_url = ""
    category = ""
    content_start = 0

    for i, line in enumerate(lines):
        if line.startswith("TITLE: "):
            title = line[7:].strip()
        elif line.startswith("VIDEO: "):
            video_url = line[7:].strip()
        elif line.startswith("CATEGORY: "):
            category = line[10:].strip()
        elif line.startswith("=" * 10):
            content_start = i + 1
            break

    transcript = '\n'.join(lines[content_start:]).strip()
    return title, video_url, category, transcript


def sanitize_filename(title):
    """Convert title to safe filename."""
    safe = re.sub(r'[<>:"/\\|?*]', '', title)
    safe = re.sub(r'\s+', '_', safe)
    safe = safe[:80]
    return safe


def main():
    print("=" * 60)
    print("PHASE 3: SUMMARIZE TRANSCRIPTS WITH CLAUDE")
    print("=" * 60)

    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("\n❌ Error: ANTHROPIC_API_KEY is not set!")
        print("\nSet it with:")
        print('  export ANTHROPIC_API_KEY="sk-ant-..."')
        print("\nThen re-run this script.")
        sys.exit(1)

    client = Anthropic()
    print(f"\n✓ API key found ({api_key[:12]}...)")

    # Find transcripts
    transcript_files = sorted(TRANSCRIPTS_DIR.glob("*.txt"))
    if not transcript_files:
        print(f"\n❌ No transcript files found in {TRANSCRIPTS_DIR}")
        sys.exit(1)

    print(f"✓ Found {len(transcript_files)} transcripts to summarize")

    # Check for already-completed summaries to allow resuming
    SUMMARIES_DIR.mkdir(exist_ok=True)
    existing_summaries = set(f.stem for f in SUMMARIES_DIR.glob("*.txt"))

    to_process = []
    skipped = 0
    for tf in transcript_files:
        if tf.stem in existing_summaries:
            skipped += 1
        else:
            to_process.append(tf)

    if skipped > 0:
        print(f"✓ Skipping {skipped} already-summarized transcripts")
        print(f"✓ {len(to_process)} remaining to process")

    if not to_process and skipped > 0:
        print("\nAll transcripts already summarized! Rebuilding master file...")
    else:
        est_minutes = round(len(to_process) * (DELAY_SECONDS + 3) / 60, 1)
        print(f"\nEstimated time: ~{est_minutes} minutes")
        print(f"Using model: {MODEL}")
        print("-" * 60)

    # Process each transcript
    success_count = 0
    failed = []

    for i, tf in enumerate(to_process, 1):
        title, video_url, category, transcript = parse_transcript_file(tf)
        word_count = len(transcript.split())

        print(f"[{i}/{len(to_process)}] {title[:50]}... ({word_count:,}w)", end=" ", flush=True)

        try:
            summary = summarize_transcript(client, title, transcript, category)

            # Save individual summary
            summary_file = SUMMARIES_DIR / f"{tf.stem}.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"TITLE: {title}\n")
                f.write(f"VIDEO: {video_url}\n")
                f.write(f"CATEGORY: {category}\n")
                f.write("=" * 60 + "\n\n")
                f.write(summary)

            success_count += 1
            print("✓")

        except Exception as e:
            print(f"❌ {str(e)[:80]}")
            failed.append({'title': title, 'error': str(e)})

        # Rate limit delay
        if i < len(to_process):
            time.sleep(DELAY_SECONDS)

    # Build master knowledge base from ALL summaries (including previously completed)
    print("\nBuilding master knowledge base...")

    all_summaries = []
    for sf in sorted(SUMMARIES_DIR.glob("*.txt")):
        text = sf.read_text(encoding='utf-8')
        lines = text.split('\n')

        title = ""
        video_url = ""
        category = "Uncategorized"
        summary_start = 0

        for j, line in enumerate(lines):
            if line.startswith("TITLE: "):
                title = line[7:].strip()
            elif line.startswith("VIDEO: "):
                video_url = line[7:].strip()
            elif line.startswith("CATEGORY: "):
                category = line[10:].strip()
            elif line.startswith("=" * 10):
                summary_start = j + 1
                break

        summary_text = '\n'.join(lines[summary_start:]).strip()
        all_summaries.append({
            'title': title,
            'video_url': video_url,
            'category': category or 'Uncategorized',
            'summary': summary_text
        })

    # Organize by category
    categories = {}
    for s in all_summaries:
        cat = s['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(s)

    # Write master file
    master_file = OUTPUT_DIR / "JEREMY_HAYNES_KNOWLEDGE_BASE.txt"
    with open(master_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("JEREMY HAYNES - KNOWLEDGE BASE\n")
        f.write(f"Total videos summarized: {len(all_summaries)}\n")
        f.write(f"Categories: {', '.join(sorted(categories.keys()))}\n")
        f.write("=" * 60 + "\n\n")

        f.write("TABLE OF CONTENTS\n")
        f.write("-" * 40 + "\n")
        for cat in sorted(categories.keys()):
            f.write(f"\n## {cat.upper()} ({len(categories[cat])} videos)\n")
            for s in categories[cat]:
                f.write(f"   - {s['title']}\n")
        f.write("\n" + "=" * 60 + "\n\n")

        for cat in sorted(categories.keys()):
            f.write(f"\n{'#' * 60}\n")
            f.write(f"# CATEGORY: {cat.upper()}\n")
            f.write(f"# {len(categories[cat])} videos\n")
            f.write(f"{'#' * 60}\n\n")

            for s in categories[cat]:
                f.write(f"\n{'-' * 60}\n")
                f.write(f"## {s['title']}\n")
                f.write(f"URL: {s['video_url']}\n")
                f.write(f"{'-' * 60}\n\n")
                f.write(s['summary'])
                f.write("\n\n")

    # Word count of master file
    master_words = len(master_file.read_text(encoding='utf-8').split())

    # Summary
    print(f"\n{'=' * 60}")
    print("COMPLETE!")
    print("=" * 60)
    print(f"  ✓ Newly summarized: {success_count}")
    if skipped:
        print(f"  ✓ Previously done: {skipped}")
    print(f"  📄 Total in knowledge base: {len(all_summaries)}")
    if failed:
        print(f"  ✗ Failed: {len(failed)}")
        for item in failed:
            print(f"      - {item['title'][:50]}: {item['error'][:50]}")
    print(f"\n  Output:")
    print(f"    - summaries/                          ({len(all_summaries)} files)")
    print(f"    - JEREMY_HAYNES_KNOWLEDGE_BASE.txt    ({master_words:,} words)")
    print(f"\n{'=' * 60}")


if __name__ == "__main__":
    main()
