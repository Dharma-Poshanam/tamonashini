#!/usr/bin/env python3
"""
Validate Tamonashini Sentiment Analyzer setup
Checks configuration, environment, and API key without making API calls
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    print("=" * 60)
    print("DATTAVANI SENTIMENT ANALYZER - SETUP VALIDATION")
    print("=" * 60)

    # Load environment
    env_path = Path(__file__).parent / '.env.local'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"\n✅ .env.local found")
    else:
        print(f"\n❌ .env.local not found")
        return 1

    # Check API key
    api_key = os.getenv('YOUTUBE_API_KEY')
    if api_key:
        print(f"✅ YOUTUBE_API_KEY present ({len(api_key)} chars)")
        if api_key.startswith('AQ.'):
            print(f"✅ API key format looks valid (starts with AQ.)")
        else:
            print(f"⚠️  API key format unusual (doesn't start with AQ.)")
    else:
        print(f"❌ YOUTUBE_API_KEY not set")
        return 1

    # Check Python version
    print(f"\n✅ Python {sys.version.split()[0]}")

    # Check required modules
    print(f"\nChecking dependencies...")
    dependencies = {
        'googleapiclient': 'YouTube API',
        'dotenv': 'Environment loader',
        'tenacity': 'Retry logic',
    }

    all_ok = True
    for module, description in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {module} ({description})")
        except ImportError as e:
            print(f"❌ {module} ({description}): {e}")
            all_ok = False

    # Check project structure
    print(f"\nChecking project structure...")
    required_files = [
        'sentiment_analyzer_v2.py',
        'main_v2.py',
        'requirements.txt',
        'deploy_scheduler.sh',
        '.env.local',
    ]

    for file in required_files:
        path = Path(__file__).parent / file
        if path.exists():
            size = path.stat().st_size
            print(f"✅ {file} ({size} bytes)")
        else:
            print(f"❌ {file} missing")
            all_ok = False

    # Check CSV file
    csv_path = Path(__file__).parent / 'sentiment_analysis_results.csv'
    if csv_path.exists():
        lines = len(csv_path.read_text().splitlines())
        print(f"✅ sentiment_analysis_results.csv ({lines} lines)")
    else:
        print(f"ℹ️  sentiment_analysis_results.csv not yet created (will be created on first run)")

    # Check official channels filter
    print(f"\nOfficial Channels Filter:")
    official_channels = {
        '@dattapeetham',
        '@gurubhavanaadpt',
        '@kshtcultural7147',
        '@DallasHanuman',
        '@YogaSangeeta',
        '@SGSRagaSagara',
        '@sgsswamiji',
    }
    print(f"✅ {len(official_channels)} official channels configured to skip")
    for channel in sorted(official_channels):
        print(f"   - {channel}")

    # Summary
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ SETUP VALIDATION PASSED")
        print("\nYou can now run:")
        print("  python main_v2.py              # Title analysis only")
        print("  ANALYZE_FULL_VIDEO=true python main_v2.py  # With full video analysis")
        return 0
    else:
        print("❌ SETUP VALIDATION FAILED")
        print("\nPlease fix the issues above, then run:")
        print("  pip install -r requirements.txt")
        return 1

if __name__ == '__main__':
    sys.exit(main())
