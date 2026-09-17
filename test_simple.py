#!/usr/bin/env python3
"""
Simple test - analyze 2-3 videos to verify the system works
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sentiment_analyzer_simple import TamonashiniSentimentAnalyzer

def main():
    # Load environment
    env_path = Path(__file__).parent / '.env.local'
    if env_path.exists():
        load_dotenv(env_path)

    try:
        print("\n" + "=" * 60)
        print("DATTAVANI SENTIMENT ANALYZER - LOCAL TEST")
        print("=" * 60)

        analyzer = TamonashiniSentimentAnalyzer()

        # Just 2 queries to find a few videos
        test_queries = [
            'Ganapathy Sachchidananda Swamiji',
            'Dattapeetham Swami',
        ]

        print(f"\nSearching for videos with {len(test_queries)} queries...\n")
        analyzer.run(test_queries)

        # Show results
        print("\n" + "=" * 60)
        print("CSV RESULTS")
        print("=" * 60)

        csv_file = analyzer.csv_file
        if os.path.exists(csv_file):
            with open(csv_file, 'r') as f:
                lines = f.readlines()

            print(f"\nFile: {csv_file}")
            print(f"Total rows: {len(lines) - 1} (excluding header)\n")

            if len(lines) > 1:
                print("Results:")
                print(lines[0].strip())
                for line in lines[1:]:
                    print(line.strip()[:120] + "..." if len(line) > 120 else line.strip())
            else:
                print("No negative videos found")

        print("\n✅ Test complete!\n")
        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
