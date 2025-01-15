import pytesseract
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def process_image(image_path):
    """
    Process an image file using Tesseract OCR and return extracted text
    """
    try:
        # Open the image
        image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Extract text using Tesseract
        text = pytesseract.image_to_string(image)
        
        # Clean up the text
        cleaned_text = ' '.join(text.split())
        
        logger.debug(f"Extracted text: {cleaned_text}")
        return cleaned_text

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return None
