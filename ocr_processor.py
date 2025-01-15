import os
import base64
import logging
import time
from openai import OpenAI, OpenAIError, RateLimitError

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def process_image(image_path, max_retries=3, initial_delay=1):
    """
    Process an image file using OpenAI's GPT-4 Vision model to extract text.
    Optimized for DVD spine images which typically have vertical text.
    """
    if not os.path.exists(image_path):
        logger.error(f"Image file not found: {image_path}")
        return None

    for attempt in range(max_retries):
        try:
            # Read and encode the image to base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")

            logger.debug("Making API request to OpenAI")
            response = client.chat.completions.create(
                model="gpt-4-vision-preview",  # Using the correct vision model
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

            # Extract and validate the text from the response
            extracted_text = response.choices[0].message.content.strip()
            logger.debug(f"Raw API response text: {extracted_text}")

            if not extracted_text:
                logger.warning("API returned empty text")
                return None

            logger.info(f"Successfully extracted text: {extracted_text}")
            return extracted_text

        except RateLimitError as e:
            delay = initial_delay * (2 ** attempt)
            logger.warning(f"Rate limit hit, attempt {attempt + 1}/{max_retries}. Waiting {delay} seconds...")

            if attempt < max_retries - 1:
                time.sleep(delay)
                continue
            else:
                logger.error("Rate limit retries exhausted")
                raise Exception("API rate limit exceeded. Please try again in a few moments.")

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
            raise Exception(f"Error communicating with OpenAI API: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error processing image: {str(e)}", exc_info=True)
            return None