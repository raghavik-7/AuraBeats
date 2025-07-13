import openai
import os
from dotenv import load_dotenv
import json

load_dotenv()

def test_openai_connection():
    """Test OpenAI API connection and response"""
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(" No OpenAI API key found in .env file")
        return False
    
    print(f"🔑 API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Test basic connection
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Simple test prompt
        test_caption = "a photography of a woman in a pink top standing on a street at night"
        
        prompt = f"""
Based on this image description: "{test_caption}"

Recommend 3 songs that would fit this scene. Respond in JSON format:
{{
    "scene_analysis": {{
        "mood": "detected mood",
        "setting": "urban night scene",
        "energy_level": "medium"
    }},
    "recommendations": [
        {{
            "song_title": "Song Name",
            "artist": "Artist Name",
            "genre": "Genre",
            "why_it_fits": "Explanation"
        }}
    ]
}}
"""
        
        print(" Sending test request to OpenAI...")
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a music expert. Always respond with valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        print(" OpenAI response received!")
        
        # Print raw response
        raw_content = response.choices[0].message.content
        print(f" Raw response:\n{raw_content}")
        
        # Try to parse JSON
        try:
            parsed_response = json.loads(raw_content)
            print(" JSON parsing successful!")
            print(f" Parsed response: {json.dumps(parsed_response, indent=2)}")
            return True
        except json.JSONDecodeError as e:
            print(f" JSON parsing failed: {e}")
            print(" Trying to extract JSON from response...")
            
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
            if json_match:
                try:
                    extracted_json = json.loads(json_match.group())
                    print(" JSON extraction successful!")
                    print(f" Extracted: {json.dumps(extracted_json, indent=2)}")
                    return True
                except:
                    print(" Extracted text is not valid JSON")
            
            return False
            
    except Exception as e:
        print(f" OpenAI API error: {e}")
        return False

if __name__ == "__main__":
    test_openai_connection()
