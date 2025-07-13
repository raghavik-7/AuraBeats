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

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class GeminiMusicRecommender:
    def __init__(self):
        self.setup_gemini()
        self.setup_spotify_genius()
        logger.info(" Gemini Music Recommender with Spotify and Genius integration initialized successfully")

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

    def setup_spotify_genius(self):
        self.genius_token = os.getenv("GENIUS_ACCESS_TOKEN")
        self.spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not self.genius_token:
            self.genius_token = input("Enter your Genius Access Token: ")
            with open('.env', 'a') as f:
                f.write(f"\nGENIUS_ACCESS_TOKEN={self.genius_token}")

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
    #lyrics_query: str,
    def hybrid_song_recommendation(self, image_caption: str, user_input: str = "", context: str = "", preferred_languages: str = "", additional_preferences: str = "") -> Dict[str, Any]:
        results = {
            "scene_analysis": None,
            "recommendations": [],
            "sources": {
                "lyrics_based": [],
                "gemini_based": []
            }
        }

        lyrics_songs = self.get_lyrics_based_recommendations(image_caption, user_input, additional_preferences, max_results=6)
        if lyrics_songs:
            results["sources"]["lyrics_based"] = lyrics_songs
            for song in lyrics_songs:
                song_entry = {
                    "song_title": song.get("title", ""),
                    "artist": song.get("artist", ""),
                    "language": "unknown",
                    "recommended_segment": "unknown",
                    "segment_description": "Lyrics-based match",
                    "why_perfect_match": "Matched lyrics provided by user.",
                    "mood_connection": "Lyrics relevance",
                    "specific_elements": f"Matched query: {image_caption}",
                    "suggested_caption": f"Found a song that echoes your words: {song.get('title')} 🎶",
                    "spotify_data": song if song.get("spotify_url") else None,
                    "spotify_url": song.get("spotify_url", None),
                    "preview_available": song.get("spotify_available", False),
                    "preview_source": "spotify",
                    "playback_type": "spotify_embed",
                    "album_cover": song.get("album_cover", None)
                }
                results["recommendations"].append(song_entry)

        try:
            gemini_result = self.recommend_songs(
                image_caption=image_caption,
                user_input=user_input,
                context=context,
                num_songs=4,
                preferred_languages=preferred_languages,
                additional_preferences=additional_preferences
            )
            if gemini_result:
                results["scene_analysis"] = gemini_result.get("scene_analysis")
                results["sources"]["gemini_based"] = gemini_result.get("recommendations", [])
                results["recommendations"].extend(gemini_result.get("recommendations", []))
        except Exception as e:
            logger.error(f" Failed to get Gemini-based recommendations: {e}")

        return results

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
        import re
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning(" Direct JSON parse failed. Attempting cleanup.")

        response_text = re.sub(r"```json|```", "", response_text).strip()

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass

        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, response_text, re.DOTALL)
        for match in matches:
            try:
                parsed = json.loads(match)
                if 'recommendations' in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue

        raise Exception(f"Could not parse LLM response as JSON. Raw response: {response_text[:300]}...")

    def search_genius_songs_by_lyrics(self, lyrics_query: str, max_results: int = 6) -> list:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        def extract_keywords(text):
            doc = nlp(text)
            keywords = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN", "ADJ"] and not token.is_stop]
            return ", ".join(f"'{kw}'" for kw in keywords)
        
        lyrics_query = extract_keywords(lyrics_query)

        try:
            headers = {"Authorization": f"Bearer {self.genius_token}"}
            response = requests.get("https://api.genius.com/search", params={"q": lyrics_query}, headers=headers)
            response.raise_for_status()
            hits = response.json()["response"]["hits"]
            return [{"title": hit["result"]["title"], "artist": hit["result"]["primary_artist"]["name"]} for hit in hits[:max_results]]
        except Exception as e:
            logger.error(f" Genius search failed: {e}")
            return []

    def search_spotify_track(self, title: str, artist: str) -> dict:
        try:
            if not self.sp:
                logger.error(" Spotify not initialized")
                return None
            query = f"track:{title} artist:{artist}"
            results = self.sp.search(q=query, type="track", limit=1)
            items = results.get("tracks", {}).get("items", [])
            if items:
                track = items[0]
                return {
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": track["album"]["name"],
                    "album_cover": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                    "spotify_url": track["external_urls"]["spotify"],
                    "embed_url": f"https://open.spotify.com/embed/track/{track['id']}",
                    "track_id": track["id"],
                    "duration_ms": track["duration_ms"],
                    "popularity": track["popularity"],
                    "preview_url": track.get("preview_url"),
                    "available": True,
                    "source": "spotify"
                }
            return None
        except Exception as e:
            logger.error(f" Spotify search failed for {title} by {artist}: {e}")
            return None

    def _add_spotify_sources(self, recommendations):
        for song in recommendations.get('recommendations', []):
            try:
                spotify_data = self.search_spotify_track(song.get('song_title', ''), song.get('artist', ''))
                if spotify_data:
                    song.update({
                        'preview_available': True,
                        'spotify_data': spotify_data,
                        'preview_source': 'spotify',
                        'spotify_embed_url': spotify_data['embed_url'],
                        'preview_note': "Full song from Spotify" if spotify_data.get('preview_url') else "30-second preview from Spotify",
                        'playback_type': 'spotify_embed',
                        'album_cover': spotify_data.get('album_cover'),
                        'spotify_url': spotify_data.get('spotify_url')
                    })
                else:
                    song['preview_available'] = False
                    song['preview_note'] = "Song not found on Spotify"
                time.sleep(0.2)
            except Exception as e:
                logger.error(f" Error getting Spotify data for {song.get('song_title', 'Unknown')}: {e}")
                song['preview_available'] = False
                song['preview_note'] = f"Error: {str(e)}"

    def get_lyrics_based_recommendations(self, image_caption:str, user_input: str, additional_preferences: str, max_results: int = 6) -> list:
        lyrics_query = f"{image_caption}, {user_input}, {additional_preferences}"

        try:
            genius_results = self.search_genius_songs_by_lyrics(lyrics_query, max_results)
            enriched_results = []
            for result in genius_results:
                spotify_data = self.search_spotify_track(result['title'], result['artist'])
                enriched_result = {
                    'title': result['title'],
                    'artist': result['artist'],
                    'found_via': 'genius_lyrics',
                    'spotify_available': spotify_data is not None
                }
                if spotify_data:
                    enriched_result.update(spotify_data)
                enriched_results.append(enriched_result)
            return enriched_results
        except Exception as e:
            logger.error(f" Lyrics-based recommendation failed: {e}")
            return []


