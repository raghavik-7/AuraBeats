import requests
import base64
import json
import time

class SystemTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
    
    def test_health(self):
        """Test health endpoint"""
        print(" Testing health endpoint...")
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print(" Health check passed!")
                print(f" Response: {response.json()}")
                return True
            else:
                print(f" Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f" Health check error: {e}")
            return False
    
    def test_recommendation(self, image_path, context="Test image", num_songs=5):
        """Test music recommendation"""
        print(f" Testing recommendation for: {image_path}")
        
        try:
            # Convert image to base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            # Prepare payload
            payload = {
                'image': image_data,
                'context': context,
                'num_songs': num_songs,
                'session_id': f'test_session_{int(time.time())}'
            }
            
            print(" Sending request...")
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/recommend",
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(" Recommendation successful!")
                print(f" Processing time: {processing_time:.2f} seconds")
                self.display_results(result)
                return True
            else:
                print(f" Recommendation failed: {response.status_code}")
                print(f" Error: {response.text}")
                return False
                
        except FileNotFoundError:
            print(f" Image file '{image_path}' not found!")
            return False
        except Exception as e:
            print(f" Test error: {e}")
            return False
    
    def display_results(self, result):
        """Display recommendation results"""
        print("\n" + "="*60)
        print(" IMAGE CAPTION:")
        print("-" * 30)
        print(result.get('image_caption', 'No caption'))
        
        print("\n MUSIC RECOMMENDATIONS:")
        print("-" * 30)
        
        recommendations = result.get('music_recommendations', {})
        
        if 'recommendations' in recommendations:
            for i, rec in enumerate(recommendations['recommendations'], 1):
                print(f"\n{i}.  {rec.get('song_title', 'Unknown')} - {rec.get('artist', 'Unknown Artist')}")
                print(f"    Genre: {rec.get('genre', 'Not specified')}")
                print(f"    Why it fits: {rec.get('why_it_fits', 'No explanation')}")
        
        if 'scene_analysis' in recommendations:
            analysis = recommendations['scene_analysis']
            print(f"\n SCENE ANALYSIS:")
            print("-" * 30)
            print(f"Mood: {analysis.get('mood', 'Not analyzed')}")
            print(f"Energy: {analysis.get('energy_level', 'Not analyzed')}")
            print(f"Setting: {analysis.get('setting', 'Not analyzed')}")
            print(f"Activity: {analysis.get('activity', 'Not analyzed')}")
        
        print("\n" + "="*60)
    
    def run_full_test(self, image_paths):
        """Run complete test suite"""
        print(" Starting Full System Test")
        print("="*60)
        
        # Test health
        if not self.test_health():
            print(" Health test failed. Stopping tests.")
            return
        
        print("\n")
        
        # Test recommendations
        for i, image_path in enumerate(image_paths, 1):
            print(f"\n TEST {i}/{len(image_paths)}")
            print("-" * 40)
            success = self.test_recommendation(
                image_path, 
                context=f"Test image {i}",
                num_songs=3
            )
            
            if not success:
                print(f" Test {i} failed")
            
            print("\n" + "-"*40)
        
        print("\n Test suite completed!")

def main():
    """Main test function"""
    tester = SystemTester()
    
    # List your test images here
    test_images = [
        "test_image.jpg",  # Replace with your actual image paths
        # "happy_image.jpg",
        # "sad_image.jpg",
        # "party_image.jpg"
    ]
    
    # Run tests
    tester.run_full_test(test_images)

if __name__ == "__main__":
    main()
