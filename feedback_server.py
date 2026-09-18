#!/usr/bin/env python3
"""
Tamonashini Feedback Server
Simple HTTP server to handle email button clicks
Run with: python3 feedback_server.py [--port 9000]
"""

from flask import Flask, request, jsonify, redirect, escape
import sys
from feedback_handler import FeedbackQueue

app = Flask(__name__)
queue = FeedbackQueue()

@app.route('/feedback', methods=['GET', 'POST'])
def handle_feedback():
    """Handle feedback submission from email buttons"""

    video_id = request.args.get('video_id') or request.form.get('video_id')
    feedback_type = request.args.get('type') or request.form.get('type')
    notes = request.args.get('notes') or request.form.get('notes', '')

    if not video_id or not feedback_type:
        return jsonify({'error': 'Missing video_id or type'}), 400

    success, message = queue.submit_feedback(video_id, feedback_type, notes)

    if request.method == 'GET':
        # Escape message to prevent XSS
        safe_message = escape(message)

        # Redirect back with success/error message
        if success:
            return f"""
            <html>
            <head>
                <title>Feedback Received</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 50px; }}
                    .success {{ color: #27ae60; font-size: 24px; margin: 20px 0; }}
                    .message {{ color: #7f8c8d; font-size: 16px; }}
                </style>
            </head>
            <body>
                <div class="success">✅ Feedback Recorded!</div>
                <div class="message">{safe_message}</div>
                <p style="margin-top: 40px; color: #95a5a6;">You can close this window.</p>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <head>
                <title>Feedback Error</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; text-align: center; padding: 50px; }}
                    .error {{ color: #e74c3c; font-size: 24px; margin: 20px 0; }}
                    .message {{ color: #7f8c8d; font-size: 16px; }}
                </style>
            </head>
            <body>
                <div class="error">❌ Error</div>
                <div class="message">{safe_message}</div>
                <p style="margin-top: 40px; color: #95a5a6;">Please try again or contact support.</p>
            </body>
            </html>
            """
    else:
        # Return JSON for programmatic use
        return jsonify({
            'success': success,
            'message': message,
            'video_id': video_id,
            'feedback_type': feedback_type
        }), 200 if success else 400

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200

@app.route('/', methods=['GET'])
def index():
    """Server info page"""
    return """
    <html>
    <head>
        <title>Tamonashini Feedback Server</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 50px; max-width: 600px; margin: 0 auto; }
            h1 { color: #2c3e50; }
            code { background-color: #ecf0f1; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🔄 Tamonashini Feedback Server</h1>
        <p>Server is running and ready to receive feedback from email buttons.</p>

        <h2>Endpoints</h2>
        <ul>
            <li><code>GET/POST /feedback?video_id=...&type=correct|false_positive|uncertain</code> - Submit feedback</li>
            <li><code>GET /health</code> - Health check</li>
        </ul>

        <h2>Running</h2>
        <p>This server is accessed by email button clicks. Make sure it's accessible from the internet or configure firewall rules.</p>
    </body>
    </html>
    """

def main():
    """Start the feedback server"""
    import argparse

    parser = argparse.ArgumentParser(description='Tamonashini Feedback Server')
    parser.add_argument('--port', type=int, default=9000, help='Port to run on (default: 9000)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()

    print(f"🚀 Starting Tamonashini Feedback Server on {args.host}:{args.port}")
    print(f"   Endpoint: http://localhost:{args.port}/feedback")
    print(f"   Health: http://localhost:{args.port}/health")

    app.run(host=args.host, port=args.port, debug=False)

if __name__ == '__main__':
    main()
