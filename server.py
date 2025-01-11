from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
import os
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.environ.get('ENVIRONMENT') == 'production' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Error handler
@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"An error occurred: {str(error)}", exc_info=True)
    return jsonify({
        'error': str(error),
        'status': 'error'
    }), 500

@app.route('/')
@limiter.limit("10 per minute")
def home():
    return jsonify({
        'status': 'Server is running',
        'endpoints': {
            'transcript': '/api/transcript',
            'health': '/health'
        },
        'version': '1.0.0'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'environment': os.environ.get('ENVIRONMENT', 'development'),
        'service': 'youtube-transcript-api'
    })

def get_video_transcript(url):
    try:
        def get_video_transcript(url):
    try:
        parsed_url = urlparse(url)
        if 'youtube.com' in parsed_url.netloc:
            query_params = parse_qs(parsed_url.query)
            video_id = query_params.get('v', [None])[0]
        else:
            video_id = parsed_url.path.split('/')[-1]

        if not video_id:
            raise ValueError("Invalid YouTube URL")

        # Test network access to YouTube
        test_url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(test_url)
        if response.status_code != 200:
            logger.error(f"Network access to YouTube failed: {response.status_code}")
            return None

        # Fetch transcript
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

        # Combine all text into a single paragraph
        transcript_text = " ".join([entry['text'] for entry in transcript])
        return transcript_text

    except TranscriptsDisabled:
        logger.error(f"Subtitles are disabled for the video: {url}")
        return None
    except Exception as e:
        logger.error(f"Error fetching transcript: {str(e)}", exc_info=True)
        raise

@app.route('/env',methods=['GET'])
def env():
    import sys
    import pkg_resources
    return jsonify({
        'python_version': sys.version,
        'installed_packages': {pkg.key: pkg.version for pkg in pkg_resources.working_set}
    })

@app.route('/api/transcript', methods=['POST'])
@limiter.limit("100 per hour")
def get_transcript():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400

        url = data['url']
        transcript = get_video_transcript(url)
        return jsonify({'transcript': transcript})

    except Exception as e:
        logger.error(f"Error in transcript endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)