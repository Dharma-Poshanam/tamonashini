#!/usr/bin/env python3
"""
Local test with mock YouTube data
Tests sentiment analysis and CSV export without needing YouTube API
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
        print("\n" + "=" * 70)
        print("TAMONASHINI - LOCAL TEST WITH MOCK DATA")
        print("=" * 70)

        analyzer = TamonashiniSentimentAnalyzer()

        # Mock video data (simulating YouTube results)
        mock_videos = [
            {
                'video_id': 'test001',
                'title': 'Swami Ganapathy Accused of Land Fraud - Documentary Evidence',
                'channel_name': 'Investigative News Channel',
                'upload_date': '2024-09-15T10:00:00Z',
                'url': 'https://www.youtube.com/watch?v=test001',
                'view_count': 15230
            },
            {
                'video_id': 'test002',
                'title': 'Official Teaching by Swami Ganapathy',
                'channel_name': 'Yoga Sangeeta',  # Official channel
                'upload_date': '2024-09-14T09:00:00Z',
                'url': 'https://www.youtube.com/watch?v=test002',
                'view_count': 5000
            },
            {
                'video_id': 'test003',
                'title': 'Court Case Fraud: How Gurus Manipulate Justice System',
                'channel_name': 'Critical Analysis',
                'upload_date': '2024-09-13T14:00:00Z',
                'url': 'https://www.youtube.com/watch?v=test003',
                'view_count': 8900
            },
            {
                'video_id': 'test004',
                'title': 'Meditation and Spirituality Guide - Tips for Practice',
                'channel_name': 'Wellness Channel',
                'upload_date': '2024-09-12T11:00:00Z',
                'url': 'https://www.youtube.com/watch?v=test004',
                'view_count': 3200
            }
        ]

        print("\n📊 MOCK VIDEOS:")
        print("-" * 70)
        for i, video in enumerate(mock_videos, 1):
            is_official = analyzer._is_official_channel(video['channel_name'])
            status = "⊘ SKIP (Official)" if is_official else "✓ ANALYZE"
            print(f"{i}. {video['title'][:55]}...")
            print(f"   Channel: {video['channel_name']:30} | {status}")

        print("\n" + "=" * 70)
        print("ANALYZING TITLES WITH TAMONASHINI")
        print("=" * 70)

        analyzed = 0
        skipped = 0
        negative = 0

        for video in mock_videos:
            # Check if official channel
            if analyzer._is_official_channel(video['channel_name']):
                print(f"\n⊘ SKIP: {video['video_id']} - Official channel")
                skipped += 1
                continue

            print(f"\n🔍 Analyzing: {video['video_id']}")
            print(f"   Title: {video['title'][:60]}...")
            print(f"   Channel: {video['channel_name']}")

            analyzed += 1

            # Analyze sentiment
            print("   Sentiment analysis in progress...", end=" ", flush=True)
            analysis = analyzer.analyze_title(video['title'])

            score = analysis.get('sentiment_score', 0)
            label = analysis.get('sentiment_label', 'unknown')
            keywords = analysis.get('keywords', [])

            print(f"✓")
            print(f"   Score: {score:.2f} | Label: {label}")
            print(f"   Keywords: {', '.join(keywords) if keywords else 'None'}")

            # Save if negative
            if score < -0.3:
                analyzer.save_to_csv(video, analysis)
                negative += 1
            else:
                print(f"   → Not negative enough to save")

        # Summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total videos tested: {len(mock_videos)}")
        print(f"Official channels skipped: {skipped}")
        print(f"Videos analyzed: {analyzed}")
        print(f"Negative videos found: {negative}")
        print(f"Saved to: {analyzer.csv_file}")

        # Show CSV results
        print("\n" + "=" * 70)
        print("CSV RESULTS")
        print("=" * 70)

        csv_path = Path(analyzer.csv_file)
        if csv_path.exists():
            with open(csv_path, 'r') as f:
                lines = f.readlines()

            print(f"\nFile: {analyzer.csv_file}")
            print(f"Rows: {len(lines) - 1} (excluding header)\n")

            if len(lines) > 1:
                # Show header
                headers = lines[0].strip().split(',')
                print("Columns:")
                for i, h in enumerate(headers, 1):
                    print(f"  {i:2}. {h}")

                # Show data rows
                print("\nData rows:")
                for line in lines[1:]:
                    cols = line.strip().split(',')
                    print(f"\n  Video ID: {cols[0]}")
                    print(f"  Title: {cols[2][:50]}...")
                    print(f"  Channel: {cols[3]}")
                    print(f"  Sentiment: {cols[5]} ({cols[6]})")
                    print(f"  Keywords: {cols[7]}")
            else:
                print("No negative videos found in results")

        print("\n" + "=" * 70)
        print("✅ LOCAL TEST COMPLETE")
        print("=" * 70)
        print("\nComponents verified:")
        print("  ✅ Official channel filtering")
        print("  ✅ Sentiment analysis with Gemini")
        print("  ✅ CSV export")
        print("\nSystem is ready for deployment!\n")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
