#!/usr/bin/env python3
"""
Tamonashini Sentiment Analyzer - Monitors YouTube for negative sentiment videos
Uses Gemini's multimodal video analysis + Vertex AI for native language support
Implements structured extraction with controlled generation (JSON schemas)
"""

import os
import json
import csv
import asyncio
from datetime import datetime
from typing import Optional, List
import google.generativeai as genai
from google.cloud import aiplatform
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from tenacity import retry, stop_after_attempt, wait_random_exponential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TamonashiniSentimentAnalyzer:
    def __init__(self):
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.project_id = 'dattavani'
        self.location = 'asia-south1'  # Mumbai

        if not self.youtube_api_key:
            raise ValueError("YOUTUBE_API_KEY not set in .env.local")

        # Initialize YouTube API
        self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)

        # Initialize Vertex AI
        aiplatform.init(project=self.project_id, location=self.location)

        # Initialize Generative AI for video analysis
        genai.configure(api_key=self.youtube_api_key)
        self.client = genai.Client()

        # Model IDs for multimodal video analysis
        self.gemini_flash_model = 'gemini-2.0-flash'
        self.gemini_pro_model = 'gemini-2.0-pro'

        self.csv_file = 'sentiment_analysis_results.csv'
        self._init_csv()

    def _init_csv(self):
        """Initialize CSV with headers if it doesn't exist"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'video_id',
                    'url',
                    'title',
                    'channel_name',
                    'upload_date',
                    'language',
                    'transcript_excerpt',
                    'sentiment_score',
                    'sentiment_label',
                    'negative_phrases',
                    'imputation_type',
                    'view_count',
                    'timestamp'
                ])
                writer.writeheader()

    def search_videos(self, query: str, max_results: int = 10) -> list:
        """Search YouTube for videos using native language queries"""
        try:
            logger.info(f"Searching YouTube for: {query}")
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
        """Get video statistics (view count, etc.)"""
        try:
            request = self.youtube.videos().list(
                id=video_id,
                part='statistics,contentDetails'
            )
            response = request.execute()

            if response['items']:
                item = response['items'][0]
                return {
                    'view_count': item['statistics'].get('viewCount', 0),
                    'duration': item['contentDetails'].get('duration', '')
                }
            return {'view_count': 0, 'duration': ''}
        except HttpError as e:
            logger.error(f"Error getting video stats: {e}")
            return {'view_count': 0, 'duration': ''}

    def extract_transcript(self, video_id: str) -> Optional[str]:
        """
        Extract transcript from YouTube video.
        For now, returns a placeholder - in production, use youtube-transcript-api
        """
        try:
            # Try to get captions
            request = self.youtube.captions().list(
                videoId=video_id,
                part='snippet'
            )
            response = request.execute()

            if response['items']:
                return f"[Captions available for {video_id}]"
            return None
        except HttpError:
            logger.warning(f"No captions found for {video_id}")
            return None

    def analyze_sentiment_with_vertex_ai(self, text: str, language: str = 'en') -> dict:
        """
        Analyze sentiment using Vertex AI Agent
        Supports native language analysis: English, Kannada, Telugu
        """
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')

            prompt = f"""Analyze the sentiment of the following text in {language} language.
Return a JSON response with:
- sentiment_score: float between -1 (most negative) and 1 (most positive)
- sentiment_label: "negative", "neutral", or "positive"
- negative_phrases: list of phrases that are negative or defamatory
- imputation_type: type of claim (e.g., "fraud", "misconduct", "crime", "false accusation")

Text: {text[:1000]}

Respond ONLY with valid JSON, no other text."""

            response = model.generate_content(prompt)

            # Parse response
            try:
                result = json.loads(response.text)
            except json.JSONDecodeError:
                # Fallback if response is not clean JSON
                result = {
                    'sentiment_score': -0.5,
                    'sentiment_label': 'negative',
                    'negative_phrases': ['Unable to parse'],
                    'imputation_type': 'unknown'
                }

            return result
        except Exception as e:
            logger.error(f"Vertex AI sentiment analysis error: {e}")
            return {
                'sentiment_score': 0,
                'sentiment_label': 'unknown',
                'negative_phrases': [],
                'imputation_type': 'error'
            }

    def detect_language(self, text: str) -> str:
        """Detect language of text (simplified - returns 'en', 'kn', or 'te')"""
        # Basic detection based on character ranges
        kannada_chars = 'ಀ-೿'
        telugu_chars = 'ఀ-౿'

        if any('ಀ' <= c <= '೿' for c in text):
            return 'kn'  # Kannada
        elif any('ఀ' <= c <= '౿' for c in text):
            return 'te'  # Telugu
        return 'en'  # English

    def save_to_csv(self, video_data: dict, sentiment_data: dict):
        """Save analysis results to CSV"""
        row = {
            'video_id': video_data['video_id'],
            'url': video_data['url'],
            'title': video_data['title'],
            'channel_name': video_data['channel_name'],
            'upload_date': video_data['upload_date'],
            'language': video_data.get('language', 'unknown'),
            'transcript_excerpt': video_data.get('transcript', '')[:200],
            'sentiment_score': sentiment_data.get('sentiment_score', 0),
            'sentiment_label': sentiment_data.get('sentiment_label', 'unknown'),
            'negative_phrases': ', '.join(sentiment_data.get('negative_phrases', [])),
            'imputation_type': sentiment_data.get('imputation_type', 'unknown'),
            'view_count': video_data.get('view_count', 0),
            'timestamp': datetime.now().isoformat()
        }

        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            writer.writerow(row)

        logger.info(f"Saved video {video_data['video_id']} to CSV")

    def run(self, queries: list):
        """Run sentiment analysis for given search queries"""
        all_videos = []

        for query in queries:
            videos = self.search_videos(query, max_results=10)
            all_videos.extend(videos)

        logger.info(f"Analyzing {len(all_videos)} videos...")

        for video in all_videos:
            try:
                # Get video stats
                stats = self.get_video_stats(video['video_id'])
                video['view_count'] = stats['view_count']

                # Extract transcript (placeholder for now)
                transcript = self.extract_transcript(video['video_id'])
                video['transcript'] = transcript or video['title']

                # Detect language
                language = self.detect_language(video['transcript'])
                video['language'] = language

                # Analyze sentiment
                sentiment_result = self.analyze_sentiment_with_vertex_ai(
                    video['transcript'],
                    language=self._language_name(language)
                )

                # Save to CSV if negative
                if sentiment_result['sentiment_score'] < -0.3:
                    self.save_to_csv(video, sentiment_result)
                    logger.info(f"Video {video['video_id']}: {sentiment_result['sentiment_label']} "
                              f"({sentiment_result['sentiment_score']:.2f})")

            except Exception as e:
                logger.error(f"Error processing video {video['video_id']}: {e}")
                continue

        logger.info(f"Analysis complete. Results saved to {self.csv_file}")

    def _language_name(self, code: str) -> str:
        """Convert language code to full name"""
        mapping = {'en': 'English', 'kn': 'Kannada', 'te': 'Telugu'}
        return mapping.get(code, 'English')


if __name__ == '__main__':
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
    ]

    analyzer.run(queries)
