from flask import Flask, request, jsonify
from flask_cors import CORS
# from scrape_youtube import Youtube
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
import logging
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_video_transcript(url):
    try:
        parsed_url = urlparse(url)
        if 'youtube.com' in parsed_url.netloc or 'youtu.be' in parsed_url.netloc:
            if 'youtu.be' in parsed_url.netloc:
                video_id = parsed_url.path.strip('/')
            else:
                query_params = parse_qs(parsed_url.query)
                video_id = query_params.get('v', [None])[0]
        else:
            logger.error(f"Invalid YouTube URL: {url}")
            return None

        if not video_id:
            logger.error(f"Invalid YouTube URL: {url}")
            return None

        logger.info(f"Fetching transcript for video ID: {video_id}")
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([entry['text'] for entry in transcript])
        logger.info("Transcript fetched successfully")
        return transcript_text

    except YouTubeTranscriptApi.NoTranscriptFound:
        logger.error(f"No subtitles available for the video: {url}")
        return None
    except Exception as e:
        logger.error(f"Error fetching transcript: {str(e)}", exc_info=True)
        return None

@app.route('/api/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'URL is required'}), 400

        url = data['url']
        transcript = get_video_transcript(url)

        if transcript is None:
            return jsonify({'error': 'Subtitles are disabled for this video'}), 404

        return jsonify({'transcript': transcript})

    except Exception as e:
        logger.error(f"Error in transcript endpoint: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)