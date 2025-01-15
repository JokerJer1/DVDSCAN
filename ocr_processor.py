import pytesseract
from PIL import Image, ImageEnhance, ImageOps
import logging
import numpy as np

logger = logging.getLogger(__name__)

def preprocess_image(image):
    """
    Preprocess image to improve OCR accuracy for DVD spine images
    """
    try:
        # Convert to grayscale if not already
        if image.mode != 'L':
            image = image.convert('L')

        # Resize if the image is too large (preserving aspect ratio)
        max_dimension = 1200
        if max(image.size) > max_dimension:
            ratio = max_dimension / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)

        # Denoise
        image = ImageOps.autocontrast(image, cutoff=2)

        # Binarization with a slightly higher threshold for text
        image = image.point(lambda x: 0 if x < 140 else 255, '1')

        return image
    except Exception as e:
        logger.error(f"Error preprocessing image: {str(e)}")
        return None

def process_image(image_path):
    """
    Process an image file using Tesseract OCR and return extracted text
    Optimized for DVD spine images which typically have vertical text
    """
    try:
        # Open and verify the image
        image = Image.open(image_path)
        if image.mode == 'RGBA':
            # Convert RGBA to RGB to avoid transparency issues
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background

        # Preprocess the image
        processed_image = preprocess_image(image)
        if processed_image is None:
            logger.error("Image preprocessing failed")
            return None

        # Configure Tesseract parameters
        # --oem 3: Use LSTM OCR Engine
        # --psm 5: Assume vertical text
        # -c parameters to improve text detection
        custom_config = r'--oem 3 --psm 5 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-:.\' '

        # Extract text using Tesseract
        text = pytesseract.image_to_string(
            processed_image,
            config=custom_config,
            lang='eng'  # Explicitly specify English language
        )

        # Clean up the extracted text
        cleaned_text = ' '.join(filter(None, [line.strip() for line in text.split('\n')]))

        if not cleaned_text:
            logger.warning("No text could be extracted from the image")
            return None

        logger.debug(f"Extracted text: {cleaned_text}")
        return cleaned_text

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return None