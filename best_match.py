import google.generativeai as genai
import json
from typing import List, Dict, Tuple
import time
import os

class SimpleVibeMatcher:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def check_song_vibe_match(self, input_text: str, song_name: str, artist_name: str) -> Tuple[str, str, float]:
        prompt = f"""
        INPUT TEXT: "{input_text}"
        SONG: "{song_name}" by {artist_name}
        
        Based on your knowledge and summary of this song, will it be suitable to be played in the background of an image with the input text situation for instagram stories?
        
        Respond in this EXACT format:
        STATUS: [PERFECT_MATCH / GOOD_MATCH / WEAK_MATCH / NO_MATCH / COMPLETELY_IRRELEVANT]
        CONFIDENCE: [0-100]
        EXPLANATION: [small explanation of why it matches or doesn't match]
        
        Consider:
        - The situation in the input text
        - Will the song be good in the background of the picture while posting for Instagram stories?
        - Does the song's mood fit the situation?
        - Would this song make sense in this context?
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._parse_vibe_response(response.text)
        except Exception as e:
            print(f"Error checking vibe match for {song_name}: {e}")
            return "ERROR", "Error in analysis", 0.0
    
    def analyze_song_list(self, input_text: str, song_list: List[Dict]) -> Dict[str, List[Dict]]:
        results = {
            "PERFECT_MATCH": [],
            "GOOD_MATCH": [],
            "WEAK_MATCH": [],
            "NO_MATCH": [],
            "COMPLETELY_IRRELEVANT": [],
            "ERROR": []
        }
        
        total_songs = len(song_list)
        print(f"Analyzing {total_songs} songs for vibe matching...")
        
        for i, song_info in enumerate(song_list):
            song_name = song_info.get('song_name', '')
            artist_name = song_info.get('artist_name', '')
            
            if not song_name or not artist_name:
                print(f"Skipping invalid song entry: {song_info}")
                continue
                
            print(f"Processing {i+1}/{total_songs}: '{song_name}' by {artist_name}")
            
            status, explanation, confidence = self.check_song_vibe_match(
                input_text, song_name, artist_name
            )
            
            song_result = {
                'song_name': song_name,
                'artist_name': artist_name,
                'explanation': explanation,
                'confidence': confidence
            }
            
            results[status].append(song_result)
            
            # Add delay to avoid rate limiting
            time.sleep(0.5)
        
        # Sort each category by confidence
        for category in results:
            results[category].sort(key=lambda x: x['confidence'], reverse=True)
        
        return results
    
    def _parse_vibe_response(self, response_text: str) -> Tuple[str, str, float]:
        """Parse the vibe match response"""
        import re
        
        lines = response_text.strip().split('\n')
        status = "ERROR"
        confidence = 0.0
        explanation = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('STATUS:'):
                status_match = re.search(r'STATUS:\s*(\w+)', line)
                if status_match:
                    status = status_match.group(1)
            elif line.startswith('CONFIDENCE:'):
                conf_match = re.search(r'CONFIDENCE:\s*(\d+)', line)
                if conf_match:
                    confidence = float(conf_match.group(1))
            elif line.startswith('EXPLANATION:'):
                explanation = line.replace('EXPLANATION:', '').strip()
                # Get remaining lines as part of explanation
                remaining_lines = lines[lines.index(line)+1:]
                if remaining_lines:
                    explanation += " " + " ".join(remaining_lines)
        
        return status, explanation, confidence

def main():
    # Initialize the matcher
    matcher = SimpleVibeMatcher()
    
    # Example input text
    input_text = "A picture of a man posing for the camera"
    
    # Example song list with song names and artists
    song_list = [
        {"song_name": "Boss", "artist_name": "Meet Bros Anjjan"},
        {"song_name": "Boss Party (From 'Waltair Veerayya')", "artist_name": "Devi Sri Prasad"},
        {"song_name": "Boss Bitch", "artist_name": "Doja Cat"},
        {"song_name": "Boss", "artist_name": "Sidhu Moose Wala"},
        {"song_name": "Boss", "artist_name": "Jass Manak"},
        {"song_name": "Hum Na Tode", "artist_name": "Vishal Dadlani"},
        {"song_name": "Har Kisi Ko (Female)", "artist_name": "Arijit Singh"},
    ]
    
    # Analyze all songs
    print(f"Input text: {input_text}")
    print("=" * 60)
    
    results = matcher.analyze_song_list(input_text, song_list)
    
    # Display results by category
    categories = ["PERFECT_MATCH", "GOOD_MATCH", "WEAK_MATCH", "NO_MATCH", "COMPLETELY_IRRELEVANT"]
    
    for category in categories:
        if results[category]:
            print(f"\n🎵 {category.replace('_', ' ')} ({len(results[category])} songs):")
            print("-" * 50)
            
            for song in results[category]:
                print(f"• '{song['song_name']}' by {song['artist_name']}")
                print(f"  Confidence: {song['confidence']:.0f}%")
                print(f"  Reason: {song['explanation']}")
                print()
    
    # Show error songs if any
    if results["ERROR"]:
        print(f"\n ERRORS ({len(results['ERROR'])} songs):")
        print("-" * 50)
        for song in results["ERROR"]:
            print(f"• '{song['song_name']}' by {song['artist_name']}")
            print(f"  Error: {song['explanation']}")
            print()

if __name__ == "__main__":
    main()