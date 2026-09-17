#!/usr/bin/env python3
"""
Quick test - analyze just a couple of videos to verify the system works
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from sentiment_analyzer_v2 import TamonashiniSentimentAnalyzer

def main():
    # Load environment variables
    env_path = Path(__file__).parent / '.env.local'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    try:
        print("=" * 60)
        print("DATTAVANI SENTIMENT ANALYZER - QUICK TEST")
        print("=" * 60)

        analyzer = TamonashiniSentimentAnalyzer(analyze_full_video=False)

        # Just 2 test queries to find a few videos
        test_queries = [
            'Ganapathy Sachchidananda Swamiji',
            'Dattapeetham Swami',
        ]

        print(f"\nSearching for videos...")
        print(f"Queries: {test_queries}\n")

        all_videos = []
        for query in test_queries:
            videos = analyzer.search_videos(query, max_results=2)  # Just 2 videos per query
            all_videos.extend(videos)

        print(f"Found {len(all_videos)} videos total\n")
        print("-" * 60)

        if not all_videos:
            print("No videos found!")
            return 1

        # Show which videos will be analyzed
        print("VIDEO LIST:")
        for i, video in enumerate(all_videos, 1):
            is_official = analyzer._is_official_channel(video['channel_name'])
            status = "SKIP (Official)" if is_official else "ANALYZE"
            print(f"{i}. {video['title'][:50]}...")
            print(f"   Channel: {video['channel_name']}")
            print(f"   Status: {status}")
            print()

        print("-" * 60)

        # Analyze
        print("\nStarting analysis...")
        asyncio.run(analyzer.run_async(test_queries))

        # Show results
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)

        if os.path.exists(analyzer.csv_file):
            with open(analyzer.csv_file, 'r') as f:
                lines = f.readlines()

            if len(lines) > 1:
                print(f"\n✅ Results saved to: {analyzer.csv_file}")
                print(f"Total rows: {len(lines) - 1} (excluding header)\n")

                # Show first few rows
                print("Sample results (first 2 rows):")
                print(lines[0].strip())  # Header
                for line in lines[1:3]:
                    print(line.strip())
            else:
                print(f"\n⚠️  No negative videos found (only header in CSV)")
        else:
            print(f"\n❌ CSV file not created")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
