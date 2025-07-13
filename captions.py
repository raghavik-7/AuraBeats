def _add_captions(self, recommendations: Dict[str, Any], image_caption: str, 
                     user_input: str, context: str, preferred_languages: str, 
                     additional_preferences: str):
        """Generate Instagram captions for the recommendations"""
        
        input_text = f"{image_caption}, {user_input}, {additional_preferences}"
        
        prompt = f"""
Create natural Instagram captions for each song in the recommendations based on the image description and context.

IMAGE DESCRIPTION: "{image_caption}"
CONTEXT: "{context}"
RECOMMENDATIONS: {json.dumps(recommendations.get('recommendations', []))}

CAPTION GUIDELINES:
- Write like a real Instagram user would caption their post
- Focus on the emotion, moment, or story in the image
- Include relevant hashtags (2-4 hashtags maximum)
- Keep it authentic and relatable, not promotional
- The song should feel like the perfect soundtrack to the moment
- Examples of good caption style:
  * "Late night drives hit different when the city lights blur past your window. #NightVibes #CityLights"
  * "Coffee shop mornings. Perfect start to the day  #MorningRitual #AcousticVibes"

Respond with this EXACT JSON format:
{{
    "captions": [
        {{
            "song_title": "Exact Song Title",
            "artist": "Artist Name",
            "suggested_caption": "Instagram caption for this song"
        }}
    ]
}}
"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.8,
                    max_output_tokens=3000,
                    top_p=0.9
                )
            )

            logger.info(" Caption generation response received")
            caption_data = self._parse_gemini_response(response.text.strip())
            
            # Merge captions with recommendations
            if caption_data.get('captions'):
                for i, song in enumerate(recommendations.get('recommendations', [])):
                    if i < len(caption_data['captions']):
                        song['suggested_caption'] = caption_data['captions'][i].get('suggested_caption', '')
                        
        except Exception as e:
            logger.error(f" Caption generation failed: {e}")
            # Add default captions
            for song in recommendations.get('recommendations', []):
                song['suggested_caption'] = "Perfect soundtrack for this moment 🎵 #MusicVibes #InstaMood"
