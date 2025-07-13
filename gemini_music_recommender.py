import google.generativeai as genai
import os
import json
import logging
from typing import Dict, Any, List, Optional
import time
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MusicRecommender:
    def __init__(self):
        self.setup_gemini()
        self.setup_spotify()
        logger.info(" Music Recommender initialized successfully")

    def setup_gemini(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            api_key = input("Enter your Google API key: ")
            self._save_to_env("GOOGLE_API_KEY", api_key)

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info(" Gemini LLM initialized successfully")

    def setup_spotify(self):
        """Setup Spotify API"""
        self.spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not self.spotify_client_id:
            self.spotify_client_id = input("Enter your Spotify Client ID: ")
            self._save_to_env("SPOTIFY_CLIENT_ID", self.spotify_client_id)

        if not self.spotify_client_secret:
            self.spotify_client_secret = input("Enter your Spotify Client Secret: ")
            self._save_to_env("SPOTIFY_CLIENT_SECRET", self.spotify_client_secret)

        try:
            sp_auth = SpotifyClientCredentials(
                client_id=self.spotify_client_id,
                client_secret=self.spotify_client_secret
            )
            self.sp = spotipy.Spotify(auth_manager=sp_auth)
            # Test the connection
            self.sp.search(q="test", type="track", limit=1)
            logger.info(" Spotify API initialized successfully")
        except Exception as e:
            logger.error(f" Spotify initialization failed: {e}")
            self.sp = None

    def _save_to_env(self, key: str, value: str):
        """Save environment variable to .env file"""
        try:
            with open('.env', 'a') as f:
                f.write(f"\n{key}={value}")
        except Exception as e:
            logger.warning(f"Could not save {key} to .env file: {e}")

    def recommend_songs(self, image_caption: str, user_input: str = "", context: str = "", 
                       preferred_languages: str = "", 
                       additional_preferences: str = "") -> Dict[str, Any]:
        try:
            # Single comprehensive Gemini API call to get everything
            logger.info("🎧 Getting comprehensive recommendations from Gemini...")
            comprehensive_data = self._get_comprehensive_recommendations(
                image_caption, user_input, context, 
                preferred_languages, additional_preferences
            )
            
            # Extract keywords and recommendations from the comprehensive response
            spotify_keywords = comprehensive_data.get("spotify_keywords", [])
            gemini_recommendations = comprehensive_data.get("recommendations", [])
            scene_analysis = comprehensive_data.get("scene_analysis", {})
            
            logger.info(f" Gemini provided {len(gemini_recommendations)} recommendations")
            logger.info(f" Using {len(spotify_keywords)} Spotify keywords: {spotify_keywords}")
            
            # Get Spotify recommendations using the generated keywords
            logger.info(" Getting Spotify recommendations using generated keywords...")
            spotify_recommendations = self._search_spotify_with_keywords(spotify_keywords)
            
            # Merge recommendations with Spotify priority and remove duplicates
            logger.info(" Merging and deduplicating recommendations...")
            final_recommendations = self._merge_recommendations(
                spotify_recommendations, gemini_recommendations, scene_analysis
            )
            
            # Add Spotify data to any Gemini recommendations that don't have it
            logger.info(" Adding Spotify data to remaining recommendations...")
            self._add_spotify_data(final_recommendations)
            
            return final_recommendations
            
        except Exception as e:
            logger.error(f" Error in recommend_songs: {e}")
            return self._create_fallback_response()

    def _get_comprehensive_recommendations(self, image_caption: str, user_input: str, context: str, 
                                         preferred_languages: str, 
                                         additional_preferences: str) -> Dict[str, Any]:
        """Single comprehensive Gemini API call to get all recommendations and data"""
        #if additional_preferences.strip():
         #   full_description = additional_preferences
        #else: 
        full_description = image_caption
        if user_input.strip():
                full_description += f". Initial preferences: {user_input}"
        if additional_preferences.strip():
            full_description += f". Additional preferences: {additional_preferences}"

        prompt = f"""
You are a professional music curator and Instagram content creator. Based on this image description and user preferences, you need to provide:

1. Scene analysis
2. Exactly 4 Spotify search keywords for finding trending songs
3. 10-15 specific, real song recommendations

IMAGE DESCRIPTION: "{image_caption}"
INITIAL USER PREFERENCES: "{user_input}"
ADDITIONAL USER PREFERENCES: "{additional_preferences}"
CONTEXT: "{context}"
"""

        # Add language preferences if provided
        if preferred_languages.strip():
            prompt += f"\nPREFERRED LANGUAGES FOR SONGS: {preferred_languages}\n"
            prompt += "IMPORTANT: Prioritize songs in the specified languages in your recommendations. However, for Spotify keywords, always use English/Roman script terms that will help find songs in the preferred language (e.g., use 'hindi sad', 'bollywood romantic', 'punjabi bhangra', 'tamil melody', etc.).\n"
        
        # Add additional preferences guidance
        if additional_preferences.strip():
            prompt += f"\nIMPORTANT: Pay special attention to the additional preferences: '{additional_preferences}'. These are refined preferences that should heavily influence your recommendations.\n"
        
        prompt += f"""

TASK 1 - SPOTIFY KEYWORDS: Generate exactly 4 short, evocative keywords or phrases that will work well for Spotify search. IMPORTANT: Always use ENGLISH/ROMAN script for keywords, even for Hindi/regional language preferences, because Spotify uses Roman script for all song metadata. Focus on keywords that capture the essence of the scene, such as emotions, character traits, or visual themes. Examples: "deshbhakti", "veer", "patriotic hindi", "soldier song", "hindi emotional", "bollywood patriotic", etc. Use transliterated Hindi words or English descriptions. Always use lowercase.

TASK 2 - SCENE ANALYSIS: Analyze the primary mood, visual elements, atmosphere, energy level, and setting type.

TASK 3 - SONG RECOMMENDATIONS: Recommend 10-15 specific, real, POPULAR songs that are likely trending on Instagram and Spotify charts. Focus on songs that feel authentic and natural for the scene. Include a good mix of different artists and styles within the theme.

IMPORTANT: Keep song titles SHORT and CLEAN. Do not include explanations or additional text in the song title field.

You MUST respond with this EXACT JSON format (no markdown, no extra text):
{{
    "spotify_keywords": ["keyword1", "keyword2", "keyword3", "keyword4"],
    "scene_analysis": {{
        "primary_mood": "main emotional tone",
        "visual_elements": "key visual components",
        "atmosphere": "overall feeling/vibe",
        "energy_level": "low/medium/high",
        "setting_type": "indoor/outdoor/urban/nature/etc"
    }},
    "recommendations": [
        {{
            "song_title": "Exact Song Title",
            "artist": "Artist Name"
        }},
        {{
            "song_title": "Another Song Title",
            "artist": "Another Artist"
        }}
    ]
}}

Ensure all three sections are properly filled out. The spotify_keywords should be exactly 4 keywords in ENGLISH/ROMAN script optimized for finding trending songs that match the scene mood. If additional preferences are provided, ensure they significantly influence both keywords and recommendations while maintaining relevance to the image.
"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=4000,
                    top_p=0.9
                )
            )

            logger.info(" Comprehensive Gemini response received")
            raw_response = response.text.strip()
            logger.info(f" Raw Gemini response length: {len(raw_response)} characters") 
            
            # Log first 200 characters to debug parsing issues
            logger.info(f" Response preview: {raw_response[:200]}...")
            
            return self._parse_gemini_response(raw_response)
            
        except Exception as e:
            logger.error(f" Gemini API call failed: {e}")
            return self._create_fallback_response()

    def _search_spotify_with_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Search Spotify using the generated keywords"""
        
        if not self.sp:
            logger.warning(" Spotify not initialized, skipping Spotify recommendations")
            return []
        
        if not keywords:
            logger.warning(" No keywords provided for Spotify search")
            return []
        
        try:
            spotify_tracks = []
            
            # Search Spotify for each keyword (now expecting 4)
            for keyword in keywords[:4]:  # Use all 4 keywords
                try:
                    results = self.sp.search(q=keyword, type="track", market="IN", limit=8)  # Increased limit
                    items = results.get("tracks", {}).get("items", [])
                    
                    for track in items:
                        # Only add popular tracks (popularity >= 35, lowered threshold)
                        if track["popularity"] >= 35:
                            spotify_tracks.append({
                                "song_title": track["name"],
                                "artist": track["artists"][0]["name"],
                                "spotify_url": track["external_urls"]["spotify"],
                                "popularity": track["popularity"],
                                "verified_title": track["name"],
                                "verified_artist": track["artists"][0]["name"],
                                "source": "spotify"
                            })
                    
                except Exception as e:
                    logger.warning(f" Spotify search failed for keyword '{keyword}': {e}")
                    continue
            
            # Sort by popularity and remove duplicates
            seen_tracks = set()
            unique_tracks = []
            
            for track in sorted(spotify_tracks, key=lambda x: x["popularity"], reverse=True):
                track_key = (track["song_title"].lower().strip(), track["artist"].lower().strip())
                if track_key not in seen_tracks:
                    seen_tracks.add(track_key)
                    unique_tracks.append(track)
            
            logger.info(f" Found {len(unique_tracks)} unique Spotify tracks")
            return unique_tracks  # Return all unique tracks (no limit)
            
        except Exception as e:
            logger.error(f" Spotify search with keywords failed: {e}")
            return []

    def _merge_recommendations(self, spotify_tracks: List[Dict[str, Any]], 
                             gemini_recommendations: List[Dict[str, Any]], 
                             scene_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Merge Spotify and Gemini recommendations, prioritizing Spotify and removing duplicates"""
        
        # Start with scene analysis
        final_result = {
            "scene_analysis": scene_analysis,
            "recommendations": []
        }
        
        # Keep track of songs to avoid duplicates
        seen_songs = set()
        
        # Add Spotify recommendations first (PRIORITY)
        for track in spotify_tracks:
            song_key = (track["song_title"].lower().strip(), track["artist"].lower().strip())
            if song_key not in seen_songs:
                seen_songs.add(song_key)
                track["source"] = "spotify"
                final_result["recommendations"].append(track)
        
        # Add Gemini recommendations to fill remaining slots
        for song in gemini_recommendations:
            song_title = song.get("song_title", "").strip()
            artist = song.get("artist", "").strip()
            song_key = (song_title.lower(), artist.lower())
            
            if song_key not in seen_songs and song_title:
                seen_songs.add(song_key)
                # Mark as Gemini source
                song["source"] = "gemini"
                final_result["recommendations"].append(song)
        
        logger.info(f" Merged recommendations: {len(final_result['recommendations'])} total songs")
        logger.info(f"   - Spotify: {len([r for r in final_result['recommendations'] if r.get('source') == 'spotify'])}")
        logger.info(f"   - Gemini: {len([r for r in final_result['recommendations'] if r.get('source') == 'gemini'])}")
        
        return final_result

    def _add_spotify_data(self, recommendations: Dict[str, Any]):
        """Add Spotify URLs and metadata to recommendations that don't already have them"""
        if 'recommendations' not in recommendations:
            return
        
        for song in recommendations['recommendations']:
            # Skip if already has Spotify data (from Spotify recommendations)
            if song.get('source') == 'spotify' and song.get('spotify_url'):
                continue
                
            title = song.get('song_title', '').strip()
            artist = song.get('artist', '').strip()
            
            # Clean up malformed titles
            title = self._clean_song_title(title)
            
            if title and artist:
                spotify_data = self._search_spotify_track(title, artist)
                if spotify_data:
                    song['spotify_url'] = spotify_data['spotify_url']
                    song['verified_title'] = spotify_data['name']
                    song['verified_artist'] = spotify_data['artist']
                    song['popularity'] = spotify_data.get('popularity', 0)
                else:
                    song['spotify_url'] = 'N/A'
                    song['popularity'] = 0
            else:
                song['spotify_url'] = 'N/A'
                song['popularity'] = 0

    def _search_spotify_track(self, title: str, artist: str) -> Optional[Dict[str, Any]]:
        """Search for a track on Spotify and return metadata"""
        if not self.sp:
            logger.warning(" Spotify not initialized")
            return None
            
        try:
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
                    results = self.sp.search(q=query, type="track", market="IN", limit=10)
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
                                    "spotify_url": track["external_urls"]["spotify"],
                                    "popularity": track.get("popularity", 0)
                                }
                        
                        # If no perfect match, return first result
                        track = items[0]
                        return {
                            "name": track["name"],
                            "artist": track["artists"][0]["name"],
                            "spotify_url": track["external_urls"]["spotify"],
                            "popularity": track.get("popularity", 0)
                        }
                
                except Exception as e:
                    logger.warning(f" Search query failed: {query}. Error: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f" Spotify search failed for {title} by {artist}: {e}")
            return None

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

    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response with improved error handling and debugging"""
        original_text = response_text
        
        try:
            # Try direct JSON parse first
            result = json.loads(response_text)
            logger.info(" Direct JSON parse successful")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f" Direct JSON parse failed: {e}")

        # Remove markdown code blocks and extra whitespace
        cleaned_text = re.sub(r"```json\s*|\s*```|```", "", response_text).strip()
        
        try:
            result = json.loads(cleaned_text)
            logger.info(" Cleaned JSON parse successful")
            return result
        except json.JSONDecodeError as e:
            logger.warning(f" Cleaned JSON parse failed: {e}")

        # Try to find JSON object in the text
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested braces
            r'\{.*?\}',  # Any content between braces
        ]
        
        for pattern in json_patterns:
            json_matches = re.findall(pattern, cleaned_text, re.DOTALL)
            for match in json_matches:
                try:
                    result = json.loads(match)
                    logger.info(" Pattern-based JSON parse successful")
                    return result
                except json.JSONDecodeError:
                    continue

        # Try to extract individual components if JSON parsing completely fails
        logger.warning(" Attempting manual component extraction")
        
        try:
            # Extract keywords
            keywords_match = re.search(r'"spotify_keywords":\s*\[(.*?)\]', cleaned_text, re.DOTALL)
            keywords = []
            if keywords_match:
                keywords_str = keywords_match.group(1)
                keywords = [k.strip().strip('"') for k in keywords_str.split(',') if k.strip()]
            
            # Extract recommendations
            recommendations = []
            rec_pattern = r'"song_title":\s*"([^"]+)"[^}]*"artist":\s*"([^"]+)"'
            rec_matches = re.findall(rec_pattern, cleaned_text)
            for title, artist in rec_matches:
                recommendations.append({
                    "song_title": title.strip(),
                    "artist": artist.strip()
                })
            
            if keywords or recommendations:
                logger.info(" Manual extraction partially successful")
                return {
                    "spotify_keywords": keywords[:4],  # Ensure only 4 keywords
                    "scene_analysis": {
                        "primary_mood": "extracted_fallback",
                        "visual_elements": "extracted_fallback",
                        "atmosphere": "extracted_fallback",
                        "energy_level": "medium",
                        "setting_type": "extracted_fallback"
                    },
                    "recommendations": recommendations
                }
        except Exception as e:
            logger.error(f" Manual extraction failed: {e}")

        # Log the problematic response for debugging
        logger.error(" Could not parse LLM response. Original response:")
        logger.error(f"Response (first 500 chars): {original_text[:500]}")
        
        return self._create_fallback_response()

    def _create_fallback_response(self) -> Dict[str, Any]:
        """Create a fallback response when API calls fail"""
        return {
            "spotify_keywords": [],
            "scene_analysis": {
                "primary_mood": "unknown",
                "visual_elements": "unknown",
                "atmosphere": "unknown",
                "energy_level": "medium",
                "setting_type": "unknown"
            },
            "recommendations": []
        }


def test_recommender():
    """Test the music recommender"""
    try:
        recommender = MusicRecommender()
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

        print("\n🎧 Final Recommended Songs:")
        print(f"Scene Analysis: {results.get('scene_analysis', {})}")
        print(f"Spotify Keywords: {results.get('spotify_keywords', {})}")
        print(f"\nTotal Recommendations: {len(results.get('recommendations', []))}")
        print("\nRecommendations:")
        
        for i, song in enumerate(results.get("recommendations", []), 1):
            print(f"\n{i}. {song.get('song_title', 'Unknown')} - {song.get('artist', 'Unknown')}")
            print(f"   Source: {song.get('source', 'Unknown').upper()}")
            print(f"   Spotify URL: {song.get('spotify_url', 'N/A')}")
            
            # Show verified Spotify metadata if available
            if song.get('verified_title'):
                print(f"   Verified on Spotify as: {song.get('verified_title')} - {song.get('verified_artist')}")
                print(f"   Popularity: {song.get('popularity', 0)}")

        print("\n Music recommendation test completed successfully!")

    except Exception as e:
        print(f" Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_recommender()