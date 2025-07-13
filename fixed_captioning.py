import torch
from transformers import AutoProcessor, AutoModelForCausalLM, BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReliableImageCaptioner:
    def __init__(self, model_name="blip"):
        """
        Initialize with reliable captioning models
        Options: blip, git-large, git-base
        """
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Initializing {model_name} on {self.device}")
        
        try:
            if model_name == "blip":
                self._load_blip()
            elif model_name == "git-large":
                self._load_git_large()
            else:
                self._load_git_base()
        except Exception as e:
            logger.error(f"Failed to load {model_name}: {e}")
            # Fallback to most reliable model
            self._load_git_base()
    
    def _load_blip(self):
        """Load BLIP model - very reliable"""
        try:
            model_id = "Salesforce/blip-image-captioning-base"
            self.processor = BlipProcessor.from_pretrained(model_id)
            self.model = BlipForConditionalGeneration.from_pretrained(model_id)
            self.model.to(self.device)
            logger.info(" BLIP loaded successfully")
        except Exception as e:
            logger.error(f"BLIP failed: {e}")
            self._load_git_base()
    
    def _load_git_large(self):
        """Load GiT-Large model"""
        try:
            model_id = "microsoft/git-large-coco"
            self.processor = AutoProcessor.from_pretrained(model_id)
            self.model = AutoModelForCausalLM.from_pretrained(model_id)
            self.model.to(self.device)
            logger.info(" GiT-Large loaded successfully")
        except Exception as e:
            logger.error(f"GiT-Large failed: {e}")
            self._load_git_base()
    
    def _load_git_base(self):
        """Load GiT-Base model - most reliable fallback"""
        try:
            model_id = "microsoft/git-base"
            self.processor = AutoProcessor.from_pretrained(model_id)
            self.model = AutoModelForCausalLM.from_pretrained(model_id)
            self.model.to(self.device)
            self.model_name = "git-base"
            logger.info(" GiT-Base loaded successfully")
        except Exception as e:
            logger.error(f"All models failed to load: {e}")
            raise e
    
    def generate_detailed_caption(self, image):
        """Generate detailed caption with error handling"""
        try:
            # Ensure image is in RGB format
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            logger.info(f"Generating caption with {self.model_name}")
            
            if self.model_name == "blip":
                return self._generate_blip_caption(image)
            else:
                return self._generate_git_caption(image)
                
        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            return f"Error generating caption: {str(e)}"
    
    def _generate_blip_caption(self, image):
        """Generate caption using BLIP"""
        try:
            # Conditional generation for more detailed captions
            text = "a photography of"
            inputs = self.processor(image, text, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                out = self.model.generate(**inputs, max_length=100, num_beams=5)
            
            caption = self.processor.decode(out[0], skip_special_tokens=True)
            
            # Also try unconditional generation for comparison
            inputs_uncond = self.processor(image, return_tensors="pt").to(self.device)
            with torch.no_grad():
                out_uncond = self.model.generate(**inputs_uncond, max_length=100, num_beams=5)
            
            caption_uncond = self.processor.decode(out_uncond[0], skip_special_tokens=True)
            
            # Return the longer, more detailed caption
            final_caption = caption if len(caption) > len(caption_uncond) else caption_uncond
            
            logger.info(f"BLIP caption generated: {final_caption}")
            return final_caption
            
        except Exception as e:
            logger.error(f"BLIP caption generation failed: {e}")
            return f"BLIP error: {str(e)}"
    
    def _generate_git_caption(self, image):
        """Generate caption using GiT model"""
        try:
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                generated_ids = self.model.generate(
                    pixel_values=inputs.pixel_values,
                    max_length=100,
                    num_beams=4,
                    temperature=0.8,
                    do_sample=True,
                    early_stopping=True
                )
            
            caption = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            logger.info(f"GiT caption generated: {caption}")
            return caption
            
        except Exception as e:
            logger.error(f"GiT caption generation failed: {e}")
            return f"GiT error: {str(e)}"

# Test function
def test_captioner():
    """Test the captioner with a sample image"""
    try:
        captioner = ReliableImageCaptioner(model_name="blip")
        
        # Create a simple test image if none exists
        from PIL import Image
        import os
        
        if os.path.exists("test_image.jpg"):
            image = Image.open("test_image.jpg")
        else:
            # Create a simple colored image for testing
            image = Image.new('RGB', (224, 224), color='blue')
            image.save("test_image_generated.jpg")
            print("Created test image: test_image_generated.jpg")
        
        caption = captioner.generate_detailed_caption(image)
        print(f"Generated caption: {caption}")
        return caption
        
    except Exception as e:
        print(f"Test failed: {e}")
        return None

if __name__ == "__main__":
    test_captioner()
