import os
import logging
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from ocr_processor import process_image
from price_lookup import get_watchcount_prices
from dotenv import load_dotenv

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or "dvd-spine-ocr-secret"

# Configure upload settings
UPLOAD_FOLDER = '/tmp'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    """Validate file extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    """
    Process uploaded DVD spine image
    Returns:
        JSON response with extracted text and price information
        or error details if processing fails
    """
    logger.debug("Processing new upload request")

    # Validate request has file
    if 'image' not in request.files:
        logger.warning("No file part in request")
        return jsonify({
            'status': 'error',
            'error': 'missing_file',
            'message': 'No file uploaded'
        }), 400

    file = request.files['image']

    # Validate file was selected
    if file.filename == '':
        logger.warning("No file selected")
        return jsonify({
            'status': 'error',
            'error': 'empty_file',
            'message': 'No file selected'
        }), 400

    # Validate file type
    if not allowed_file(file.filename):
        logger.warning(f"Invalid file type: {file.filename}")
        return jsonify({
            'status': 'error',
            'error': 'invalid_file_type',
            'message': 'Invalid file type. Allowed types: PNG, JPG, JPEG'
        }), 400

    try:
        # Save the uploaded file with secure filename
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Ensure upload directory exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        file.save(filepath)
        logger.debug(f"File saved successfully: {filepath}")

        # Process image with OCR
        logger.debug("Starting OCR processing")
        try:
            text = process_image(filepath)
            if not text:
                return jsonify({
                    'status': 'error',
                    'error': 'ocr_failed',
                    'message': 'Could not extract text from the image. Please ensure the image is clear and contains readable text.'
                }), 422
        except Exception as ocr_error:
            return jsonify({
                'status': 'error',
                'error': 'ocr_failed',
                'message': str(ocr_error)
            }), 422

        # Get price information
        logger.debug(f"Looking up prices for: {text}")
        try:
            media_type = text.get('type', 'DVD')  # Get media type from OCR response
            titles = text.get('titles', '')  # Get titles from OCR response
            prices = get_watchcount_prices(titles, media_type)
            if 'error' in prices:
                return jsonify({
                    'status': 'error',
                    'error': 'price_lookup_failed',
                    'message': prices['error']
                }), 422
        except Exception as price_error:
            return jsonify({
                'status': 'error',
                'error': 'price_lookup_failed',
                'message': f'Error looking up prices: {str(price_error)}'
            }), 422

        # Return successful response
        response_data = {
            'text': text,
            'prices': prices  # prices is now a list of dictionaries
        }

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Unexpected error processing request: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': 'processing_failed',
            'message': 'An unexpected error occurred while processing the image'
        }), 500

    finally:
        # Clean up the uploaded file
        try:
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
                logger.debug(f"Temporary file removed: {filepath}")
        except Exception as cleanup_error:
            logger.error(f"Failed to clean up temporary file: {cleanup_error}")