from flask import Flask, request, jsonify, render_template_string, redirect, url_for, send_file
from flask_cors import CORS
import base64
from io import BytesIO
import secrets
import time
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
        
        # Combine AI caption with user description
        full_description = caption
        if image_description.strip():
            full_description = f"{caption}. User notes: {image_description}"
        
        # Step 2: Get LLM music recommendations
        logger.info(" Getting LLM music recommendations...")
        recommendations = music_recommender.recommend_songs(
            full_description, context, 8
        )
        
        # Store results
        analysis_results[analysis_id] = {
            'image_data': data['image'],  # Store base64 for display
            'user_description': image_description,
            'ai_caption': caption,
            'full_description': full_description,
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

@app.route('/composition/<analysis_id>/<int:song_index>')
def show_composition(analysis_id, song_index):
    """Show final composition page with music player"""
    if analysis_id not in analysis_results:
        return redirect(url_for('home'))
    
    result = analysis_results[analysis_id]
    
    if song_index >= len(result['recommendations'].get('recommendations', [])):
        return redirect(url_for('show_results', analysis_id=analysis_id))
    
    selected_song = result['recommendations']['recommendations'][song_index]
    
    # Generate background music based on scene analysis
    scene_analysis = result['recommendations'].get('scene_analysis', {})
    mood = scene_analysis.get('primary_mood', 'happy')
    
    # Generate 30-second background music
    background_music = music_generator.generate_background_music(mood)
    
    return render_template_string(COMPOSITION_PAGE_HTML, 
                                result=result, 
                                selected_song=selected_song, 
                                analysis_id=analysis_id,
                                song_index=song_index,
                                background_music=background_music)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Professional Image to Music Recommendation API with Music Generation',
        'models': {
            'captioning': captioner.model_name,
            'llm': getattr(music_recommender, 'provider', 'gemini')
        }
    })

