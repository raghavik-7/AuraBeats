# MusicVision AI

A sophisticated web application that transforms images into personalized music recommendations using advanced AI technologies. The system analyzes visual content, understands context and emotions, and provides curated song suggestions with suggested captions for social media content.

## Overview

MusicVision AI combines computer vision, natural language processing, and music recommendation systems to create a comprehensive content creation tool. Users upload images and receive personalized music recommendations along with AI-generated captions optimized for social media platforms.

## Features

### Core Functionality
- **Image Analysis**: Advanced computer vision models (BLIP, GiT) for detailed image understanding
- **Music Recommendations**: AI-powered song curation using Gemini LLM and Spotify integration
- **Multi-language Support**: Recommendations in preferred languages with transliteration support
- **Dynamic Refinement**: Real-time recommendation updates based on user feedback
- **Caption Generation**: AI-generated social media captions for each recommended song

### Technical Features
- **YouTube Integration**: Embedded video previews for recommended songs
- **Spotify Integration**: Direct links to songs on Spotify
- **Security**: Enterprise-grade privacy protection with secure image processing
- **Responsive Design**: Modern, mobile-friendly web interface
- **Real-time Processing**: Instant analysis and recommendation generation

### User Experience
- **Drag & Drop Interface**: Intuitive image upload with preview
- **Copyable Captions**: One-click caption copying for social media
- **Preference Customization**: Detailed music and language preferences
- **Visual Feedback**: Loading states and progress indicators
- **Error Handling**: Graceful error recovery and user notifications

## Architecture

### Backend Components

#### Image Processing (`fixed_captioning.py`)
- **BLIP Model**: Primary image captioning using Salesforce BLIP
- **GiT Models**: Fallback models (GiT-Large, GiT-Base) for reliability
- **Error Handling**: Automatic model fallback and recovery
- **Multi-format Support**: Handles various image formats and sizes

#### Music Recommendation Engine (`gemini_music_recommender.py`)
- **Gemini LLM Integration**: Advanced language model for music curation
- **Spotify API**: Real-time song data and metadata retrieval
- **Keyword Generation**: Intelligent search term creation for music discovery
- **Recommendation Merging**: Combines AI suggestions with Spotify data
- **Scene Analysis**: Detailed mood and atmosphere analysis

#### Security Layer (`simple_security.py`)
- **Image Processing Security**: Secure handling of user uploads
- **Session Management**: Unique processing IDs for each analysis
- **Privacy Protection**: No permanent image storage
- **Rate Limiting**: Protection against abuse

#### Music Generation (`music_generator.py`)
- **Fallback System**: AI-generated music when external APIs are unavailable
- **Custom Compositions**: Unique musical pieces based on image analysis
- **Format Support**: Multiple audio output formats

### Frontend Components

#### Main Application (`app4.py`)
- **Flask Web Server**: RESTful API endpoints
- **CORS Support**: Cross-origin resource sharing enabled
- **Template Rendering**: Dynamic HTML generation
- **Session Management**: User session tracking and result storage

#### User Interface
- **Responsive Design**: Mobile-first approach with CSS Grid and Flexbox
- **Modern Styling**: Gradient backgrounds, smooth animations, and professional aesthetics
- **Interactive Elements**: Hover effects, loading states, and visual feedback
- **Accessibility**: Keyboard navigation and screen reader support

## Installation

### Prerequisites
- Python 3.8 or higher
- Git
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd image-music-ai
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install additional language models**
   ```bash
   pip install spacy
   python -m spacy download en_core_web_sm
   ```