def test_recommender_with_spotify_genius():
    try:
        recommender = GeminiMusicRecommender()
        lyrics_query = "teri mitti me mil java"
        image_caption = "A soldier standing alone on a battlefield at dusk"
        user_input = "I want emotional and patriotic songs"
        context = "Instagram reel"
        preferred_languages = "Hindi"
        additional_preferences = "Prefer acoustic or orchestral backgrounds"

        results = recommender.hybrid_song_recommendation(
            lyrics_query=lyrics_query,
            image_caption=image_caption,
            user_input=user_input,
            context=context,
            preferred_languages=preferred_languages,
            additional_preferences=additional_preferences
        )

        print("\n🎧 Final Recommended Songs:")
        for i, song in enumerate(results["recommendations"], 1):
            print(f"\n{i}. {song.get('song_title', 'Unknown')} - {song.get('artist', 'Unknown')}")
            print(f"   Spotify URL: {song.get('spotify_url', 'N/A')}")
            print(f"   Preview Available: {song.get('preview_available', False)}")
            print(f"   Caption: {song.get('suggested_caption', '')}")

        print("\n Hybrid recommendation test completed successfully!")

    except Exception as e:
        print(f" Test failed: {e}")


if __name__ == "__main__":
    test_recommender_with_spotify_genius()
