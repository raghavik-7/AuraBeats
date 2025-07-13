import google.generativeai as genai
import os
import json
import logging
from typing import Dict, Any
import time
import yt_dlp

logger = logging.getLogger(__name__)

class GeminiMusicRecommender:
    def __init__(self):
        """Initialize Gemini LLM for music recommendations with YouTube integration"""
        # Initialize Gemini
        self.setup_gemini()
        
        logger.info(" Gemini Music Recommender with YouTube integration initialized successfully")
    
    def setup_gemini(self):
        """Setup Gemini LLM"""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            api_key = input("Enter your Google API key: ")
            with open('.env', 'a') as f:
                f.write(f"\nGOOGLE_API_KEY={api_key}")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.provider = "gemini"
        logger.info(" Gemini LLM initialized successfully")
    
    def recommend_songs(self, image_caption: str, user_input: str = "", context: str = "", num_songs: int = 5, preferred_languages: str = "", additional_preferences: str = "") -> Dict[str, Any]:
        """Generate music recommendations based on image, user input, language preferences, and additional preferences"""
        
        # Combine all user inputs
        full_description = image_caption
        if user_input.strip():
            full_description = f"{image_caption}. Initial preferences: {user_input}"
        if additional_preferences.strip():
            full_description = f"{full_description}. Additional preferences: {additional_preferences}"
        
        # Build the prompt with all preferences
        prompt = f"""
You are a professional music curator and Instagram content creator. Based on this image description and user preferences, recommend {num_songs} specific, real songs.

IMAGE DESCRIPTION: "{image_caption}"
INITIAL USER PREFERENCES: "{user_input}"
ADDITIONAL USER PREFERENCES: "{additional_preferences}"
CONTEXT: "{context}"
"""

        # Add language preferences if provided
        if preferred_languages.strip():
            prompt += f"\nPREFERRED LANGUAGES FOR SONGS: {preferred_languages}\n"
            prompt += "IMPORTANT: Prioritize songs in the specified languages. If a language is specified, try to recommend songs primarily in those languages unless the mood/scene strongly suggests otherwise.\n"
        
        # Add additional preferences guidance
        if additional_preferences.strip():
            prompt += f"\nIMPORTANT: Pay special attention to the additional preferences: '{additional_preferences}'. These are refined preferences that should heavily influence your recommendations.\n"
        
        prompt += """
For each song, specify a 15-second segment that best matches the image's mood and create a natural Instagram caption that incorporates the song organically.

CAPTION GUIDELINES:
- Write like a real Instagram user would caption their post
- Focus on the emotion, moment, or story in the image
- Naturally mention the song as part of the mood/feeling
- Include relevant hashtags (2-4 hashtags maximum)
- Keep it authentic and relatable, not promotional
- The song should feel like the perfect soundtrack to the moment
- Examples of good caption style:
  * "Late night drives hit different when the city lights blur past your window. This track just gets it ✨ #NightVibes #CityLights"
  * "Sometimes you need that one song that makes you feel invincible. Feeling grateful for moments like these 🌅 #MorningMotivation #GoodVibes"
  * "Coffee shop mornings with this acoustic melody playing softly in the background. Perfect start to the day ☕ #MorningRitual #AcousticVibes"

Respond with this EXACT JSON format:
{
    "scene_analysis": {
        "primary_mood": "main emotional tone",
        "visual_elements": "key visual components",
        "atmosphere": "overall feeling/vibe",
        "energy_level": "low/medium/high",
        "setting_type": "indoor/outdoor/urban/nature/etc"
    },
    "recommendations": [
        {
            "song_title": "Exact Song Title",
            "artist": "Artist Name",
            "album": "Album Name (if known)",
            "genre": "Primary Genre",
            "language": "Song language (e.g., English, Spanish, Hindi, Korean)",
            "release_year": "Year (if known)",
            "why_perfect_match": "Why this song captures the scene's essence and matches user preferences",
            "mood_connection": "How the song's mood aligns with visual mood",
            "specific_elements": "Which visual elements and user preferences this song addresses",
            "recommended_segment": "Start and end time, e.g., 1:15-1:30",
            "segment_description": "What happens in this 15-second segment",
            "suggested_caption": "A natural Instagram caption that tells the story of the image while organically incorporating the song as the perfect soundtrack to the moment"
        }
    ],
    "overall_curation_philosophy": "Your approach to selecting these songs considering all user preferences",
    "alternative_direction": "If user wanted different mood, what direction",
    "preference_analysis": "How the additional preferences influenced your song selection"
}

Focus on POPULAR songs on INSTAGRAM likely available on YouTube. Create captions that feel authentic and natural, like real Instagram users would write them.
If additional preferences are provided, ensure they significantly influence your recommendations while maintaining relevance to the image.
"""
        
        try:
            logger.info(" Requesting Gemini music recommendations with all preferences...")
            if preferred_languages:
                logger.info(f"🌐 Language preferences: {preferred_languages}")
            if additional_preferences:
                logger.info(f" Additional preferences: {additional_preferences}")
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=3000,
                    top_p=0.9
                )
            )
            
            logger.info(" Gemini response received")
            
            # Parse the response
            recommendations = self._parse_gemini_response(response.text)
            
            # Add YouTube data for each song
            if 'recommendations' in recommendations:
                logger.info(" Adding YouTube data...")
                self._add_youtube_sources(recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f" Gemini recommendation failed: {e}")
            raise Exception(f"LLM recommendation failed: {e}")
    
    def _add_youtube_sources(self, recommendations):
        """Add YouTube data for each song"""
        for i, song in enumerate(recommendations.get('recommendations', [])):
            try:
                logger.info(f" Getting YouTube data for: {song.get('song_title', 'Unknown')} by {song.get('artist', 'Unknown')}")
                
                # Get YouTube data
                youtube_data = self._get_youtube_data(
                    song.get('song_title', ''),
                    song.get('artist', '')
                )
                
                if youtube_data:
                    song['preview_available'] = True
                    song['youtube_data'] = youtube_data
                    song['preview_source'] = 'youtube'
                    song['youtube_embed_url'] = f"https://www.youtube.com/embed/{youtube_data['video_id']}"
                    song['preview_note'] = "Full song from YouTube"
                    song['playback_type'] = 'full_song'
                    logger.info(f" YouTube data added: {song['song_title']}")
                else:
                    song['preview_available'] = False
                    song['preview_note'] = "Song not found on YouTube"
                    logger.warning(f" YouTube data not found: {song['song_title']}")
                
                # Add rate limiting delay
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f" Error getting YouTube data for {song.get('song_title', 'Unknown')}: {e}")
                song['preview_available'] = False
                song['preview_note'] = f"Error: {str(e)}"
    
    def _get_youtube_data(self, song_title: str, artist: str) -> dict:
        """Get YouTube data for the song"""
        try:
            search_query = f"{song_title} {artist} official audio"
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                search_results = ydl.extract_info(
                    f"ytsearch1:{search_query}",
                    download=False
                )
                
                if search_results and search_results.get('entries'):
                    video_info = search_results['entries'][0]
                    
                    return {
                        'video_id': video_info['id'],
                        'title': video_info['title'],
                        'uploader': video_info.get('uploader', 'Unknown'),
                        'duration': video_info.get('duration', 0),
                        'view_count': video_info.get('view_count', 0),
                        'youtube_url': f"https://www.youtube.com/watch?v={video_info['id']}",
                        'embed_url': f"https://www.youtube.com/embed/{video_info['id']}",
                        'thumbnail': video_info.get('thumbnail'),
                        'available': True,
                        'source': 'youtube'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"YouTube data error: {e}")
            return None
    
    def get_youtube_segment_on_demand(self, song_title: str, artist: str, start_time: str, duration: int = 15) -> dict:
        """Download YouTube segment only when requested"""
        try:
            from youtube_audio_processor import YouTubeAudioProcessor
            
            logger.info(f" On-demand: Downloading {song_title} by {artist}")
            
            processor = YouTubeAudioProcessor()
            segment_info = processor.download_and_extract_segment(
                song_title, artist, start_time, duration
            )
            
            if segment_info:
                logger.info(f" On-demand segment extracted: {song_title}")
                return segment_info
            else:
                logger.warning(f" On-demand extraction failed: {song_title}")
                return None
                
        except Exception as e:
            logger.error(f"On-demand YouTube processing error: {e}")
            return None
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response with robust JSON extraction"""
        try:
            if response_text.strip().startswith('{'):
                return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        import re
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, response_text, re.DOTALL)
        for match in matches:
            try:
                parsed = json.loads(match)
                if 'recommendations' in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue
        
        raise Exception(f"Could not parse LLM response as JSON. Raw response: {response_text}")

# Test function
def test_recommender_with_additional_preferences():
    """Test music recommender with additional preferences"""
    try:
        recommender = GeminiMusicRecommender()
        
        test_caption = "a photography of a woman in a pink top standing on a street at night"
        test_user_input = "I love indie rock and melancholic songs"
        test_languages = "English, Spanish"
        test_additional = "I want more upbeat songs with guitar solos"
        result = recommender.recommend_songs(test_caption, test_user_input, "Instagram post", 3, test_languages, test_additional)
        
        print(" Music recommender with additional preferences test successful!")
        
        for i, song in enumerate(result.get('recommendations', []), 1):
            print(f"\n{i}. {song.get('song_title', 'Unknown')} - {song.get('artist', 'Unknown')}")
            print(f"   Language: {song.get('language', 'Unknown')}")
            print(f"   Preview Available: {song.get('preview_available', False)}")
            print(f"   Why Perfect Match: {song.get('why_perfect_match', 'N/A')}")
        
    except Exception as e:
        print(f" Test failed: {e}")

if __name__ == "__main__":
    test_recommender_with_additional_preferences()