5. **Set up environment variables**
   Create a `.env` file in the project root with the following variables:
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   ```

### API Keys Setup

#### Google Gemini API
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to your `.env` file

#### Spotify API
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new application
3. Copy Client ID and Client Secret
4. Add to your `.env` file

## Usage

### Starting the Application

1. **Activate virtual environment**
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Run the application**
   ```bash
   python app4.py
   ```

3. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

### Using the Application

1. **Upload Image**: Drag and drop or click to upload an image (JPG, PNG, GIF, WebP, max 10MB)

2. **Add Context** (Optional):
   - Describe your image
   - Specify music preferences
   - Choose preferred languages

3. **Analyze**: Click "Analyze & Get Music Recommendations"

4. **Review Results**: 
   - View AI-generated image description
   - Browse recommended songs with captions
   - Copy captions for social media use
   - Watch YouTube previews
   - Access Spotify links

5. **Refine Recommendations** (Optional):
   - Add additional preferences
   - Get updated recommendations in real-time

## API Endpoints

### Core Endpoints

- `GET /` - Main application interface
- `POST /analyze` - Image analysis and music recommendation
- `GET /results/<analysis_id>` - View analysis results
- `POST /refine_recommendations` - Update recommendations with additional preferences
- `GET /health` - System health check

### Request Format

#### Image Analysis
```json
{
  "image": "base64_encoded_image",
  "description": "Optional image description",
  "preferences": "Optional music preferences",
  "language_preferences": "Optional language preferences",
  "context": "Analysis context"
}
```

#### Refinement
```json
{
  "analysis_id": "unique_analysis_id",
  "additional_preferences": "Additional music preferences"
}
```

## Configuration

### Model Configuration

The application supports multiple image captioning models:

- **BLIP** (default): Most reliable for general use
- **GiT-Large**: Better for complex scenes
- **GiT-Base**: Fastest processing

Change models in `fixed_captioning.py`:
```python
captioner = ReliableImageCaptioner(model_name="blip")
```

### Performance Tuning

#### Memory Optimization
- Reduce batch sizes for lower memory usage
- Use CPU-only mode for systems without GPU
- Adjust model parameters in configuration files

#### Speed Optimization
- Enable GPU acceleration when available
- Use smaller models for faster processing
- Implement caching for repeated requests

## Development

### Project Structure
```
image-music-ai/
├── app4.py                    # Main Flask application
├── gemini_music_recommender.py # Music recommendation engine
├── fixed_captioning.py        # Image captioning system
├── simple_security.py         # Security and privacy layer
├── music_generator.py         # AI music generation
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
└── README.md                  # This file
```

### Testing

Run the test suite:
```bash
python test_system.py
```

Test individual components:
```bash
python debug_captioning.py
python debug_llm.py
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## Troubleshooting

### Common Issues

#### Model Loading Errors
- Ensure sufficient disk space for model downloads
- Check internet connection for model downloads
- Verify PyTorch installation

#### API Key Issues
- Verify API keys are correctly set in `.env` file
- Check API key permissions and quotas
- Ensure keys are not expired

#### Memory Issues
- Reduce image size before upload
- Use CPU-only mode if GPU memory is insufficient
- Close other applications to free memory

#### Performance Issues
- Enable GPU acceleration if available
- Use smaller models for faster processing
- Implement request caching

### Error Logs

Check application logs for detailed error information:
```bash
tail -f app.log
```

## Security Considerations

- **Image Privacy**: Images are processed in memory and not stored permanently
- **API Security**: All API keys are stored securely in environment variables
- **Input Validation**: Comprehensive validation of user inputs
- **Rate Limiting**: Protection against API abuse
- **HTTPS**: Use HTTPS in production environments

## Future Enhancements

- **Video Analysis**: Support for video content analysis
- **Advanced Filtering**: More granular music preference controls
- **Playlist Generation**: Automatic playlist creation
- **Social Integration**: Direct posting to social media platforms
- **Offline Mode**: Local processing without internet dependency
- **Mobile App**: Native mobile application development

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For technical support or questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the documentation

## Acknowledgments

- **Salesforce BLIP**: Image captioning model
- **Microsoft GiT**: Alternative captioning models
- **Google Gemini**: Language model for music curation
- **Spotify API**: Music data and metadata
- **YouTube API**: Video preview integration 
