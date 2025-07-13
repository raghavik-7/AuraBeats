import requests
import urllib.parse
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
import os
import re

# -------------------- SETUP --------------------

# Get credentials from environment variables
GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Setup Spotify client
sp_auth = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID,
                                   client_secret=SPOTIFY_CLIENT_SECRET)
sp = spotipy.Spotify(auth_manager=sp_auth)

# -------------------- FUNCTIONS --------------------

def normalize_text(text):
    """Normalize quotes and remove non-ASCII characters."""
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r'[^\x00-\x7F]+',' ', text).strip()

def search_genius_songs_by_lyrics(lyrics_query, max_results=6):
    headers = {"Authorization": f"Bearer {GENIUS_ACCESS_TOKEN}"}
    search_url = "https://api.genius.com/search"
    params = {"q": lyrics_query}
    response = requests.get(search_url, params=params, headers=headers)

    if response.status_code != 200:
        print(f" Genius API error: {response.status_code} - {response.text}")
        return []

    data = response.json()
    hits = data.get("response", {}).get("hits", [])

    results = []
    for hit in hits[:max_results]:
        title = normalize_text(hit["result"]["title"])
        artist = normalize_text(hit["result"]["primary_artist"]["name"])
        results.append({"title": title, "artist": artist})
    return results

def search_spotify_track(title, artist):
    # First try with both title and artist
    query = f"track:{title} artist:{artist}"
    results = sp.search(q=query, type="track", limit=1)
    items = results.get("tracks", {}).get("items", [])
    
    if not items:
        # Try with just title
        query = f"track:{title}"
        results = sp.search(q=query, type="track", limit=1)
        items = results.get("tracks", {}).get("items", [])
    
    if items:
        track = items[0]
        return {
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "album_cover": track["album"]["images"][0]["url"],
            "spotify_url": track["external_urls"]["spotify"],
            "embed_url": f"https://open.spotify.com/embed/track/{track['id']}"
        }
    return None

# -------------------- EXECUTION --------------------

lyrics_input = "amma"
genius_results = search_genius_songs_by_lyrics(lyrics_input)

if not genius_results:
    print(" No songs found using Genius for those lyrics.")
else:
    print(f" Showing top {len(genius_results)} results from Genius:\n")
    for idx, result in enumerate(genius_results):
        print(f"{idx+1}. 🎵 {result['title']} by {result['artist']}")
        spotify_result = search_spotify_track(result['title'], result['artist'])
        if spotify_result:
            print(f"   🔗 Spotify: {spotify_result['spotify_url']}")
        else:
            print("    No match found on Spotify")
