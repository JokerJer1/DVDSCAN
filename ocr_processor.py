import pytesseract
from PIL import Image, ImageEnhance, ImageOps
import logging
import numpy as np

logger = logging.getLogger(__name__)

def preprocess_image(image):
    """
    Preprocess image to improve OCR accuracy
    """
    try:
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')

        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Binarization using Otsu's method
        image = image.point(lambda x: 0 if x < 128 else 255, '1')

        # Auto-rotate if needed (DVD spines are often vertical)
        try:
            osd = pytesseract.image_to_osd(image)
            angle = int(''.join(filter(str.isdigit, osd.split('\nRotate: ')[1].split('\n')[0])))
            if angle != 0:
                image = image.rotate(angle, expand=True, fillcolor=255)
        except Exception as e:
            logger.warning(f"Could not determine text orientation: {str(e)}")

        return image
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return None

def process_image(image_path):
    """
    Process an image file using Tesseract OCR and return extracted text
    """
    try:
        # Open the image
        image = Image.open(image_path)

        # Preprocess the image
        processed_image = preprocess_image(image)
        if processed_image is None:
            return None

        # Configure Tesseract parameters
        custom_config = r'--oem 3 --psm 5'  # PSM 5 is good for vertical text

        # Extract text using Tesseract
        text = pytesseract.image_to_string(
            processed_image,
            config=custom_config
        )

        # Clean up the text
        cleaned_text = ' '.join(text.split())

        logger.debug(f"Extracted text: {cleaned_text}")
        return cleaned_text

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return None