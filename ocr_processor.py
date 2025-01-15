import os
import base64
import logging
from PIL import Image
from openai import OpenAI
from io import BytesIO

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def encode_image_to_base64(image_path):
    """
    Convert an image file to base64 string
    """
    try:
        with Image.open(image_path) as image:
            # Convert RGBA to RGB if necessary
            if image.mode == 'RGBA':
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[3])
                image = background

            # Save to BytesIO in JPEG format
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image: {str(e)}")
        return None

def process_image(image_path):
    """
    Process an image file using OpenAI's GPT-4 Vision model to extract text
    Optimized for DVD spine images which typically have vertical text
    """
    try:
        # Encode image to base64
        base64_image = encode_image_to_base64(image_path)
        if not base64_image:
            return None

        # Create the API request
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at reading text from DVD spine images. "
                    "Extract only the title text, ignore any other text or information. "
                    "Return only the extracted title, nothing else."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please read and extract the DVD title from this spine image. "
                            "The text may be vertical or horizontal."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=100
        )

        # Extract the text from the response
        extracted_text = response.choices[0].message.content.strip()

        if not extracted_text:
            logger.warning("No text could be extracted from the image")
            return None

        logger.debug(f"Extracted text: {extracted_text}")
        return extracted_text

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return None