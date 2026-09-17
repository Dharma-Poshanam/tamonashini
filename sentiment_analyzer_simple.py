#!/usr/bin/env python3
"""
Simplified Tamonashini Sentiment Analyzer - Compatible with google-generativeai 0.4.0
Two-phase analysis: Title → Optional Full Video
"""

import os
import json
import csv
from datetime import datetime
from typing import Optional, Dict
import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TamonashiniSentimentAnalyzer:
    # Official channels to exclude
    OFFICIAL_CHANNELS = {
        '@dattapeetham',
        '@gurubhavanaadpt',
        '@kshtcultural7147',
        '@DallasHanuman',
        '@YogaSangeeta',
        '@SGSRagaSagara',
        '@sgsswamiji',
        'Dattapeetham',
        'Guru Bhavana',
        'KSHT Cultural',
        'Dallas Hanuman',
        'Yoga Sangeeta',
        'SGS Raga Sagara',
        'SGS Swamiji',
    }

    def __init__(self, analyze_full_video: bool = False, credentials_file: str = None):
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.analyze_full_video = analyze_full_video
        self.credentials_file = credentials_file or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

        # Initialize YouTube API
        if self.credentials_file and os.path.exists(self.credentials_file):
            # Use OAuth2 with service account
            logger.info(f"Using service account: {self.credentials_file}")
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/youtube.readonly']
            )
            self.youtube = build('youtube', 'v3', credentials=credentials)
        elif self.youtube_api_key:
            # Fallback to API key (limited, but works for some operations)
            logger.info("Using API key authentication")
            self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
        else:
            raise ValueError("No authentication found. Set GOOGLE_APPLICATION_CREDENTIALS or YOUTUBE_API_KEY")

        # Initialize Generative AI
        if self.youtube_api_key:
            genai.configure(api_key=self.youtube_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            raise ValueError("YOUTUBE_API_KEY required for Gemini API")

        self.csv_file = 'sentiment_analysis_results.csv'
        self._init_csv()

    def _init_csv(self):
        """Initialize CSV with headers"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'video_id',
                    'url',
                    'title',
                    'channel_name',
                    'upload_date',
                    'title_sentiment_score',
                    'title_sentiment_label',
                    'negative_keywords',
                    'view_count',
                    'analysis_timestamp'
                ])
                writer.writeheader()

    def _is_official_channel(self, channel_name: str) -> bool:
        """Check if channel is official"""
        if not channel_name:
            return False

        channel_lower = channel_name.lower()
        for official in self.OFFICIAL_CHANNELS:
            if official.lower() in channel_lower or channel_lower in official.lower():
                return True
        return False

    def search_videos(self, query: str, max_results: int = 10) -> list:
        """Search YouTube for videos"""
        try:
            logger.info(f"Searching: {query}")
            request = self.youtube.search().list(
                q=query,
                part='snippet',
                maxResults=max_results,
                order='relevance',
                type='video',
                regionCode='IN'
            )
            response = request.execute()

            videos = []
            for item in response.get('items', []):
                video_id = item['id']['videoId']
                videos.append({
                    'video_id': video_id,
                    'title': item['snippet']['title'],
                    'channel_name': item['snippet']['channelTitle'],
                    'upload_date': item['snippet']['publishedAt'],
                    'url': f'https://www.youtube.com/watch?v={video_id}'
                })

            logger.info(f"Found {len(videos)} videos")
            return videos
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return []

    def get_video_stats(self, video_id: str) -> dict:
        """Get video view count"""
        try:
            request = self.youtube.videos().list(
                id=video_id,
                part='statistics'
            )
            response = request.execute()

            if response['items']:
                return {'view_count': response['items'][0]['statistics'].get('viewCount', 0)}
            return {'view_count': 0}
        except HttpError as e:
            logger.error(f"Error getting stats: {e}")
            return {'view_count': 0}

    def analyze_title(self, title: str) -> dict:
        """Analyze title sentiment using Gemini"""
        try:
            prompt = f"""Analyze this YouTube video title for negative sentiment.
Title: "{title}"

Respond with ONLY a JSON object (no markdown, no explanation):
{{"sentiment_score": <-1 to 1>, "sentiment_label": "negative|neutral|positive", "keywords": [<list>]}}

Score: -1 = very negative, 0 = neutral, 1 = very positive
Keywords: Extract words suggesting fraud, crime, false accusations, misconduct."""

            response = self.model.generate_content(prompt)
            text = response.text.strip()

            # Clean response
            if text.startswith('```'):
                text = '\n'.join(text.split('\n')[1:-1])
                if text.startswith('json'):
                    text = text[4:]

            result = json.loads(text)
            return {
                'sentiment_score': float(result.get('sentiment_score', 0)),
                'sentiment_label': result.get('sentiment_label', 'unknown'),
                'keywords': result.get('keywords', [])
            }
        except Exception as e:
            logger.error(f"Title analysis error: {e}")
            return {'sentiment_score': 0, 'sentiment_label': 'unknown', 'keywords': []}

    def save_to_csv(self, video: dict, analysis: dict):
        """Save results to CSV"""
        row = {
            'video_id': video['video_id'],
            'url': video['url'],
            'title': video['title'],
            'channel_name': video['channel_name'],
            'upload_date': video['upload_date'],
            'title_sentiment_score': analysis.get('sentiment_score', 0),
            'title_sentiment_label': analysis.get('sentiment_label', 'unknown'),
            'negative_keywords': ', '.join(analysis.get('keywords', [])),
            'view_count': video.get('view_count', 0),
            'analysis_timestamp': datetime.now().isoformat()
        }

        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            writer.writerow(row)

        logger.info(f"✅ Saved {video['video_id']} - {analysis.get('sentiment_label')} "
                  f"({analysis.get('sentiment_score', 0):.2f})")

    def run(self, queries: list):
        """Analyze videos"""
        all_videos = []

        # Search
        for query in queries:
            videos = self.search_videos(query, max_results=10)
            all_videos.extend(videos)

        print(f"\n📊 Found {len(all_videos)} videos total\n")

        # Analyze
        analyzed_count = 0
        skipped_count = 0
        negative_count = 0

        for video in all_videos:
            # Skip official channels
            if self._is_official_channel(video['channel_name']):
                logger.info(f"⊘ Skipping official channel: {video['channel_name']}")
                skipped_count += 1
                continue

            analyzed_count += 1

            # Get view count
            stats = self.get_video_stats(video['video_id'])
            video['view_count'] = stats['view_count']

            # Analyze title
            analysis = self.analyze_title(video['title'])

            # Save if negative
            if analysis.get('sentiment_score', 0) < -0.3:
                self.save_to_csv(video, analysis)
                negative_count += 1
            else:
                logger.info(f"Neutral/Positive: {video['video_id']} "
                          f"({analysis.get('sentiment_label')})")

        # Summary
        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"Videos found: {len(all_videos)}")
        print(f"Official channels skipped: {skipped_count}")
        print(f"Analyzed: {analyzed_count}")
        print(f"Negative found: {negative_count}")
        print(f"Results saved to: {self.csv_file}")
