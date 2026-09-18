#!/usr/bin/env python3
"""
HTML email templates with clickable feedback buttons
Properly escapes all user-controlled data to prevent XSS
"""

import html as html_module
from datetime import datetime
from urllib.parse import urlparse, quote

def is_valid_youtube_url(url: str) -> bool:
    """Validate that URL is a YouTube URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc in ('youtube.com', 'www.youtube.com', 'm.youtube.com')
    except:
        return False

def generate_email_html(new_videos_count: int, new_videos: list, prev_videos: list, feedback_base_url: str = "http://localhost:9000") -> str:
    """Generate HTML email with clickable feedback buttons"""

    email_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }
        .video-card {
            background-color: #f9f9f9;
            border-left: 4px solid #e74c3c;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .video-title {
            font-weight: bold;
            color: #2c3e50;
            font-size: 16px;
            word-wrap: break-word;
        }
        .video-meta {
            color: #7f8c8d;
            font-size: 14px;
            margin: 8px 0;
        }
        .video-score {
            display: inline-block;
            background-color: #e74c3c;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
            margin-right: 10px;
        }
        .button-group {
            margin-top: 12px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .feedback-btn {
            padding: 10px 16px;
            border: none;
            border-radius: 4px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.2s;
        }
        .btn-correct {
            background-color: #27ae60;
            color: white;
        }
        .btn-correct:hover {
            background-color: #229954;
        }
        .btn-false-positive {
            background-color: #e74c3c;
            color: white;
        }
        .btn-false-positive:hover {
            background-color: #c0392b;
        }
        .btn-uncertain {
            background-color: #f39c12;
            color: white;
        }
        .btn-uncertain:hover {
            background-color: #d68910;
        }
        .status-box {
            background-color: #ecf0f1;
            border: 1px solid #bdc3c7;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }
        .status-positive {
            background-color: #d5f4e6;
            border-color: #27ae60;
        }
        .status-negative {
            background-color: #fadbd8;
            border-color: #e74c3c;
        }
        .timestamp {
            color: #7f8c8d;
            font-size: 12px;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            color: #7f8c8d;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Tamonashini Daily Analysis Report</h1>
        <p class="timestamp">{timestamp}</p>
"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    email_html = email_html.replace("{timestamp}", timestamp)

    # Status section
    if new_videos_count > 0:
        email_html += f"""
        <div class="status-box status-negative">
            <strong>⚠️ {new_videos_count} NEW NEGATIVE VIDEO(S) FOUND</strong>
            <p>Click feedback buttons below to validate accuracy</p>
        </div>
"""
    else:
        email_html += """
        <div class="status-box status-positive">
            <strong>✅ NO NEW NEGATIVE VIDEOS FOUND</strong>
            <p>System is actively monitoring and all recently flagged content has been reviewed.</p>
        </div>
"""

    # New videos section
    if new_videos_count > 0:
        email_html += f"<h2>🚨 NEW VIDEOS ({new_videos_count})</h2>"
        for i, video in enumerate(new_videos, 1):
            vid_id = html_module.escape(str(video.get('id', '')))
            title = html_module.escape(str(video.get('title', '')))
            channel = html_module.escape(str(video.get('channel', '')))
            score = video.get('analysis', {}).get('sentiment_score', 0)
            url = video.get('url', '')

            # Validate and escape YouTube URL
            if is_valid_youtube_url(url):
                safe_url = html_module.escape(url, quote=True)
            else:
                safe_url = '#'

            # URL encode video_id for use in feedback URL
            encoded_vid_id = quote(str(video.get('id', '')), safe='')

            email_html += f"""
        <div class="video-card">
            <div class="video-title">{i}. {title}</div>
            <div class="video-meta">
                <span class="video-score">{score:.2f}</span>
                Channel: <strong>{channel}</strong><br>
                <a href="{safe_url}" target="_blank">Watch on YouTube →</a>
            </div>
            <div class="button-group">
                <a href="{feedback_base_url}/feedback?video_id={encoded_vid_id}&type=correct" class="feedback-btn btn-correct">✓ Correct</a>
                <a href="{feedback_base_url}/feedback?video_id={encoded_vid_id}&type=false_positive" class="feedback-btn btn-false-positive">✗ False Positive</a>
                <a href="{feedback_base_url}/feedback?video_id={encoded_vid_id}&type=uncertain" class="feedback-btn btn-uncertain">? Uncertain</a>
            </div>
        </div>
"""

    # Previously reported videos section
    if prev_videos:
        email_html += f"<h2>📋 PREVIOUSLY REPORTED VIDEOS ({len(prev_videos)})</h2>"
        for i, video in enumerate(prev_videos, 1):
            vid_id = html_module.escape(str(video[0]))
            title = html_module.escape(str(video[1]))
            channel = html_module.escape(str(video[2]))
            url = video[3]
            score = video[5]

            # Validate and escape YouTube URL
            if is_valid_youtube_url(url):
                safe_url = html_module.escape(url, quote=True)
            else:
                safe_url = '#'

            # URL encode video_id for use in feedback URL
            encoded_vid_id = quote(str(video[0]), safe='')

            email_html += f"""
        <div class="video-card">
            <div class="video-title">{i}. {title}</div>
            <div class="video-meta">
                <span class="video-score">{score:.2f}</span>
                Channel: <strong>{channel}</strong><br>
                <a href="{safe_url}" target="_blank">Watch on YouTube →</a>
            </div>
            <div class="button-group">
                <a href="{feedback_base_url}/feedback?video_id={encoded_vid_id}&type=correct" class="feedback-btn btn-correct">✓ Correct</a>
                <a href="{feedback_base_url}/feedback?video_id={encoded_vid_id}&type=false_positive" class="feedback-btn btn-false-positive">✗ False Positive</a>
                <a href="{feedback_base_url}/feedback?video_id={encoded_vid_id}&type=uncertain" class="feedback-btn btn-uncertain">? Uncertain</a>
            </div>
        </div>
"""

    email_html += """
        <div class="footer">
            <p><strong>Tamonashini</strong> - Sentiment Analysis Monitoring System</p>
            <p>Powered by Qwen2.5-7B-Instruct (vLLM) | Feedback-driven threshold optimization</p>
            <p>Your feedback helps improve accuracy. Thank you!</p>
        </div>
    </div>
</body>
</html>
"""

    return email_html
