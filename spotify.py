import os
import logging
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy

# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class SpotifyHelper:
    def __init__(self):
        self.setup_spotify()

    def setup_spotify(self):
        # Load credentials from environment variables
        self.spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        # Prompt for credentials if not found
        if not self.spotify_client_id:
            self.spotify_client_id = input("Enter your Spotify Client ID: ")
            with open('.env', 'a') as f:
                f.write(f"\nSPOTIFY_CLIENT_ID={self.spotify_client_id}")

        if not self.spotify_client_secret:
            self.spotify_client_secret = input("Enter your Spotify Client Secret: ")
            with open('.env', 'a') as f:
                f.write(f"\nSPOTIFY_CLIENT_SECRET={self.spotify_client_secret}")

        # Authenticate
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

    def search_spotify_track(self, query: str) -> list:
        try:
            if not self.sp:
                logger.error(" Spotify not initialized")
                return []

            # Perform Spotify track search
            #f"track:{query}"
            results = self.sp.search(q=query, type="track", market = "IN")

            items = results.get("tracks", {}).get("items", [])

            if not items:
                logger.info(f"ℹ️ No tracks found for query: {query}")
                return []

            track_list = []
            for track in items:
                #if track["popularity"] >= 50: 
                    track_list.append({
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
                })

            return track_list
        

        except Exception as e:
            logger.error(f" Spotify search failed for query '{query}': {e}")
            return []

# Example usage
if __name__ == "__main__":
    spotify = SpotifyHelper()
    query = "boss"  # You can change this to any song or mood
    results = spotify.search_spotify_track(query)

  

    if results:
        print("\n Top Tracks Found:")
        for i, track in enumerate(results, 1):
            print(f"\n{i}. 🎵 {track['name']} by {track['artist']}")
            print(f"    {track['spotify_url']}")
    else:
        print(" No results found")
