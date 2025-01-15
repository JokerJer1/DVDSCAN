import os
import logging
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from ocr_processor import process_image
from price_lookup import get_watchcount_prices

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dvd-spine-ocr-secret"

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
        file.save(filepath)
        logger.debug(f"File saved successfully: {filepath}")

        # Process image with OCR
        logger.debug("Starting OCR processing")
        text = process_image(filepath)
        if not text:
            logger.warning("OCR processing failed to extract text")
            return jsonify({
                'status': 'error',
                'error': 'ocr_failed',
                'message': 'No text could be extracted from the image'
            }), 422

        # Get price information
        logger.debug(f"Looking up prices for: {text}")
        prices = get_watchcount_prices(text)
        if 'error' in prices:
            logger.warning(f"Price lookup failed: {prices['error']}")
            return jsonify({
                'status': 'error',
                'error': 'price_lookup_failed',
                'message': prices['error']
            }), 422

        # Clean up the uploaded file
        try:
            os.remove(filepath)
            logger.debug(f"Temporary file removed: {filepath}")
        except Exception as cleanup_error:
            logger.error(f"Failed to remove temporary file: {cleanup_error}")
            # Continue with response despite cleanup failure

        # Return successful response
        return jsonify({
            'status': 'success',
            'data': {
                'text': text,
                'prices': {
                    'average': prices['average_price'],
                    'lowest': prices['lowest_price'],
                    'highest': prices['highest_price'],
                    'results_count': prices['num_results']
                }
            }
        })

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        # Clean up file if it exists
        if 'filepath' in locals():
            try:
                os.remove(filepath)
                logger.debug(f"Cleaned up file after error: {filepath}")
            except Exception as cleanup_error:
                logger.error(f"Failed to clean up file after error: {cleanup_error}")

        return jsonify({
            'status': 'error',
            'error': 'processing_failed',
            'message': 'An unexpected error occurred while processing the image'
        }), 500