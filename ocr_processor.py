import os
import base64
import logging
from openai import OpenAI

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def process_image(image_path):
    """
    Process an image file using OpenAI's GPT-4 Vision model to extract text.
    Optimized for DVD spine images which typically have vertical text
    """
    try:
        # Read and encode the image to base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        # Create the API request
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",  # Use the vision-specific model
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert at reading DVD spine images. "
                        "Extract the exact movie title from the spine, ignoring any other text "
                        "such as studio names, ratings, or technical specifications. "
                        "Return only the movie title text, nothing else. "
                        "If you see multiple titles, return them separated by semicolons."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract the movie title(s) from this DVD spine image."
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
            max_tokens=500
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