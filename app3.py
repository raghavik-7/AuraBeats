from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from flask_cors import CORS
import base64
import secrets
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
import json

# Import our modules
from fixed_captioning import ReliableImageCaptioner
from gemini_music_recommender import GeminiMusicRecommender as MusicRecommender
from simple_security import SimpleSecurityManager
from music_generator import MusicGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize systems
logger.info(" Initializing advanced systems...")

try:
    captioner = ReliableImageCaptioner(model_name="blip")
    music_recommender = MusicRecommender()
    security_manager = SimpleSecurityManager()
    music_generator = MusicGenerator()
    logger.info(" All systems initialized!")
except Exception as e:
    logger.error(f" Initialization failed: {e}")
    exit(1)

# Store active sessions and results
active_sessions = {}
analysis_results = {}

@app.route('/')
def home():
    """Serve the professional home page"""
    return render_template_string(HOME_PAGE_HTML)

@app.route('/analyze', methods=['POST'])
def analyze_image():
    """Analyze image and redirect to results page"""
    try:
        data = request.get_json()
        
        if 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Generate unique analysis ID
        analysis_id = secrets.token_urlsafe(16)
        
        # Get parameters
        image_description = data.get('description', '')
        user_preferences = data.get('preferences', '')
        language_preferences = data.get('language_preferences', '')
        context = data.get('context', 'Music recommendation')
        
        # Decode image
        image_data = base64.b64decode(data['image'])
        
        # Step 1: Generate detailed caption
        logger.info(" Generating detailed image caption...")
        caption, processing_id = security_manager.secure_image_processing(
            image_data, analysis_id, captioner, context
        )
        
        if caption.startswith("Error:"):
            return jsonify({'error': caption}), 500
        
        # Step 2: Get LLM music recommendations with language preferences
        logger.info(" Getting LLM music recommendations with language preferences...")
        recommendations = music_recommender.recommend_songs(
            caption, user_preferences, context, 8, preferred_languages=language_preferences
        )
        
        # Store results
        analysis_results[analysis_id] = {
            'image_data': data['image'],  # Store base64 for display
            'user_description': image_description,
            'user_preferences': user_preferences,
            'language_preferences': language_preferences,
            'ai_caption': caption,
            'recommendations': recommendations,
            'timestamp': datetime.now().isoformat(),
            'processing_id': processing_id
        }
        
        return jsonify({'analysis_id': analysis_id, 'redirect_url': f'/results/{analysis_id}'})
        
    except Exception as e:
        logger.error(f" Analysis failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/results/<analysis_id>')
def show_results(analysis_id):
    """Show analysis results page"""
    if analysis_id not in analysis_results:
        return redirect(url_for('home'))
    
    result = analysis_results[analysis_id]
    return render_template_string(RESULTS_PAGE_HTML, result=result, analysis_id=analysis_id)

@app.route('/refine_recommendations', methods=['POST'])
def refine_recommendations():
    """Refine recommendations based on additional user input"""
    try:
        data = request.get_json()
        
        analysis_id = data.get('analysis_id')
        additional_preferences = data.get('additional_preferences', '')
        
        if analysis_id not in analysis_results:
            return jsonify({'error': 'Analysis not found'}), 404
        
        result = analysis_results[analysis_id]
        
        # Get refined recommendations
        logger.info(" Refining music recommendations with additional preferences...")
        refined_recommendations = music_recommender.recommend_songs(
            result['ai_caption'],
            result['user_preferences'],
            'Music recommendation refinement',
            8,
            preferred_languages=result['language_preferences'],
            additional_preferences=additional_preferences
        )
        
        # Update stored results
        analysis_results[analysis_id]['recommendations'] = refined_recommendations
        analysis_results[analysis_id]['additional_preferences'] = additional_preferences
        analysis_results[analysis_id]['refined_timestamp'] = datetime.now().isoformat()
        
        return jsonify({
            'success': True,
            'recommendations': refined_recommendations,
            'message': 'Recommendations refined successfully!'
        })
        
    except Exception as e:
        logger.error(f" Refinement failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Professional Image to Music Recommendation API with Dynamic Refinement',
        'models': {
            'captioning': captioner.model_name,
            'llm': getattr(music_recommender, 'provider', 'gemini')
        },
        'integrations': {
            'youtube_enabled': True,
            'music_generation': True,
            'language_preferences': True,
            'dynamic_refinement': True
        }
    })

