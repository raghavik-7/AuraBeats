import requests
import base64
from PIL import Image

def debug_captioning():
    """Debug the captioning specifically"""
    
    # Test 1: Test the captioner directly
    print(" Testing captioner directly...")
    try:
        from fixed_captioning import ReliableImageCaptioner
        captioner = ReliableImageCaptioner(model_name="blip")
        
        image = Image.open("test_image.jpg")
        caption = captioner.generate_detailed_caption(image)
        print(f" Direct caption: {caption}")
        
    except Exception as e:
        print(f" Direct test failed: {e}")
    
    # Test 2: Test through API
    print("\n🌐 Testing through API...")
    try:
        with open("test_image.jpg", "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
        
        payload = {
            'image': image_data,
            'context': 'Debug test',
            'num_songs': 3
        }
        
        response = requests.post(
            "http://localhost:5000/recommend",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f" API caption: {result.get('image_caption', 'No caption')}")
        else:
            print(f" API failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f" API test failed: {e}")

if __name__ == "__main__":
    debug_captioning()
