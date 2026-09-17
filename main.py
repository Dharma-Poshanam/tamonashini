#!/usr/bin/env python3
"""
Main entry point for sentiment analyzer
Can be run locally or via Cloud Scheduler / Cloud Functions
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sentiment_analyzer import TamonashiniSentimentAnalyzer

def main():
    # Load environment variables
    env_path = Path(__file__).parent / '.env.local'
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()  # Load from system env

    try:
        analyzer = TamonashiniSentimentAnalyzer()

        # Search queries in multiple languages
        queries = [
            'Ganapathy Sachchidananda Swamiji',
            'Satchidananda Swami',
            'Dattapeetham Swami',
            'ಗಣಪತಿ ಸತ್ಯನಂದ',  # Kannada
            'గణపతి సత్యానంద',   # Telugu
            'land encroachment Dattapeetham',
            'Ganapathy court case',
            'Sachchidananda fraud',
            'Dattapeetham controversy',
            'Swami Ganapathy case',
        ]

        analyzer.run(queries)
        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
