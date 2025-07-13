import requests
import re
from googleapiclient.discovery import build

class YouTubeMusicIntegration:
    def __init__(self):
        #self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.youtube_api_key="AIzaSyDrzy-dOWxaKuoRuP0N68Gm8RVLwDeK1d4"
        self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
    
    def search_track(self, song_title, artist):
        """Search for track on YouTube"""
        query = f"{song_title} {artist} official audio"
        
        search_response = self.youtube.search().list(
            q=query,
            part='id,snippet',
            maxResults=1,
            type='video'
        ).execute()
        
        if search_response['items']:
            video = search_response['items'][0]
            return {
                'youtube_video_id': video['id']['videoId'],
                'youtube_url': f"https://www.youtube.com/watch?v={video['id']['videoId']}",
                'thumbnail': video['snippet']['thumbnails']['high']['url']
            }
        
        return None