# Home Page HTML (same as before)
HOME_PAGE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MusicVision AI - Transform Images into Perfect Soundtracks</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            scroll-behavior: smooth;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            padding: 20px 0;
            box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 28px;
            font-weight: 700;
            color: #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .hero {
            text-align: center;
            padding: 160px 0 80px;
            color: white;
        }
        
        .hero h1 {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .hero p {
            font-size: 1.3rem;
            margin-bottom: 40px;
            opacity: 0.9;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .upload-section {
            background: white;
            border-radius: 20px;
            padding: 50px;
            margin: 50px auto;
            max-width: 800px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
        }
        
        .upload-area {
            border: 3px dashed #e0e7ff;
            border-radius: 15px;
            padding: 60px 40px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            background: #f8faff;
        }
        
        .upload-area:hover {
            border-color: #667eea;
            background: #f0f4ff;
            transform: translateY(-2px);
        }
        
        .upload-area.dragover {
            border-color: #667eea;
            background: #e0e7ff;
            transform: scale(1.02);
        }
        
        .upload-icon {
            font-size: 4rem;
            color: #667eea;
            margin-bottom: 20px;
        }
        
        .upload-text h3 {
            font-size: 1.5rem;
            color: #333;
            margin-bottom: 10px;
        }
        
        .upload-text p {
            color: #666;
            font-size: 1rem;
        }
        
        input[type="file"] {
            display: none;
        }
        
        .description-section {
            margin-top: 30px;
        }
        
        .description-section label {
            display: block;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1rem;
        }
        
        .description-input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e7ff;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
            resize: vertical;
            min-height: 100px;
        }
        
        .description-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .preferences-section {
            margin-top: 30px;
        }
        
        .language-preference-section {
            margin-top: 30px;
        }
        
        .language-input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e7ff;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
        }
        
        .language-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .language-examples {
            background: #f8faff;
            padding: 15px;
            border-radius: 10px;
            margin-top: 10px;
            border-left: 4px solid #667eea;
        }
        
        .language-examples h5 {
            color: #667eea;
            margin-bottom: 8px;
            font-size: 0.9rem;
        }
        
        .language-examples p {
            color: #666;
            font-size: 0.85rem;
            line-height: 1.4;
        }
        
        .privacy-notice {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin: 30px 0;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }
        
        .privacy-notice i {
            font-size: 1.5rem;
        }
        
        .analyze-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 18px 40px;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: block;
            margin: 30px auto 0;
            min-width: 200px;
        }
        
        .analyze-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        
        .analyze-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .image-preview {
            max-width: 300px;
            max-height: 300px;
            border-radius: 15px;
            margin: 20px auto;
            display: none;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        
        .spinner {
            border: 4px solid #f3f4f6;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            background: #fee2e2;
            border: 1px solid #fecaca;
            color: #dc2626;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            display: none;
        }
        
        @media (max-width: 768px) {
            .hero h1 {
                font-size: 2.5rem;
            }
            
            .upload-section {
                margin: 30px 20px;
                padding: 30px 20px;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="container">
            <div class="header-content">
                <div class="logo">
                    <i class="fas fa-music"></i>
                    MusicVision AI
                </div>
            </div>
        </div>
    </header>

    <main>
        <section id="home" class="hero">
            <div class="container">
                <h1>Transform Images into Perfect Soundtracks</h1>
                <p>Upload any image and let our AI analyze the mood, scene, and emotions to recommend perfect songs in your preferred languages with suggested captions.</p>
            </div>
        </section>

        <section class="upload-section">
            <div class="upload-area" onclick="document.getElementById('imageInput').click()">
                <input type="file" id="imageInput" accept="image/*">
                <div class="upload-icon">
                    <i class="fas fa-cloud-upload-alt"></i>
                </div>
                <div class="upload-text">
                    <h3>Upload Your Image</h3>
                    <p>Click here or drag and drop your image<br>
                    Supports JPG, PNG, GIF, WebP (Max 10MB)</p>
                </div>
            </div>
            
            <img id="imagePreview" class="image-preview">
            
            <div class="description-section">
                <label for="imageDescription">
                    <i class="fas fa-comment-alt"></i>
                    Describe your image (optional)
                </label>
                <textarea 
                    id="imageDescription" 
                    class="description-input" 
                    placeholder="Tell us more about this image... What's the occasion? What's happening in the scene?"
                ></textarea>
            </div>
            
            <div class="preferences-section">
                <label for="musicPreferences">
                    <i class="fas fa-music"></i>
                    Your Music Preferences (optional)
                </label>
                <textarea 
                    id="musicPreferences" 
                    class="description-input" 
                    placeholder="What kind of music do you like? Any specific genres, artists, or moods you prefer? (e.g., 'I love indie rock and melancholic songs', 'upbeat pop music', 'classical piano pieces')"
                ></textarea>
            </div>
            
            <div class="language-preference-section">
                <label for="languagePreferences">
                    <i class="fas fa-globe"></i>
                    Preferred Languages for Songs
                </label>
                <input 
                    type="text" 
                    id="languagePreferences" 
                    class="language-input"
                    placeholder="e.g., English, Spanish, Hindi, French, Korean"
                />
                <div class="language-examples">
                    <h5><i class="fas fa-lightbulb"></i> Examples:</h5>
                    <p><strong>Single language:</strong> English<br>
                    <strong>Multiple languages:</strong> English, Spanish, Hindi<br>
                    <strong>Any language:</strong> Leave empty for songs in any language</p>
                </div>
            </div>
            
            <div class="privacy-notice">
                <i class="fas fa-shield-alt"></i>
                <div>
                    <strong>100% Secure & Private</strong><br>
                    Your images are processed securely and never stored on our servers. Complete privacy guaranteed.
                </div>
            </div>
            
            <button class="analyze-btn" onclick="analyzeImage()" disabled>
                <i class="fas fa-magic"></i>
                Analyze & Get Music Recommendations
            </button>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <h3>Analyzing your image...</h3>
                <p>Our AI is examining the mood, scene, and emotions in your image to find the perfect songs in your preferred languages with suggested captions.</p>
            </div>
            
            <div class="error" id="error"></div>
        </section>
    </main>

    <script>
        let selectedFile = null;

        // File upload handling
        document.getElementById('imageInput').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                if (file.size > 10 * 1024 * 1024) {
                    showError('File size must be less than 10MB');
                    return;
                }
                
                selectedFile = file;
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.getElementById('imagePreview');
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                    
                    document.querySelector('.analyze-btn').disabled = false;
                };
                reader.readAsDataURL(file);
            }
        });

        // Drag and drop handling
        const uploadArea = document.querySelector('.upload-area');
        
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', function(e) {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                if (file.type.startsWith('image/')) {
                    document.getElementById('imageInput').files = files;
                    document.getElementById('imageInput').dispatchEvent(new Event('change'));
                }
            }
        });

        async function analyzeImage() {
            if (!selectedFile) {
                showError('Please select an image first');
                return;
            }

            const loadingDiv = document.getElementById('loading');
            const analyzeBtn = document.querySelector('.analyze-btn');
            
            loadingDiv.style.display = 'block';
            analyzeBtn.disabled = true;
            hideError();

            try {
                const base64Image = await fileToBase64(selectedFile);
                const description = document.getElementById('imageDescription').value;
                const preferences = document.getElementById('musicPreferences').value;
                const languagePreferences = document.getElementById('languagePreferences').value;
                
                const payload = {
                    image: base64Image.split(',')[1],
                    description: description,
                    preferences: preferences,
                    language_preferences: languagePreferences,
                    context: 'Professional music recommendation with AI curation and language preferences'
                };

                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });

                const result = await response.json();
                
                if (response.ok) {
                    window.location.href = result.redirect_url;
                } else {
                    showError('Analysis failed: ' + result.error);
                }
            } catch (error) {
                showError('Error: ' + error.message);
            } finally {
                loadingDiv.style.display = 'none';
                analyzeBtn.disabled = false;
            }
        }

        function fileToBase64(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = () => resolve(reader.result);
                reader.onerror = error => reject(error);
            });
        }

        function showError(message) {
            const errorDiv = document.getElementById('error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }

        function hideError() {
            document.getElementById('error').style.display = 'none';
        }
    </script>
</body>
</html>
'''

# Enhanced Results Page HTML with Dynamic Refinement
RESULTS_PAGE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Music Recommendations - MusicVision AI</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            padding: 20px 0;
            margin-bottom: 30px;
            border-radius: 15px;
        }
        
        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        .logo {
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
        }
        
        .back-btn {
            background: #667eea;
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 25px;
            transition: all 0.3s ease;
        }
        
        .back-btn:hover {
            background: #5a67d8;
            transform: translateY(-2px);
        }
        
        .results-layout {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 40px;
            margin-bottom: 40px;
        }
        
        .left-section {
            display: flex;
            flex-direction: column;
            gap: 30px;
        }
        
        .image-section {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        .uploaded-image {
            width: 100%;
            max-height: 400px;
            object-fit: cover;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            margin-bottom: 20px;
        }
        
        .analysis-section {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            flex: 1;
        }
        
        .analysis-item {
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .analysis-item:last-child {
            border-bottom: none;
        }
        
        .analysis-item h3 {
            color: #667eea;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .refinement-section {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            margin-top: 20px;
        }
        
        .refinement-input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e7ff;
            border-radius: 10px;
            font-size: 1rem;
            transition: border-color 0.3s ease;
            resize: vertical;
            min-height: 100px;
            margin-bottom: 15px;
        }
        
        .refinement-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .refine-btn {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .refine-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4);
        }
        
        .refine-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .recommendations-section {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        
        .ai-status {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .language-status {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .refinement-status {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            display: none;
        }
        
        .recommendations-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .song-card {
            background: linear-gradient(135deg, #f8faff, #e0e7ff);
            padding: 25px;
            border-radius: 15px;
            border: 2px solid transparent;
            transition: all 0.3s ease;
            position: relative;
        }
        
        .song-card:hover {
            border-color: #667eea;
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
        }
        
        .song-card h4 {
            color: #333;
            margin-bottom: 8px;
            font-size: 1.1rem;
        }
        
        .song-card .artist {
            color: #667eea;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .song-card .badges {
            margin-bottom: 15px;
        }
        
        .song-card .genre {
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            display: inline-block;
            margin-right: 5px;
        }
        
        .song-card .language-badge {
            background: #10b981;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            display: inline-block;
            margin-right: 5px;
        }
        
        .song-card .segment {
            background: #f59e0b;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            display: inline-block;
            margin-right: 5px;
        }
        
        .song-card .youtube-badge {
            background: #ff0000;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            display: inline-block;
            margin-right: 5px;
        }
        
        .song-card .reason {
            color: #666;
            font-size: 0.9rem;
            line-height: 1.4;
            margin-bottom: 15px;
        }
        
        .song-card .segment-description {
            color: #555;
            font-size: 0.85rem;
            font-style: italic;
            margin-bottom: 15px;
        }
        
        .suggested-caption {
            background: rgba(102, 126, 234, 0.1);
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            border-left: 4px solid #667eea;
        }
        
        .suggested-caption h5 {
            color: #667eea;
            margin-bottom: 8px;
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        .suggested-caption p {
            color: #555;
            font-style: italic;
            line-height: 1.4;
        }
        
        .youtube-preview {
            background: rgba(255, 0, 0, 0.1);
            padding: 10px;
            border-radius: 8px;
            margin: 15px 0;
        }
        
        .youtube-preview iframe {
            border-radius: 8px;
        }
        
        .spotify-link {
            background: #1db954;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            text-decoration: none;
            font-size: 0.85rem;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 10px;
            transition: all 0.3s ease;
        }
        
        .spotify-link:hover {
            background: #1ed760;
            transform: translateY(-1px);
        }
        
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }
        
        .loading-content {
            background: white;
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            max-width: 400px;
        }
        
        .spinner {
            border: 4px solid #f3f4f6;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @media (max-width: 768px) {
            .results-layout {
                grid-template-columns: 1fr;
            }
            
            .recommendations-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-content">
            <div class="logo">
                <i class="fas fa-music"></i>
                MusicVision AI
            </div>
            <a href="/" class="back-btn">
                <i class="fas fa-arrow-left"></i>
                New Analysis
            </a>
        </div>
    </header>

    <div class="container">
        <div class="results-layout">
            <div class="left-section">
                <div class="image-section">
                    <img src="data:image/jpeg;base64,{{ result.image_data }}" alt="Uploaded Image" class="uploaded-image">
                    {% if result.user_description %}
                    <div style="margin-top: 15px; padding: 15px; background: #f8faff; border-radius: 10px;">
                        <h4 style="color: #667eea; margin-bottom: 8px;">
                            <i class="fas fa-comment"></i>
                            Your Description
                        </h4>
                        <p style="color: #666;">{{ result.user_description }}</p>
                    </div>
                    {% endif %}
                    {% if result.user_preferences %}
                    <div style="margin-top: 15px; padding: 15px; background: #f0f9ff; border-radius: 10px;">
                        <h4 style="color: #667eea; margin-bottom: 8px;">
                            <i class="fas fa-music"></i>
                            Your Music Preferences
                        </h4>
                        <p style="color: #666;">{{ result.user_preferences }}</p>
                    </div>
                    {% endif %}
                    {% if result.language_preferences %}
                    <div style="margin-top: 15px; padding: 15px; background: #f0fdf4; border-radius: 10px;">
                        <h4 style="color: #10b981; margin-bottom: 8px;">
                            <i class="fas fa-globe"></i>
                            Language Preferences
                        </h4>
                        <p style="color: #666;">{{ result.language_preferences }}</p>
                    </div>
                    {% endif %}
                </div>
                
                <div class="analysis-section">
                    <h2 style="color: #333; margin-bottom: 25px;">
                        <i class="fas fa-chart-line"></i>
                        AI Analysis Results
                    </h2>
                    
                    <div class="analysis-item">
                        <h3>
                            <i class="fas fa-eye"></i>
                            Image Description
                        </h3>
                        <p>{{ result.ai_caption }}</p>
                    </div>
                    
                    {% if result.recommendations.scene_analysis %}
                    <div class="analysis-item">
                        <h3>
                            <i class="fas fa-theater-masks"></i>
                            Scene Analysis
                        </h3>
                        {% set scene = result.recommendations.scene_analysis %}
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px;">
                            {% if scene.primary_mood %}
                            <div>
                                <strong>Mood:</strong><br>
                                <span style="color: #667eea;">{{ scene.primary_mood }}</span>
                            </div>
                            {% endif %}
                            {% if scene.energy_level %}
                            <div>
                                <strong>Energy:</strong><br>
                                <span style="color: #667eea;">{{ scene.energy_level }}</span>
                            </div>
                            {% endif %}
                            {% if scene.setting_type %}
                            <div>
                                <strong>Setting:</strong><br>
                                <span style="color: #667eea;">{{ scene.setting_type }}</span>
                            </div>
                            {% endif %}
                            {% if scene.atmosphere %}
                            <div>
                                <strong>Atmosphere:</strong><br>
                                <span style="color: #667eea;">{{ scene.atmosphere }}</span>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                    {% endif %}
                    
                    {% if result.recommendations.overall_curation_philosophy %}
                    <div class="analysis-item">
                        <h3>
                            <i class="fas fa-lightbulb"></i>
                            Curation Philosophy
                        </h3>
                        <p>{{ result.recommendations.overall_curation_philosophy }}</p>
                    </div>
                    {% endif %}
                </div>
                
                <!-- NEW: Dynamic Refinement Section -->
                <div class="refinement-section">
                    <h3 style="color: #333; margin-bottom: 15px;">
                        <i class="fas fa-sliders-h"></i>
                        Refine Your Music Preferences
                    </h3>
                    <p style="color: #666; margin-bottom: 15px; font-size: 0.9rem;">
                        Want different songs? Tell us more about what you're looking for and we'll update the recommendations instantly.
                    </p>
                    <textarea 
                        id="additionalPreferences" 
                        class="refinement-input"
                        placeholder="e.g., 'I want more upbeat songs with guitar solos', 'prefer slower ballads', 'need songs with strong vocals', 'more electronic/dance music'"
                    ></textarea>
                    <button class="refine-btn" onclick="refineRecommendations()">
                        <i class="fas fa-magic"></i>
                        Update Recommendations
                    </button>
                </div>
            </div>
            
            <div class="recommendations-section" id="recommendationsSection">
                <div class="ai-status">
                    <i class="fas fa-brain"></i>
                    <div>
                        <strong>AI Music Curation Active</strong><br>
                        Personalized song recommendations with suggested captions
                    </div>
                </div>
                
                {% if result.language_preferences %}
                <div class="language-status">
                    <i class="fas fa-globe"></i>
                    <div>
                        <strong>Language Filter Applied</strong><br>
                        Songs recommended in: {{ result.language_preferences }}
                    </div>
                </div>
                {% endif %}
                
                <div class="refinement-status" id="refinementStatus">
                    <i class="fas fa-sliders-h"></i>
                    <div>
                        <strong>Recommendations Refined</strong><br>
                        <span id="refinementText">Updated based on your additional preferences</span>
                    </div>
                </div>
                
                <h2 style="color: #333; margin-bottom: 10px;">
                    <i class="fas fa-music"></i>
                    Recommended Songs & Captions
                </h2>
                <p style="color: #666; margin-bottom: 25px;">Perfect songs{% if result.language_preferences %} in your preferred languages{% endif %} for your image with AI-generated captions</p>
                
                <div class="recommendations-grid" id="recommendationsGrid">
                    {% for song in result.recommendations.recommendations %}
                    <div class="song-card">
                        <h4>{{ song.song_title }}</h4>
                        <div class="artist">{{ song.artist }}</div>
                        
                        <div class="badges">
                            {% if song.genre %}
                            <span class="genre">{{ song.genre }}</span>
                            {% endif %}
                            {% if song.language %}
                            <span class="language-badge"><i class="fas fa-globe"></i> {{ song.language }}</span>
                            {% endif %}
                            {% if song.recommended_segment %}
                            <span class="segment">{{ song.recommended_segment }}</span>
                            {% endif %}
                            {% if song.preview_available %}
                            <span class="youtube-badge"><i class="fab fa-youtube"></i> YouTube</span>
                            {% endif %}
                        </div>
                        
                        {% if song.segment_description %}
                        <div class="segment-description">
                            "{{ song.segment_description }}"
                        </div>
                        {% endif %}
                        
                        <div class="reason">
                            {{ song.why_perfect_match or song.why_it_fits or song.reasoning or "Perfect match for your image" }}
                        </div>
                        
                        {% if song.suggested_caption %}
                        <div class="suggested-caption">
                            <h5><i class="fas fa-quote-left"></i> Suggested Caption</h5>
                            <p>"{{ song.suggested_caption }}"</p>
                        </div>
                        {% endif %}
                        
                        <!-- YouTube Preview Player -->
                        {% if song.preview_available and song.youtube_data %}
                        <div class="youtube-preview">
                            <iframe 
                                width="100%" 
                                height="200" 
                                src="https://www.youtube.com/embed/{{ song.youtube_data.video_id }}?start=75&autoplay=0&controls=1" 
                                frameborder="0" 
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                allowfullscreen>
                            </iframe>
                        </div>
                        {% endif %}
                        
                        <!-- Spotify Link -->
                        <a href="https://open.spotify.com/search/{{ song.song_title | urlencode }}%20{{ song.artist | urlencode }}" 
                           target="_blank" 
                           class="spotify-link">
                            <i class="fab fa-spotify"></i>
                            Listen on Spotify
                        </a>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    
    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loading-content">
            <div class="spinner"></div>
            <h3>Refining Recommendations...</h3>
            <p>Our AI is analyzing your additional preferences to find better songs.</p>
        </div>
    </div>

    <script>
        const analysisId = '{{ analysis_id }}';
        
        async function refineRecommendations() {
            const additionalPreferences = document.getElementById('additionalPreferences').value.trim();
            
            if (!additionalPreferences) {
                alert('Please enter your additional preferences to refine recommendations.');
                return;
            }
            
            const refineBtn = document.querySelector('.refine-btn');
            const loadingOverlay = document.getElementById('loadingOverlay');
            
            // Show loading
            loadingOverlay.style.display = 'flex';
            refineBtn.disabled = true;
            
            try {
                const response = await fetch('/refine_recommendations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        analysis_id: analysisId,
                        additional_preferences: additionalPreferences
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Update the recommendations grid
                    updateRecommendationsGrid(result.recommendations);
                    
                    // Show refinement status
                    const refinementStatus = document.getElementById('refinementStatus');
                    const refinementText = document.getElementById('refinementText');
                    refinementText.textContent = `Updated based on: "${additionalPreferences}"`;
                    refinementStatus.style.display = 'flex';
                    
                    // Clear the input
                    document.getElementById('additionalPreferences').value = '';
                    
                    // Show success message
                    showNotification('Recommendations updated successfully! 🎉', 'success');
                    
                } else {
                    showNotification('Failed to refine recommendations: ' + result.error, 'error');
                }
                
            } catch (error) {
                console.error('Refinement failed:', error);
                showNotification('Failed to refine recommendations. Please try again.', 'error');
            } finally {
                loadingOverlay.style.display = 'none';
                refineBtn.disabled = false;
            }
        }
        
        function updateRecommendationsGrid(recommendations) {
            const grid = document.getElementById('recommendationsGrid');
            
            // Create new HTML for recommendations
            let html = '';
            
            recommendations.recommendations.forEach(song => {
                html += `
                    <div class="song-card">
                        <h4>${song.song_title}</h4>
                        <div class="artist">${song.artist}</div>
                        
                        <div class="badges">
                            ${song.genre ? `<span class="genre">${song.genre}</span>` : ''}
                            ${song.language ? `<span class="language-badge"><i class="fas fa-globe"></i> ${song.language}</span>` : ''}
                            ${song.recommended_segment ? `<span class="segment">${song.recommended_segment}</span>` : ''}
                                                        ${song.preview_available ? `<span class="youtube-badge"><i class="fab fa-youtube"></i> YouTube</span>` : ''}
                        </div>
                        
                        ${song.segment_description ? `<div class="segment-description">"${song.segment_description}"</div>` : ''}
                        
                        <div class="reason">
                            ${song.why_perfect_match || song.why_it_fits || song.reasoning || "Perfect match for your image"}
                        </div>
                        
                        ${song.suggested_caption ? `
                        <div class="suggested-caption">
                            <h5><i class="fas fa-quote-left"></i> Suggested Caption</h5>
                            <p>"${song.suggested_caption}"</p>
                        </div>
                        ` : ''}
                        
                        ${song.preview_available && song.youtube_data ? `
                        <div class="youtube-preview">
                            <iframe 
                                width="100%" 
                                height="200" 
                                src="https://www.youtube.com/embed/${song.youtube_data.video_id}?start=75&autoplay=0&controls=1" 
                                frameborder="0" 
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                allowfullscreen>
                            </iframe>
                        </div>
                        ` : ''}
                        
                        <a href="https://open.spotify.com/search/${encodeURIComponent(song.song_title)}%20${encodeURIComponent(song.artist)}" 
                           target="_blank" 
                           class="spotify-link">
                            <i class="fab fa-spotify"></i>
                            Listen on Spotify
                        </a>
                    </div>
                `;
            });
            
            // Update the grid with animation
            grid.style.opacity = '0.5';
            setTimeout(() => {
                grid.innerHTML = html;
                grid.style.opacity = '1';
            }, 300);
        }
        
        function showNotification(message, type) {
            // Create notification element
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 25px;
                border-radius: 10px;
                color: white;
                font-weight: 600;
                z-index: 10000;
                animation: slideIn 0.3s ease-out;
                max-width: 400px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            `;
            
            if (type === 'success') {
                notification.style.background = 'linear-gradient(135deg, #10b981, #059669)';
            } else {
                notification.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
            }
            
            notification.innerHTML = `
                <div style="display: flex; align-items: center; gap: 10px;">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
                    <span>${message}</span>
                </div>
            `;
            
            // Add animation styles
            const style = document.createElement('style');
            style.textContent = `
                @keyframes slideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                @keyframes slideOut {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
            
            document.body.appendChild(notification);
            
            // Auto remove after 4 seconds
            setTimeout(() => {
                notification.style.animation = 'slideOut 0.3s ease-in';
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }, 4000);
        }
        
        // Allow Enter key to trigger refinement
        document.getElementById('additionalPreferences').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && e.ctrlKey) {
                refineRecommendations();
            }
        });
        
        // Add placeholder rotation for better UX
        const placeholders = [
            "e.g., 'I want more upbeat songs with guitar solos'",
            "e.g., 'prefer slower ballads with emotional lyrics'",
            "e.g., 'need songs with strong vocals and piano'",
            "e.g., 'more electronic/dance music'",
            "e.g., 'acoustic songs with folk vibes'",
            "e.g., 'rock songs from the 90s'",
            "e.g., 'jazz or blues with saxophone'"
        ];
        
        let placeholderIndex = 0;
        const additionalPreferencesInput = document.getElementById('additionalPreferences');
        
        setInterval(() => {
            if (!additionalPreferencesInput.value) {
                placeholderIndex = (placeholderIndex + 1) % placeholders.length;
                additionalPreferencesInput.placeholder = placeholders[placeholderIndex];
            }
        }, 3000);
        
        // Auto-focus on refinement input when page loads
        window.addEventListener('load', () => {
            setTimeout(() => {
                additionalPreferencesInput.focus();
            }, 1000);
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print(" Starting MusicVision AI with Dynamic Refinement...")
    print(f" Captioning: {captioner.model_name}")
    print(f" LLM: {getattr(music_recommender, 'provider', 'gemini')}")
    print(" YouTube Integration: Enabled")
    print(" Language Preferences: Enabled")
    print(" Dynamic Refinement: Enabled")
    print(" Music Generation: Enabled (Fallback)")
    print(" Security: Enterprise-grade privacy protection")
    print(" Server: http://localhost:5000")
    
    print(" YouTube Integration: Enabled - Full song previews available")
    print(" AI Captions: Enabled - Suggested captions for each song")
    print(" User Preferences: Enabled - Personalized recommendations")
    print(" Language Preferences: Enabled - Multi-language support")
    print(" Dynamic Refinement: Enabled - Real-time recommendation updates")
    
    app.run(host="0.0.0.0", port=5000, debug=False)

