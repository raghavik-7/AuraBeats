import hashlib
import time
import logging
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

class SimpleSecurityManager:
    def __init__(self):
        self.processing_logs = {}
    
    def secure_image_processing(self, image_data: bytes, session_id: str, 
                              captioner, context: str = ""):
        """
        Process image securely - generate caption and immediately delete image
        """
        try:
            # Create processing ID for tracking
            processing_id = hashlib.sha256(f"{session_id}{time.time()}".encode()).hexdigest()[:16]
            
            # Create non-reversible hash for logging
            image_hash = hashlib.sha256(image_data).hexdigest()[:16]
            
            # Log start
            self.processing_logs[processing_id] = {
                'session_id': session_id,
                'image_hash': image_hash,
                'timestamp': time.time(),
                'status': 'processing'
            }
            
            # Convert to PIL Image
            image = Image.open(BytesIO(image_data))
            
            # Generate caption
            caption = captioner.generate_detailed_caption(image)
            
            # IMMEDIATELY delete image data
            del image_data
            del image
            
            # Update log
            self.processing_logs[processing_id]['status'] = 'completed'
            self.processing_logs[processing_id]['caption_length'] = len(caption)
            
            logger.info(f" Secure processing completed: {processing_id}")
            return caption, processing_id
            
        except Exception as e:
            logger.error(f"Secure processing failed: {e}")
            # Cleanup on error
            try:
                del image_data
                del image
            except:
                pass
            return f"Error: {str(e)}", processing_id
