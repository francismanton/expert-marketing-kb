#!/usr/bin/env python3
"""Fetch transcripts from Apify datasets and save as text files."""
import json
import os
import urllib.request

APIFY_TOKEN = os.environ["APIFY_TOKEN"]
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Format: (expert, video_title, dataset_id)
VIDEOS = [
    # --- HORMOZI ---
    ("hormozi", "The Best SALES TRAINING On The Internet", "Ina8SFrEr3DAaH2BQ"),
    ("hormozi", "100M CEO Explains How to Build A Brand", "YjmoDHdThGFTJK3hu"),
    ("hormozi", "Watch this to get your first 5 customers", "QvPjQka1ehvuOtcHQ"),
    ("hormozi", "13 Years Of Brutally Honest Business Advice", "YSHv4Eu5Mc5nUeYy9"),
    ("hormozi", "If I Wanted to Become a Millionaire In 2024", "ZQ1sC3bq94KnF5uIu"),
    ("hormozi", "How to Make Money So Fast It Feels ILLEGAL", "Gevjr4Gx5R0TrIX9L"),
    ("hormozi", "Im Broke What Business Do I Start", "VFQ1guSDAZenli2pu"),
    ("hormozi", "How to Grow an Audience if You Have 0 Followers", "1xwdj1gxQcHtH4p3H"),
    ("hormozi", "The Alex Hormozi Cookbook REVEALED", "adhRptbSsMpahUspr"),
    ("hormozi", "If You Have Less Than 10000 Saved", "OXGd77ehioa4NNaMj"),
    # --- RAVI ABUVALA ---
    ("ravi", "How To Generate 5-10 Qualified Sales Calls Per Day", "DnH7MQ70GCqqfxUz4"),
    ("ravi", "How To Do Cold Email To Get Clients", "hPFyag8IgigXdRvBv"),
    ("ravi", "How To Use LinkedIn Sales Navigator To Generate Leads", "5izHLk7jmeyHy3VTI"),
    ("ravi", "LinkedIn Lead Generation Using Sales Navigator Dripify", "Wsdxcx8hop9QnMlcG"),
    ("ravi", "This One Thing Doubled Our Show-Up Rate", "xT3aRK7g4NPHfmfMK"),
    ("ravi", "How To Craft the Perfect Email Marketing Strategy", "21MK4lPhUaH4J3AZA"),
    ("ravi", "12 B2B Lead Generation Strategies For 2026", "4q38RUeD0ingH6bsC"),
    ("ravi", "How Optimizing Operations Exploded Our 8-Figure Business", "MmkiGzJTjm6XdJb2D"),
    ("ravi", "How I Manage 1296 High-Ticket Clients", "ayDgrGMxzr3TUjcX5"),
    ("ravi", "12 Proven Steps To Build A Million Dollar Landing Page", "UhT1vwGenOanJieJi"),
    # --- SAM OVENS ---
    ("ovens", "9 Inconvenient Truths About The Online Business Market", "GXeWmhIKi05gMakdv"),
    ("ovens", "How Id Start Over And Rebuild My Business From Scratch", "aahm4fpixtezR1552"),
    ("ovens", "Ninja Shit Playing To The Biases Of Facebooks Algorithm", "jZml1BU1tZDNSTmEb"),
    ("ovens", "The Flywheel Secret Behind Amazon Google Uber", "5ei3tHM2reNcVASgR"),
    ("ovens", "A Recipe For Domination Long Term Thinking Moats", "ieCdRFOHk6ChaZxa1"),
    ("ovens", "Horizontal Scaling How To Scale Facebook Ads To The Moon", "TgsLCvgEfC72CHlFx"),
    ("ovens", "Systems Thinking How Billionaires Think", "23kDtiggaG5Yta5nZ"),
    ("ovens", "Stop Confusing Yourself Define The Problem And Solve It", "04qVSvE7j0fal30Zc"),
    ("ovens", "Tools To Plan For The New Year", "ce6Ibj0tz1DE9ChIr"),
    ("ovens", "Sacrifice Yield And Asymmetric Returns", "SL7cSMmLGIn8IxsCZ"),
    # --- SABRI SUBY ---
    ("suby", "17 Years of Marketing Advice in 46 Mins", "xXmvrZO7K7tTRBY9A"),
    ("suby", "How To Sell Anything For 23x More Than Competition", "9povEbZhze1XKjiFd"),
    ("suby", "I Locked Myself In A Room Until I Made 1M", "tdWdC3OR5c9DHHxMh"),
    ("suby", "The Ultimate Step-By-Step Landing Page Guide", "6JjvouF5jZQu4QsgD"),
    ("suby", "The Ultimate Step-By-Step Guide To Cold-Calling", "SiYokn6Cb02ovsl4S"),
    ("suby", "How To Craft A Godfather Offer", "xzAFqWWz8NbNjamSI"),
    ("suby", "How Id Make 10k Per Month If My Life Depended On It", "E7R9NbmSjsSxHYXLx"),
    ("suby", "POV You Spend 200M On Facebook Ads To Learn This", "iyCUNDPGp5daLb0Ta"),
    ("suby", "How To Fix Your Funnels And Landing Pages", "iXcgcFMILTA3TrBEs"),
    ("suby", "7.8 Billion Of Marketing Advice In 68 Minutes", "tdc4rXpM0TVaVDpBX"),
    # --- RUSSELL BRUNSON ---
    ("brunson", "What Is A Sales Funnel And How To Create One", "udnN5K9mXK08bswbE"),
    ("brunson", "Sales Funnel Strategy 7 Simple Hacks", "y4awF6MFags4WOO1k"),
    ("brunson", "Fastest Way To Make Money With Clickbank", "XNGXnNSIReGunn2gL"),
    ("brunson", "How I Learned How To Sell ANYTHING Door-To-Door", "YWgkBIEGrgWOUg52h"),
    ("brunson", "How To Sell Anything With An Irresistible Offer", "5cyrgc2RBxRuxDC14"),
    ("brunson", "From 0 To 1 Million In 1 Year", "vDVGxA8SMcAgAYr9B"),
    ("brunson", "How To Create A Mastermind Group", "BseQIdNec2SaGAd6b"),
    ("brunson", "How To 5X Your Business With Dan Kennedy", "v5nJbdeHuXUkWlpJU"),
    ("brunson", "Number 1 Way To Make More Money Value Ladder", "jWL4FR0mT1WtNuBJA"),
    ("brunson", "Your Funnel SUCKS Heres How To Fix It", "bVmD4Zlr3xceYMeCF"),
]

def fetch_dataset(dataset_id):
    url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def extract_transcript(data):
    if not data:
        return ""
    item = data[0]
    segments = item.get("data", [])
    if isinstance(segments, list):
        return " ".join(seg.get("text", "") for seg in segments)
    return str(segments)

def main():
    for expert, title, dataset_id in VIDEOS:
        safe_title = title.replace(" ", "_").replace("/", "_").replace("'", "")
        filename = f"{expert}_{safe_title}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 100:
            print(f"SKIP (exists): {filename}")
            continue

        try:
            data = fetch_dataset(dataset_id)
            transcript = extract_transcript(data)
            if transcript:
                with open(filepath, "w") as f:
                    f.write(transcript)
                print(f"OK ({len(transcript):,} chars): {filename}")
            else:
                print(f"EMPTY: {filename}")
        except Exception as e:
            print(f"ERROR: {filename} - {e}")

if __name__ == "__main__":
    main()
