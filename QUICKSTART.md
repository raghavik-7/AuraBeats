# Quick Start Guide

Get MusicVision AI running in 5 minutes!

## Prerequisites
- Python 3.8+
- Git

## Quick Setup

1. **Clone and setup**
   ```bash
   git clone <your-repo-url>
   cd image-music-ai
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Get API Keys**
   - [Google Gemini API](https://makersuite.google.com/app/apikey) - Free tier available
   - [Spotify API](https://developer.spotify.com/dashboard) - Free tier available

3. **Configure environment**
   ```bash
   cp env_template.txt .env
   # Edit .env with your API keys
   ```

4. **Run the application**
   ```bash
   python app4.py
   ```

5. **Open in browser**
   Navigate to: http://localhost:5000

## What's Next?

- Upload an image
- Add your preferences
- Get music recommendations with captions
- Copy captions for social media

## Need Help?

- Check the main [README.md](README.md) for detailed documentation
- Review the [troubleshooting section](README.md#troubleshooting)
- Create an issue if you encounter problems 