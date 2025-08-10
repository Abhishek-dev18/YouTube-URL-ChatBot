from flask import Flask, render_template, request, jsonify, session
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini AI configured successfully")
else:
    logger.warning("Gemini API key not found")

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([^?]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^?]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/([^?]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([^?]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_youtube_transcript(video_id):
    """Get transcript from YouTube video"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US', 'en-GB'])
        transcript_text = ' '.join([item['text'] for item in transcript_list])
        return transcript_text
    except Exception as e:
        logger.error(f"Transcript extraction failed for {video_id}: {str(e)}")
        try:
            # Try with auto-generated captions
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = ' '.join([item['text'] for item in transcript_list])
            return transcript_text
        except Exception as e2:
            logger.error(f"All transcript extraction attempts failed: {str(e2)}")
            return None

def chat_with_gemini(question, transcript):
    """Chat with Gemini AI using the transcript as context"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')

        prompt = f"""
        You are an AI assistant that helps users understand YouTube video content based on transcripts.
        You are knowledgeable, helpful, and provide clear, concise responses.

        TRANSCRIPT:
        {transcript[:8000]}  # Limit to avoid token limits

        USER QUESTION: {question}

        Instructions:
        1. Answer the question based ONLY on the information in the transcript above
        2. If the transcript doesn't contain relevant information, politely say so
        3. Keep responses clear, concise, and helpful
        4. Use bullet points or numbered lists when appropriate
        5. Quote specific parts of the transcript when relevant

        Response:
        """

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        return f"I apologize, but I encountered an error while processing your question: {str(e)}"

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/extract_transcript', methods=['POST'])
def extract_transcript():
    """Extract transcript from YouTube URL"""
    try:
        data = request.get_json()
        youtube_url = data.get('url', '').strip()

        if not youtube_url:
            return jsonify({'error': 'Please provide a YouTube URL'}), 400

        # Extract video ID
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL format. Please check the URL and try again.'}), 400

        logger.info(f"Extracting transcript for video: {video_id}")

        # Get transcript
        transcript = get_youtube_transcript(video_id)
        if not transcript:
            return jsonify({
                'error': 'Could not extract transcript. This video might not have captions/subtitles available. Please try a different video.'
            }), 400

        # Store transcript in session
        session['transcript'] = transcript
        session['video_id'] = video_id
        session['extraction_time'] = datetime.now().isoformat()

        logger.info(f"Transcript extracted successfully for {video_id}")

        return jsonify({
            'success': True,
            'transcript': transcript,
            'video_id': video_id,
            'length': len(transcript)
        })

    except Exception as e:
        logger.error(f"Extract transcript error: {str(e)}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/ask_question', methods=['POST'])
def ask_question():
    """Ask AI about the transcript content"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()

        if not question:
            return jsonify({'error': 'Please provide a question'}), 400

        # Get transcript from session
        transcript = session.get('transcript')
        if not transcript:
            return jsonify({'error': 'No transcript available. Please extract a transcript first.'}), 400

        if not GEMINI_API_KEY:
            return jsonify({'error': 'AI service is not configured. Please contact the administrator.'}), 500

        logger.info(f"Processing question: {question[:50]}...")

        # Get AI response
        ai_response = chat_with_gemini(question, transcript)

        # Store in session for history (optional)
        if 'chat_history' not in session:
            session['chat_history'] = []

        session['chat_history'].append({
            'question': question,
            'response': ai_response,
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({
            'success': True,
            'response': ai_response,
            'question': question
        })

    except Exception as e:
        logger.error(f"Ask question error: {str(e)}")
        return jsonify({'error': f'An error occurred while processing your question: {str(e)}'}), 500

@app.route('/clear_session', methods=['POST'])
def clear_session():
    """Clear the current session"""
    session.clear()
    logger.info("Session cleared")
    return jsonify({'success': True, 'message': 'Session cleared successfully'})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'gemini_configured': GEMINI_API_KEY is not None
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
