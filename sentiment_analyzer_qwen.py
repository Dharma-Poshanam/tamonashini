#!/usr/bin/env python3
"""
Tamonashini Sentiment Analyzer - Using local Qwen via vLLM
Runs against local vLLM server for fast offline sentiment analysis
"""

import os
import requests
import json
from typing import Dict

class QwenSentimentAnalyzer:
    """Sentiment analysis using local Qwen model via vLLM"""

    def __init__(self, vllm_base_url: str = "http://127.0.0.1:8000", use_feedback_context: bool = True):
        self.base_url = vllm_base_url
        self.api_endpoint = f"{vllm_base_url}/v1/messages"
        self.use_feedback_context = use_feedback_context
        self.feedback_context = ""

        # Load feedback context if enabled
        if use_feedback_context:
            self._load_feedback_context()

        # Test connection
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            if response.status_code == 200:
                print(f"✅ Connected to vLLM at {self.base_url}")
            else:
                print(f"⚠️  vLLM returned status {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"⚠️  Cannot connect to vLLM at {self.base_url}")
            print("   Start it with: bash ~/infra/scripts/vllm-01-serve.sh Qwen/Qwen2.5-7B-Instruct 32768 0.80")

    def _load_feedback_context(self):
        """Load feedback-informed context for prompt refinement"""
        try:
            from feedback_analyzer import FeedbackAnalyzer
            analyzer = FeedbackAnalyzer()
            self.feedback_context = analyzer.generate_refined_prompt_context()
        except (ImportError, Exception):
            self.feedback_context = ""

    def analyze_video_title(self, title: str, channel: str) -> Dict:
        """Analyze video relevance and sentiment"""

        prompt = f"""Analyze this YouTube video for relevance and sentiment.

Title: "{title}"
Channel: "{channel}"

Respond ONLY with JSON (no markdown):
{{
  "relevant": true/false,
  "reason": "brief reason",
  "sentiment_score": -1 to 1,
  "sentiment_label": "negative|neutral|positive",
  "keywords": ["list", "of", "keywords"]
}}

Relevance criteria:
- True if mentions: Swamiji, Ganapathy, Satchidananda, Dattapeetham, court, fraud, land encroachment
- False if generic content (meditation, yoga, music) unrelated to Swamiji
- True if appears controversial/negative

Sentiment score:
- Negative (-0.5 to -1.0): accuses, fraud, court case, scandal
- Neutral (-0.1 to 0.1): educational, informational
- Positive (0.1 to 1.0): praise, endorsement{self.feedback_context}"""

        try:
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": "Qwen2.5-7B-Instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 256,
                    "temperature": 0.7
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                # vLLM returns Anthropic-style response format
                if 'content' in data and isinstance(data['content'], list):
                    text = data['content'][0]['text'].strip()
                else:
                    # Fallback for OpenAI-style format
                    text = data['choices'][0]['message']['content'].strip()

                # Extract JSON from response
                try:
                    # Try direct parse
                    result = json.loads(text)
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown
                    if '```' in text:
                        text = text.split('```')[1]
                        if text.startswith('json'):
                            text = text[4:]
                        text = text.strip()
                    result = json.loads(text)

                return result
            else:
                print(f"vLLM error: {response.status_code}")
                return {
                    'relevant': False,
                    'reason': f'API error {response.status_code}',
                    'sentiment_score': 0,
                    'sentiment_label': 'unknown',
                    'keywords': []
                }

        except requests.exceptions.Timeout:
            print("⚠️  vLLM request timeout")
            return {
                'relevant': False,
                'reason': 'timeout',
                'sentiment_score': 0,
                'sentiment_label': 'unknown',
                'keywords': []
            }
        except Exception as e:
            print(f"Analysis error: {e}")
            return {
                'relevant': False,
                'reason': f'error: {str(e)[:50]}',
                'sentiment_score': 0,
                'sentiment_label': 'unknown',
                'keywords': []
            }

    def filter_and_analyze(self, videos: list) -> list:
        """Filter videos by relevance and sentiment"""

        relevant_videos = []

        print(f"\nAnalyzing {len(videos)} videos with Qwen...\n")

        for i, video in enumerate(videos, 1):
            title = video.get('title', '')
            channel = video.get('channel', '')

            # Quick keyword filter first
            keywords = ['swamiji', 'ganapathy', 'satchidananda', 'dattapeetham',
                       'court', 'fraud', 'land', 'encroachment', 'case', 'scandal']
            has_keyword = any(kw.lower() in title.lower() for kw in keywords)

            if not has_keyword:
                print(f"{i}. ⊘ SKIP: {title[:50]}... (generic content)")
                continue

            # Analyze with Qwen
            analysis = self.analyze_video_title(title, channel)

            if analysis.get('relevant'):
                sentiment = analysis.get('sentiment_label', 'unknown')
                score = analysis.get('sentiment_score', 0)

                video['analysis'] = analysis
                relevant_videos.append(video)

                print(f"{i}. ✓ RELEVANT: {title[:50]}...")
                print(f"   Sentiment: {sentiment} ({score:.2f})")
                print(f"   Reason: {analysis.get('reason', 'N/A')}")
            else:
                print(f"{i}. ⊘ SKIP: {title[:50]}... ({analysis.get('reason', 'not relevant')})")

        return relevant_videos
