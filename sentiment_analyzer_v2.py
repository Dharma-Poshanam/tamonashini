#!/usr/bin/env python3
"""
Tamonashini Sentiment Analyzer v2 - Optimized analysis
Phase 1: Title-based sentiment analysis (fast, low-cost)
Phase 2: Optional full video analysis for negative titles (controlled by flag)
"""

import os
import json
import csv
import asyncio
from datetime import datetime
from typing import Optional, List, Dict
import google.generativeai as genai
from google.cloud import aiplatform
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from tenacity import retry, stop_after_attempt, wait_random_exponential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TamonashiniSentimentAnalyzer:
    # Official channels to exclude from analysis
    OFFICIAL_CHANNELS = {
        '@dattapeetham',
        '@gurubhavanaadpt',
        '@kshtcultural7147',
        '@DallasHanuman',
        '@YogaSangeeta',
        '@SGSRagaSagara',
        '@sgsswamiji',
        # Also check by display name
        'Dattapeetham',
        'Guru Bhavana',
        'KSHT Cultural',
        'Dallas Hanuman',
        'Yoga Sangeeta',
        'SGS Raga Sagara',
        'SGS Swamiji',
    }

    def __init__(self, analyze_full_video: bool = False):
        """
        Initialize analyzer

        Args:
            analyze_full_video: If True, analyze full video content after title analysis
                               If False, only analyze titles (faster, lower cost)
        """
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.project_id = 'dattavani'
        self.location = 'asia-south1'  # Mumbai
        self.analyze_full_video = analyze_full_video

        if not self.youtube_api_key:
            raise ValueError("YOUTUBE_API_KEY not set in .env.local")

        # Initialize YouTube API
        self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)

        # Initialize Vertex AI
        aiplatform.init(project=self.project_id, location=self.location)

        # Initialize Generative AI
        genai.configure(api_key=self.youtube_api_key)

        # Model IDs (using 1.5 models for compatibility)
        self.gemini_flash_model = 'gemini-1.5-flash'
        self.gemini_pro_model = 'gemini-1.5-pro'

        self.csv_file = 'sentiment_analysis_results.csv'
        self._init_csv()

        self.system_instruction = """You are a specialized analyzer for detecting defamatory content
under Bharatiya Nyaya Sanhita (BNS) Section 356. Analyze for:
(1) False statements of fact, (2) Crime/misconduct accusations, (3) Damaging false claims"""

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
                    'title_negative_phrases',
                    'full_video_sentiment_score',
                    'full_video_sentiment_label',
                    'defamatory_claims',
                    'language_detected',
                    'view_count',
                    'analysis_timestamp'
                ])
                writer.writeheader()

    def _is_official_channel(self, channel_name: str) -> bool:
        """Check if channel is one of our official channels"""
        if not channel_name:
            return False

        channel_lower = channel_name.lower()
        for official in self.OFFICIAL_CHANNELS:
            if official.lower() in channel_lower or channel_lower in official.lower():
                return True
        return False

    def _get_title_analysis_schema(self) -> dict:
        """Schema for quick title-based sentiment analysis"""
        return {
            "type": "OBJECT",
            "properties": {
                "sentiment_score": {
                    "type": "NUMBER",
                    "description": "Score from -1 (negative) to 1 (positive)"
                },
                "sentiment_label": {
                    "type": "STRING",
                    "enum": ["highly_negative", "negative", "neutral", "positive"]
                },
                "negative_phrases": {
                    "type": "ARRAY",
                    "items": {"type": "STRING"}
                }
            }
        }

    def _get_full_video_analysis_schema(self) -> dict:
        """Schema for comprehensive video content analysis"""
        return {
            "type": "OBJECT",
            "properties": {
                "sentiment_score": {
                    "type": "NUMBER"
                },
                "sentiment_label": {
                    "type": "STRING",
                    "enum": ["highly_negative", "negative", "neutral", "positive"]
                },
                "defamatory_claims": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "claim": {"type": "STRING"},
                            "claim_type": {
                                "type": "STRING",
                                "enum": ["crime_accusation", "fraud", "misconduct",
                                        "immoral_conduct", "false_fact", "other"]
                            },
                            "timestamp": {"type": "STRING"}
                        }
                    }
                },
                "language_detected": {
                    "type": "STRING",
                    "enum": ["english", "kannada", "telugu", "mixed"]
                }
            }
        }

    @retry(wait=wait_random_exponential(multiplier=1, max=30), stop=stop_after_attempt(2))
    def analyze_title(self, title: str) -> dict:
        """
        Quick sentiment analysis of video title only
        Fast and low-cost (Phase 1)
        """
        try:
            schema = self._get_title_analysis_schema()

            prompt = f"""Analyze this YouTube video title for negative sentiment and defamatory language.
Title: "{title}"

Respond with JSON containing:
1. sentiment_score: -1 to 1 (negative to positive)
2. sentiment_label: highly_negative, negative, neutral, or positive
3. negative_phrases: key phrases that indicate negativity or defamation

Focus on words indicating: false accusations, fraud, crime, misconduct, damage to reputation."""

            response = self.client.models.generate_content(
                model=self.gemini_flash_model,
                contents=[prompt],
                config={
                    "max_output_tokens": 1024,
                    "response_mime_type": "application/json",
                    "response_schema": schema
                }
            )

            result = json.loads(response.text)
            return result

        except Exception as e:
            logger.error(f"Title analysis error: {e}")
            return {
                'sentiment_score': 0,
                'sentiment_label': 'unknown',
                'negative_phrases': []
            }

    @retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_attempt(2))
    def analyze_full_video(self, video_url: str) -> dict:
        """
        Comprehensive analysis of full video content
        Optional Phase 2 (only if title shows negative sentiment)
        """
        try:
            schema = self._get_full_video_analysis_schema()

            prompt = """Analyze this YouTube video for defamatory content.
Return JSON with:
1. sentiment_score: -1 to 1
2. sentiment_label: highly_negative, negative, neutral, or positive
3. defamatory_claims: array of false/defamatory statements found
4. language_detected: english, kannada, telugu, or mixed

Focus on BNS Section 356 criteria: false facts, false accusations, reputation damage."""

            response = self.client.models.generate_content(
                model=self.gemini_pro_model,
                contents=[
                    self.system_instruction,
                    {
                        "file_data": {
                            "file_uri": video_url,
                            "mime_type": "video/webm"
                        }
                    },
                    prompt
                ],
                config={
                    "max_output_tokens": 4096,
                    "response_mime_type": "application/json",
                    "response_schema": schema
                }
            )

            result = json.loads(response.text)
            return result

        except Exception as e:
            logger.error(f"Full video analysis error: {e}")
            return {
                'sentiment_score': 0,
                'sentiment_label': 'unknown',
                'defamatory_claims': [],
                'language_detected': 'unknown'
            }

    def search_videos(self, query: str, max_results: int = 10) -> list:
        """Search YouTube for videos"""
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
        """Get view count"""
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
            logger.error(f"Error getting video stats: {e}")
            return {'view_count': 0}

    def save_to_csv(self, video_data: dict, title_analysis: dict, full_video_analysis: Optional[dict] = None):
        """Save analysis results to CSV"""
        claims = []
        full_sentiment = 'N/A'
        language = 'N/A'

        if full_video_analysis:
            claims = full_video_analysis.get('defamatory_claims', [])
            full_sentiment = full_video_analysis.get('sentiment_label', 'N/A')
            language = full_video_analysis.get('language_detected', 'N/A')

        claim_texts = [c.get('claim', '') for c in claims]

        row = {
            'video_id': video_data['video_id'],
            'url': video_data['url'],
            'title': video_data['title'],
            'channel_name': video_data['channel_name'],
            'upload_date': video_data['upload_date'],
            'title_sentiment_score': title_analysis.get('sentiment_score', 0),
            'title_sentiment_label': title_analysis.get('sentiment_label', 'unknown'),
            'title_negative_phrases': ', '.join(title_analysis.get('negative_phrases', [])),
            'full_video_sentiment_score': full_video_analysis.get('sentiment_score', 'N/A') if full_video_analysis else 'N/A',
            'full_video_sentiment_label': full_sentiment,
            'defamatory_claims': ' | '.join(claim_texts) if claim_texts else '',
            'language_detected': language,
            'view_count': video_data.get('view_count', 0),
            'analysis_timestamp': datetime.now().isoformat()
        }

        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            writer.writerow(row)

        logger.info(f"Saved {video_data['video_id']} - Title sentiment: {title_analysis.get('sentiment_label')}")

    async def analyze_video_async(self, video_data: dict) -> bool:
        """
        Analyze single video: title first, then full video if negative
        Returns True if saved to CSV
        Skips videos from official channels
        """
        try:
            # Skip official channels
            if self._is_official_channel(video_data['channel_name']):
                logger.info(f"Skipping {video_data['video_id']} - Official channel: {video_data['channel_name']}")
                return False

            # Phase 1: Title analysis (fast)
            title_analysis = self.analyze_title(video_data['title'])

            # Get view count
            stats = self.get_video_stats(video_data['video_id'])
            video_data['view_count'] = stats['view_count']

            # Phase 2: Full video analysis (optional, only if negative title)
            full_video_analysis = None
            if self.analyze_full_video and title_analysis.get('sentiment_score', 0) < -0.3:
                logger.info(f"Title negative ({title_analysis.get('sentiment_score'):.2f}), analyzing full video...")
                full_video_analysis = self.analyze_full_video(video_data['url'])

            # Save if negative
            if title_analysis.get('sentiment_score', 0) < -0.3:
                self.save_to_csv(video_data, title_analysis, full_video_analysis)
                return True

            return False

        except Exception as e:
            logger.error(f"Error analyzing {video_data['video_id']}: {e}")
            return False

    async def run_async(self, queries: list):
        """
        Analyze multiple videos asynchronously
        Phase 1: Title analysis for all
        Phase 2: Full video analysis for negative titles (if enabled)
        """
        all_videos = []

        for query in queries:
            videos = self.search_videos(query, max_results=10)
            all_videos.extend(videos)

        logger.info(f"Analyzing {len(all_videos)} videos (title-first strategy)...")

        tasks = [self.analyze_video_async(video) for video in all_videos]
        results = await asyncio.gather(*tasks)

        saved_count = sum(1 for r in results if r)
        logger.info(f"Analysis complete. {saved_count} negative videos saved to {self.csv_file}")

    def run(self, queries: list):
        """Synchronous version"""
        all_videos = []

        for query in queries:
            videos = self.search_videos(query, max_results=10)
            all_videos.extend(videos)

        logger.info(f"Analyzing {len(all_videos)} videos (title-first strategy)...")

        saved_count = 0
        for video in all_videos:
            try:
                # Skip official channels
                if self._is_official_channel(video['channel_name']):
                    logger.info(f"Skipping {video['video_id']} - Official channel: {video['channel_name']}")
                    continue

                title_analysis = self.analyze_title(video['title'])
                stats = self.get_video_stats(video['video_id'])
                video['view_count'] = stats['view_count']

                full_video_analysis = None
                if self.analyze_full_video and title_analysis.get('sentiment_score', 0) < -0.3:
                    full_video_analysis = self.analyze_full_video(video['url'])

                if title_analysis.get('sentiment_score', 0) < -0.3:
                    self.save_to_csv(video, title_analysis, full_video_analysis)
                    saved_count += 1

                logger.info(f"{video['video_id']}: {title_analysis.get('sentiment_label')} "
                          f"({title_analysis.get('sentiment_score', 0):.2f})")

            except Exception as e:
                logger.error(f"Error processing {video['video_id']}: {e}")

        logger.info(f"Analysis complete. {saved_count} negative videos saved to {self.csv_file}")
