import google.generativeai as genai
import os
import json
import logging
from typing import Dict, Any
import time
import requests
import urllib.parse
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import re

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class GeminiMusicRecommender:
    def __init__(self):
        self.setup_gemini()
        self.setup_spotify()
        logger.info(" Gemini Music Recommender with Spotify integration initialized successfully")

    def setup_gemini(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            api_key = input("Enter your Google API key: ")
            with open('.env', 'a') as f:
                f.write(f"\nGOOGLE_API_KEY={api_key}")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.provider = "gemini"
        logger.info(" Gemini LLM initialized successfully")

    def setup_spotify(self):
        self.spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not self.spotify_client_id:
            self.spotify_client_id = input("Enter your Spotify Client ID: ")
            with open('.env', 'a') as f:
                f.write(f"\nSPOTIFY_CLIENT_ID={self.spotify_client_id}")

        if not self.spotify_client_secret:
            self.spotify_client_secret = input("Enter your Spotify Client Secret: ")
            with open('.env', 'a') as f:
                f.write(f"\nSPOTIFY_CLIENT_SECRET={self.spotify_client_secret}")

        try:
            sp_auth = SpotifyClientCredentials(
                client_id=self.spotify_client_id,
                client_secret=self.spotify_client_secret
            )
            self.sp = spotipy.Spotify(auth_manager=sp_auth)
            logger.info(" Spotify API initialized successfully")
        except Exception as e:
            logger.error(f" Spotify initialization failed: {e}")
            self.sp = None

    def recommend_songs(self, image_caption: str, user_input: str = "", context: str = "", num_songs: int = 4, preferred_languages: str = "", additional_preferences: str = "") -> Dict[str, Any]:
        full_description = image_caption
        if user_input.strip():
            full_description += f". Initial preferences: {user_input}"
        if additional_preferences.strip():
            full_description += f". Additional preferences: {additional_preferences}"

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
        
        prompt += """Focus on POPULAR songs on INSTAGRAM likely Trending on Spotify charts(like 1.Trending now - India[https://open.spotify.com/playlist/37i9dQZF1DXbVhgADFy3im]). Create captions that feel authentic and natural, like real Instagram users would write them."""
        
        prompt += """
For each song, create a natural Instagram caption that incorporates the song organically.

CAPTION GUIDELINES:
- Write like a real Instagram user would caption their post
- Focus on the emotion, moment, or story in the image
- Include relevant hashtags (2-4 hashtags maximum)
- Keep it authentic and relatable, not promotional
- The song should feel like the perfect soundtrack to the moment
- Examples of good caption style:
  * "Late night drives hit different when the city lights blur past your window. #NightVibes #CityLights"
  * "Coffee shop mornings. Perfect start to the day  #MorningRitual #AcousticVibes"

IMPORTANT: Keep song titles SHORT and CLEAN. Do not include explanations or additional text in the song title field.

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
            "suggested_caption": "Instagram caption for this song"
        }
    ]
}

If additional preferences are provided, ensure they significantly influence your recommendations while maintaining relevance to the image.
"""

        response = self.model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.8,
                max_output_tokens=3000,
                top_p=0.9
            )
        )

        logger.info(" Gemini raw response:")
        logger.info(response.text)

        recommendations = self._parse_gemini_response(response.text.strip())

        if 'recommendations' in recommendations:
            self._add_spotify_sources(recommendations)

        return recommendations

    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response with improved error handling"""
        try:
            # Try direct JSON parse first
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning(" Direct JSON parse failed. Attempting cleanup.")

        # Remove markdown code blocks
        cleaned_text = re.sub(r"```json\s*|\s*```", "", response_text).strip()

        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            logger.warning(" Cleanup failed. Attempting to extract JSON from text.")

        # Try to find JSON object in the text
        json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # If all else fails, create a basic response structure
        logger.error(" Could not parse LLM response as JSON. Creating fallback response.")
        return {
            "scene_analysis": {
                "primary_mood": "unknown",
                "visual_elements": "unknown",
                "atmosphere": "unknown",
                "energy_level": "medium",
                "setting_type": "unknown"
            },
            "recommendations": []
        }
    
    def _add_spotify_sources(self, recommendations: Dict[str, Any]):
        """Add Spotify URLs and additional metadata to recommendations"""
        if 'recommendations' not in recommendations:
            return
        
        for song in recommendations['recommendations']:
            title = song.get('song_title', '').strip()
            artist = song.get('artist', '').strip()
            
            # Clean up malformed titles
            title = self._clean_song_title(title)
            
            if title and artist:
                spotify_data = self.search_spotify_track(title, artist)
                if spotify_data:
                    song['spotify_url'] = spotify_data['spotify_url']
                    song['verified_title'] = spotify_data['name']
                    song['verified_artist'] = spotify_data['artist']
                else:
                    song['spotify_url'] = 'N/A'
            else:
                song['spotify_url'] = 'N/A'
    
    def _clean_song_title(self, title: str) -> str:
        """Clean malformed song titles"""
        # Remove common prefixes that indicate explanatory text
        prefixes_to_remove = [
            r'^\(Finding.*?\)\s*',
            r'^\(.*?\)\s*',
            r'^Note:.*?:\s*',
            r'^.*?:\s*'
        ]
        
        cleaned_title = title
        for prefix in prefixes_to_remove:
            cleaned_title = re.sub(prefix, '', cleaned_title, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        cleaned_title = ' '.join(cleaned_title.split())
        
        return cleaned_title
    
    def search_spotify_track(self, title: str, artist: str) -> dict:
        """Search for a track on Spotify and return metadata"""
        try:
            if not self.sp:
                logger.error(" Spotify not initialized")
                return None
            
            # Limit query length to avoid Spotify API errors
            max_query_length = 200
            
            # Try different search strategies
            search_queries = [
                f"track:{title[:50]} artist:{artist[:50]}",
                f"{title[:50]} {artist[:50]}",
                f"{title[:100]}"
            ]
            
            for query in search_queries:
                if len(query) > max_query_length:
                    query = query[:max_query_length]
                
                try:
                    results = self.sp.search(q=query, type="track", limit=10)
                    items = results.get("tracks", {}).get("items", [])
                    
                    if items:
                        # Try to find the best match
                        for track in items:
                            track_name = track["name"].lower()
                            track_artist = track["artists"][0]["name"].lower()
                            
                            # Check for partial matches
                            if (title.lower() in track_name or track_name in title.lower()) and \
                               (artist.lower() in track_artist or track_artist in artist.lower()):
                                return {
                                    "name": track["name"],
                                    "artist": track["artists"][0]["name"],
                                    "spotify_url": track["external_urls"]["spotify"]
                                }
                        
                        # If no perfect match, return first result
                        track = items[0]
                        return {
                            "name": track["name"],
                            "artist": track["artists"][0]["name"],
                            "spotify_url": track["external_urls"]["spotify"]
                        }
                
                except Exception as e:
                    logger.warning(f" Search query failed: {query}. Error: {e}")
                    continue
            
            return None
        except Exception as e:
            logger.error(f" Spotify search failed for {title} by {artist}: {e}")
            return None


def test_recommender_with_spotify():
    try:
        recommender = GeminiMusicRecommender()
        image_caption = "A soldier standing alone on a battlefield at dusk"
        user_input = "I want emotional and patriotic songs"
        context = "Instagram reel"
        preferred_languages = "Hindi"
        additional_preferences = "Prefer acoustic or orchestral backgrounds"

        results = recommender.recommend_songs(
            image_caption=image_caption,
            user_input=user_input,
            context=context,
            preferred_languages=preferred_languages,
            additional_preferences=additional_preferences
        )

        print("\n Final Recommended Songs:")
        print(f"Scene Analysis: {results.get('scene_analysis', {})}")
        print("\nRecommendations:")
        
        for i, song in enumerate(results.get("recommendations", []), 1):
            print(f"\n{i}. {song.get('song_title', 'Unknown')} - {song.get('artist', 'Unknown')}")
            print(f"   Spotify URL: {song.get('spotify_url', 'N/A')}")
            print(f"   Caption: {song.get('suggested_caption', '')}")
            
            # Show verified Spotify metadata if available
            if song.get('verified_title'):
                print(f"   Verified on Spotify as: {song.get('verified_title')} - {song.get('verified_artist')}")

        print("\n Music recommendation test completed successfully!")

    except Exception as e:
        print(f" Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_recommender_with_spotify()