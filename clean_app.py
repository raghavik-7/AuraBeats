from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
from io import BytesIO
import os
from datetime import datetime
import logging
from dotenv import load_dotenv

# Import our clean modules
#from advanced_captioning import AdvancedImageCaptioner
from fixed_captioning import ReliableImageCaptioner
#from llm_music_recommender import PureLLMMusicRecommender
#from fixed_llm_music_recommender import FixedLLMMusicRecommender
from gemini_music_recommender import GeminiMusicRecommender as MusicRecommender
from simple_security import SimpleSecurityManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize systems
logger.info(" Initializing clean systems...")

try:
    # Choose your models here
    captioner = ReliableImageCaptioner(model_name="blip")  # or "git-large", "blip2"
    #music_recommender = PureLLMMusicRecommender(llm_provider="openai")  # or "anthropic", "google"
    music_recommender = MusicRecommender()
    security_manager = SimpleSecurityManager()
    logger.info(" All systems initialized!")
except Exception as e:
    logger.error(f" Initialization failed: {e}")
    exit(1)

@app.route('/')
def home():
    """Simple home page"""
    return jsonify({
        'message': 'Clean Image to Music Recommendation API',
        'description': 'Pure AI-driven recommendations without manual mappings',
        'endpoints': {
            '/recommend': 'POST - Get music recommendations from image',
            '/health': 'GET - Check system health'
        }
    })

@app.route('/recommend', methods=['POST'])
def recommend_music():
    """Main endpoint - pure AI recommendations"""
    try:
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Get parameters
        context = data.get('context', '')
        num_songs = data.get('num_songs', 5)
        session_id = data.get('session_id', 'anonymous')
        
        # Decode image
        image_data = base64.b64decode(data['image'])
        
        # Step 1: Generate detailed caption
        logger.info(" Generating detailed image caption...")
        caption, processing_id = security_manager.secure_image_processing(
            image_data, session_id, captioner, context
        )
        
        if caption.startswith("Error:"):
            return jsonify({'error': caption}), 500
        
        # Step 2: Get LLM music recommendations
        logger.info(" Getting LLM music recommendations...")
        recommendations = music_recommender.recommend_songs(
            caption, context, num_songs
        )
        
        # Prepare response
        response = {
            'processing_id': processing_id,
            'image_caption': caption,
            'music_recommendations': recommendations,
            'context': context,
            'timestamp': datetime.now().isoformat(),
            'models_used': {
                'captioning': captioner.model_name,
                'llm': music_recommender.provider
            }
        }
        
        logger.info(f" Request completed: {processing_id}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f" Request failed: {e}")
        return jsonify({
            'error': 'Processing failed',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'message': 'Clean AI-powered music recommendation system',
        'models': {
            'captioning_model': captioner.model_name,
            'llm_provider': music_recommender.provider
        },
        'features': [
            'Advanced image captioning',
            'Pure LLM music recommendations',
            'No manual mappings',
            'Secure image processing'
        ]
    })

if __name__ == '__main__':
    print(" Starting Clean Image to Music Recommendation System...")
    print(f" Captioning: {captioner.model_name}")
    print(f" LLM: {getattr(music_recommender, 'provider', 'gemini')}")
    print(" Server: http://localhost:5000")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