# Home Page HTML
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
        
        .nav-links {
            display: flex;
            gap: 30px;
            list-style: none;
        }
        
        .nav-links a {
            text-decoration: none;
            color: #333;
            font-weight: 500;
            transition: color 0.3s ease;
        }
        
        .nav-links a:hover {
            color: #667eea;
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
        
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 50px;
            margin: 80px 0;
            padding: 80px 0;
        }
        
        .feature-card {
            background: rgba(255, 255, 255, 0.95);
            padding: 50px 30px;
            border-radius: 20px;
            text-align: center;
            backdrop-filter: blur(20px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
        }
        
        .feature-icon {
            font-size: 3rem;
            color: #667eea;
            margin-bottom: 30px;
        }
        
        .feature-card h3 {
            font-size: 1.3rem;
            margin-bottom: 20px;
            color: #333;
        }
        
        .feature-card p {
            color: #666;
            line-height: 1.6;
        }
        
        .about-section {
            background: rgba(255, 255, 255, 0.95);
            padding: 80px 50px;
            border-radius: 20px;
            margin: 80px auto;
            max-width: 800px;
            text-align: center;
            backdrop-filter: blur(20px);
        }
        
        .contact-section {
            background: rgba(255, 255, 255, 0.95);
            padding: 80px 50px;
            border-radius: 20px;
            margin: 80px auto;
            max-width: 800px;
            text-align: center;
            backdrop-filter: blur(20px);
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
            
            .nav-links {
                display: none;
            }
            
            .features {
                gap: 30px;
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
                <nav>
                    <ul class="nav-links">
                        <li><a href="#home">Home</a></li>
                        <li><a href="#features">Features</a></li>
                        <li><a href="#about">About</a></li>
                        <li><a href="#contact">Contact</a></li>
                    </ul>
                </nav>
            </div>
        </div>
    </header>

    <main>
        <section id="home" class="hero">
            <div class="container">
                <h1>Transform Images into Perfect Soundtracks</h1>
                <p>Upload any image and let our AI analyze the mood, scene, and emotions to recommend perfect 30-second music segments for your Instagram stories.</p>
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
                    placeholder="Tell us more about this image... What's the occasion? What mood are you going for? Any specific genre preferences?"
                ></textarea>
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
                <p>Our AI is examining the mood, scene, and emotions in your image to find the perfect 30-second music segments.</p>
            </div>
            
            <div class="error" id="error"></div>
        </section>

        <section id="features" class="features">
            <div class="container">
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-brain"></i>
                    </div>
                    <h3>AI-Powered Analysis</h3>
                    <p>Advanced computer vision and natural language processing to understand your image's mood, setting, and emotional context with unprecedented accuracy.</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-music"></i>
                    </div>
                    <h3>30-Second Song Segments</h3>
                    <p>Get personalized 30-second music segments from popular songs, perfectly matched to your image's vibe and optimized for Instagram stories.</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-instagram"></i>
                    </div>
                    <h3>Instagram Story Ready</h3>
                    <p>Create and download beautiful Instagram story compositions with background music, ready to post and share with your followers.</p>
                </div>
            </div>
        </section>

        <section id="about" class="about-section">
            <h2 style="color: #667eea; margin-bottom: 30px; font-size: 2.5rem;">About MusicVision AI</h2>
            <p style="font-size: 1.2rem; line-height: 1.8; color: #666; margin-bottom: 30px;">
                MusicVision AI is a cutting-edge platform that bridges the gap between visual content and musical expression. 
                Using state-of-the-art artificial intelligence, we analyze the emotional depth, contextual elements, and 
                aesthetic qualities of your images to recommend 30-second music segments that perfectly complement your visual story.
            </p>
            <p style="font-size: 1.1rem; line-height: 1.6; color: #666;">
                Whether you're a content creator, social media enthusiast, or simply someone who loves the intersection 
                of visual and auditory art, our platform provides you with the tools to create meaningful, emotionally 
                resonant compositions that tell your story in both sight and sound.
            </p>
        </section>

        <section id="contact" class="contact-section">
            <h2 style="color: #667eea; margin-bottom: 30px; font-size: 2.5rem;">Get in Touch</h2>
            <p style="font-size: 1.2rem; line-height: 1.8; color: #666; margin-bottom: 30px;">
                Have questions, feedback, or suggestions? We'd love to hear from you!
            </p>
            <div style="display: flex; justify-content: center; gap: 30px; flex-wrap: wrap;">
                <div style="text-align: center;">
                    <i class="fas fa-envelope" style="font-size: 2rem; color: #667eea; margin-bottom: 10px;"></i>
                    <p style="color: #666;">hello@musicvision.ai</p>
                </div>
                <div style="text-align: center;">
                    <i class="fas fa-phone" style="font-size: 2rem; color: #667eea; margin-bottom: 10px;"></i>
                    <p style="color: #666;">+1 (555) 123-4567</p>
                </div>
                <div style="text-align: center;">
                    <i class="fas fa-map-marker-alt" style="font-size: 2rem; color: #667eea; margin-bottom: 10px;"></i>
                    <p style="color: #666;">San Francisco, CA</p>
                </div>
            </div>
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
                
                const payload = {
                    image: base64Image.split(',')[1],
                    description: description,
                    context: 'Professional music recommendation'
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

# Results Page HTML
RESULTS_PAGE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis Results - MusicVision AI</title>
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
        
        .recommendations-section {
            background: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        
        .recommendations-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .song-card {
            background: linear-gradient(135deg, #f8faff, #e0e7ff);
            padding: 25px;
            border-radius: 15px;
            border: 2px solid transparent;
            transition: all 0.3s ease;
            cursor: pointer;
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
        
        .song-card .genre {
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            display: inline-block;
            margin-bottom: 10px;
        }
        
        .song-card .segment {
            background: #10b981;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            display: inline-block;
            margin-bottom: 10px;
            margin-left: 10px;
        }
        
        .song-card .reason {
            color: #666;
            font-size: 0.9rem;
            line-height: 1.4;
            margin-bottom: 10px;
        }
        
        .song-card .segment-description {
            color: #555;
            font-size: 0.85rem;
            font-style: italic;
            margin-bottom: 10px;
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
            </div>
            
            <div class="recommendations-section">
                <h2 style="color: #333; margin-bottom: 10px;">
                    <i class="fas fa-music"></i>
                    Recommended 30-Second Song Segments
                </h2>
                <p style="color: #666; margin-bottom: 25px;">Click on any song segment to create your Instagram story composition</p>
                
                <div class="recommendations-grid">
                    {% for song in result.recommendations.recommendations %}
                    <div class="song-card" onclick="selectSong({{ loop.index0 }})">
                        <h4>{{ song.song_title }}</h4>
                        <div class="artist">{{ song.artist }}</div>
                        <div style="margin-bottom: 10px;">
                            {% if song.genre %}
                            <span class="genre">{{ song.genre }}</span>
                            {% endif %}
                            {% if song.recommended_segment %}
                            <span class="segment">{{ song.recommended_segment }}</span>
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
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <script>
        function selectSong(songIndex) {
            window.location.href = `/composition/{{ analysis_id }}/${songIndex}`;
        }
    </script>
</body>
</html>
'''

# Composition Page HTML
COMPOSITION_PAGE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Instagram Story Composition - MusicVision AI</title>
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
            max-width: 1000px;
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
            max-width: 1000px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        .logo {
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
        }
        
        .nav-buttons {
            display: flex;
            gap: 15px;
        }
        
        .nav-btn {
            background: #667eea;
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 25px;
            transition: all 0.3s ease;
            border: none;
            cursor: pointer;
        }
        
        .nav-btn:hover {
            background: #5a67d8;
            transform: translateY(-2px);
        }
        
        .composition-card {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        .story-preview {
            background: #000;
            border-radius: 15px;
            padding: 20px;
            margin: 30px auto;
            max-width: 400px;
            position: relative;
            aspect-ratio: 9/16;
            overflow: hidden;
        }
        
        .composition-image {
            width: 100%;
            height: 100%;
            object-fit: cover;
            border-radius: 10px;
        }
        
        .music-overlay {
            position: absolute;
            bottom: 20px;
            left: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 15px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .play-btn {
            background: #667eea;
            color: white;
            border: none;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            font-size: 1.2rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .play-btn:hover {
            transform: scale(1.1);
            background: #5a67d8;
        }
        
        .music-info {
            flex: 1;
            text-align: left;
        }
        
        .music-info .song-title {
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .music-info .artist {
            opacity: 0.8;
            font-size: 0.9rem;
        }
        
        .song-details {
            background: linear-gradient(135deg, #f8faff, #e0e7ff);
            padding: 30px;
            border-radius: 15px;
            margin: 30px 0;
        }
        
        .segment-info {
            background: #10b981;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            display: inline-block;
            margin: 15px 0;
            font-weight: 600;
        }
        
        .action-buttons {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 40px;
            flex-wrap: wrap;
        }
        
        .action-btn {
            padding: 15px 30px;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }
        
        .download-btn {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
        }
        
        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(16, 185, 129, 0.4);
        }
        
        .new-composition-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        
        .new-composition-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        
        .progress-bar {
            width: 100%;
            height: 4px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 2px;
            margin-top: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: #667eea;
            width: 0%;
            transition: width 0.1s ease;
        }
        
        @media (max-width: 768px) {
            .action-buttons {
                flex-direction: column;
                align-items: center;
            }
            
            .action-btn {
                width: 100%;
                max-width: 300px;
                justify-content: center;
            }
            
            .nav-buttons {
                flex-direction: column;
                gap: 10px;
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
            <div class="nav-buttons">
                <a href="/results/{{ analysis_id }}" class="nav-btn">
                    <i class="fas fa-arrow-left"></i>
                    Back to Results
                </a>
                <a href="/" class="nav-btn">
                    <i class="fas fa-plus"></i>
                    New Analysis
                </a>
            </div>
        </div>
    </header>

    <div class="container">
        <div class="composition-card">
            <h1 style="color: #333; margin-bottom: 30px;">
                <i class="fas fa-instagram"></i>
                Your Instagram Story Composition
            </h1>
            
            <div class="story-preview">
                <img src="data:image/jpeg;base64,{{ result.image_data }}" alt="Your Image" class="composition-image">
                
                <div class="music-overlay">
                    <button class="play-btn" onclick="toggleMusic()">
                        <i class="fas fa-play" id="playIcon"></i>
                    </button>
                    <div class="music-info">
                        <div class="song-title">{{ selected_song.song_title }}</div>
                        <div class="artist">{{ selected_song.artist }}</div>
                    </div>
                    <div style="color: #667eea;">
                        <i class="fas fa-music"></i>
                    </div>
                </div>
                
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
            </div>
            
            <div class="song-details">
                <h3 style="color: #333; margin-bottom: 15px;">Selected Song Segment</h3>
                <h4 style="color: #667eea; margin-bottom: 10px;">{{ selected_song.song_title }} - {{ selected_song.artist }}</h4>
                {% if selected_song.recommended_segment %}
                <div class="segment-info">
                    <i class="fas fa-clock"></i>
                    {{ selected_song.recommended_segment }} (30 seconds)
                </div>
                {% endif %}
                {% if selected_song.segment_description %}
                <p style="color: #666; font-style: italic; margin: 15px 0;">
                    "{{ selected_song.segment_description }}"
                </p>
                {% endif %}
                <p style="color: #666; margin-top: 15px;">
                    {{ selected_song.why_perfect_match or selected_song.why_it_fits or selected_song.reasoning }}
                </p>
            </div>
            
            <div class="action-buttons">
                <button class="action-btn download-btn" onclick="downloadInstagramStory()">
                    <i class="fas fa-download"></i>
                    Download Instagram Story
                </button>
                
                <a href="/" class="action-btn new-composition-btn">
                    <i class="fas fa-plus-circle"></i>
                    Create New Composition
                </a>
            </div>
        </div>
    </div>

    <!-- Audio element for background music -->
    <audio id="backgroundMusic" loop>
        <source src="data:audio/wav;base64,{{ background_music }}" type="audio/wav">
        Your browser does not support the audio element.
    </audio>

    <script>
        let isPlaying = false;
        let progressInterval;
        const audio = document.getElementById('backgroundMusic');
        const playIcon = document.getElementById('playIcon');
        const progressFill = document.getElementById('progressFill');

        function toggleMusic() {
            if (isPlaying) {
                audio.pause();
                playIcon.className = 'fas fa-play';
                clearInterval(progressInterval);
            } else {
                audio.play();
                playIcon.className = 'fas fa-pause';
                startProgressBar();
            }
            isPlaying = !isPlaying;
        }

        function startProgressBar() {
            progressInterval = setInterval(() => {
                if (audio.duration) {
                    const progress = (audio.currentTime / audio.duration) * 100;
                    progressFill.style.width = progress + '%';
                    
                    if (audio.ended) {
                        playIcon.className = 'fas fa-play';
                        isPlaying = false;
                        progressFill.style.width = '0%';
                        clearInterval(progressInterval);
                    }
                }
            }, 100);
        }

        async function downloadInstagramStory() {
            try {
                // Show loading state
                const downloadBtn = document.querySelector('.download-btn');
                const originalText = downloadBtn.innerHTML;
                downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
                downloadBtn.disabled = true;

                // Create canvas for Instagram story (1080x1920)
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = 1080;
                canvas.height = 1920;

                // Fill background
                ctx.fillStyle = '#000000';
                ctx.fillRect(0, 0, canvas.width, canvas.height);

                // Load and draw image
                const img = new Image();
                img.onload = function() {
                    // Calculate dimensions to fit Instagram story format
                    const imgAspect = img.width / img.height;
                    const canvasAspect = canvas.width / canvas.height;
                    
                    let drawWidth, drawHeight, drawX, drawY;
                    
                    if (imgAspect > canvasAspect) {
                        drawHeight = canvas.height * 0.8; // Leave space for music info
                        drawWidth = drawHeight * imgAspect;
                        drawX = (canvas.width - drawWidth) / 2;
                        drawY = (canvas.height * 0.8 - drawHeight) / 2;
                    } else {
                        drawWidth = canvas.width * 0.9;
                        drawHeight = drawWidth / imgAspect;
                        drawX = (canvas.width - drawWidth) / 2;
                        drawY = (canvas.height * 0.8 - drawHeight) / 2;
                    }
                    
                    ctx.drawImage(img, drawX, drawY, drawWidth, drawHeight);
                    
                    // Add music info overlay
                    const overlayY = canvas.height * 0.85;
                    const overlayHeight = canvas.height * 0.15;
                    
                    // Semi-transparent overlay
                    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
                    ctx.fillRect(0, overlayY, canvas.width, overlayHeight);
                    
                    // Music icon
                    ctx.fillStyle = '#667eea';
                    ctx.font = 'bold 60px Arial';
                    ctx.fillText('♪', 60, overlayY + 80);
                    
                    // Song title
                    ctx.fillStyle = '#ffffff';
                    ctx.font = 'bold 48px Arial';
                    ctx.fillText('{{ selected_song.song_title }}', 150, overlayY + 60);
                    
                    // Artist
                    ctx.fillStyle = '#cccccc';
                    ctx.font = '36px Arial';
                    ctx.fillText('{{ selected_song.artist }}', 150, overlayY + 110);
                    
                    {% if selected_song.recommended_segment %}
                    // Segment info
                    ctx.fillStyle = '#10b981';
                    ctx.font = '32px Arial';
                    ctx.fillText('{{ selected_song.recommended_segment }}', 150, overlayY + 150);
                    {% endif %}
                    
                    // Download
                    const link = document.createElement('a');
                    link.download = 'instagram-story-musicvision.png';
                    link.href = canvas.toDataURL('image/png');
                    link.click();
                    
                    // Reset button
                    downloadBtn.innerHTML = originalText;
                    downloadBtn.disabled = false;
                    
                    // Show success message
                    alert('Instagram story downloaded successfully! ');
                };
                
                img.src = document.querySelector('.composition-image').src;
                
            } catch (error) {
                console.error('Download failed:', error);
                alert('Download failed. Please try again.');
                
                // Reset button
                const downloadBtn = document.querySelector('.download-btn');
                downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download Instagram Story';
                downloadBtn.disabled = false;
            }
        }

        // Auto-play music when page loads (with user interaction)
        document.addEventListener('click', function() {
            if (!isPlaying) {
                toggleMusic();
            }
        }, { once: true });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print(" Starting Professional Image to Music Recommendation System with Music Generation...")
    print(f" Captioning: {captioner.model_name}")
    print(f" LLM: {getattr(music_recommender, 'provider', 'gemini')}")
    print(" Music Generation: Enabled")
    print(" Security: Enterprise-grade privacy protection")
    print(" Server: http://localhost:5000")
    
    app.run(host="0.0.0.0", port=5000, debug=False)
