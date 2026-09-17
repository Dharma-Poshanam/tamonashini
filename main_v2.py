#!/usr/bin/env python3
"""
Tamonashini Sentiment Analyzer v2 - Main entry point
Two-phase analysis:
1. Title-based sentiment (fast, always run)
2. Full video analysis (optional, only for negative titles)
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
        # Control full video analysis via environment variable
        # Default: False (only analyze titles - fast & cheap)
        analyze_full_video = os.getenv('ANALYZE_FULL_VIDEO', 'false').lower() == 'true'

        print(f"Mode: {'Title + Full Video Analysis' if analyze_full_video else 'Title Analysis Only'}")

        analyzer = TamonashiniSentimentAnalyzer(analyze_full_video=analyze_full_video)

        # Comprehensive search queries
        queries = [
            # English variations
            'Ganapathy Sachchidananda Swamiji',
            'Satchidananda Swami',
            'Dattapeetham Swami',
            'land encroachment Dattapeetham',
            'Ganapathy court case',
            'Sachchidananda fraud',
            'Dattapeetham controversy',
            'Swami Ganapathy case',
            'Swami Satyananda',
            'Dattapeetham fraud',

            # Kannada
            'ಗಣಪತಿ ಸತ್ಯನಂದ',
            'ದತ್ತಪೀಠ ಸ್ವಾಮಿ',

            # Telugu
            'గణపతి సత్యానంద',
            'దత్తపీఠ స్వామి',
        ]

        asyncio.run(analyzer.run_async(queries))
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
