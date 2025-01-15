import os
import base64
import logging
import time
from openai import OpenAI, OpenAIError, RateLimitError
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert at reading DVD and Blu-ray spine images. "
                            "Extract the main title and determine the media type. "
                            "Rules:\n"
                            "- Remove studio names, ratings, or specifications\n"
                            "- If multiple titles exist, separate with newlines\n"
                            "- Determine if it's a DVD or Blu-ray based on visual cues (case color, logos, etc)\n"
                            "- Return each title followed by media type on same line (e.g., 'Movie Title DVD')\n"
                            "- Preserve exact spelling and capitalization"
                        )
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "What are the titles and media types from this spine?"
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            )

            # Parse the response
            response_text = response.choices[0].message.content.strip()
            titles_with_types = []

            for line in response_text.splitlines():
                if line.strip():
                    # Last word should be the media type
                    parts = line.strip().rsplit(' ', 1)
                    if len(parts) == 2:
                        title, media_type = parts
                        titles_with_types.append(f"{title} {media_type}")

            return {
                "titles": "\n".join(titles_with_types)
            }

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