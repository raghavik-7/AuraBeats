import base64

def image_to_base64(image_path):
    """Convert image to base64 string"""
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        print(f" Image converted successfully!")
        print(f"📏 Base64 length: {len(image_data)} characters")
        return image_data
    except FileNotFoundError:
        print(f" Image file '{image_path}' not found!")
        return None

if __name__ == "__main__":
    # Replace with your image path
    image_path = "test_image.jpg"
    base64_data = image_to_base64(image_path)
    
    if base64_data:
        # Save to file for easy copying
        with open("image_base64.txt", "w") as f:
            f.write(base64_data)
        print(" Base64 data saved to 'image_base64.txt'")
