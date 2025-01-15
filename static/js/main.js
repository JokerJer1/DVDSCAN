document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons
    feather.replace();

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const processing = document.getElementById('processing');
    const results = document.getElementById('results');
    const error = document.getElementById('error');
    const errorMessage = document.getElementById('error-message');
    const previewContainer = document.getElementById('preview-container');
    const imagePreview = document.getElementById('image-preview');
    const removePreviewBtn = document.getElementById('remove-preview');
    const processImageBtn = document.getElementById('process-image');

    // Handle drag and drop events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        dropZone.classList.add('dragover');
    }

    function unhighlight(e) {
        dropZone.classList.remove('dragover');
    }

    // Handle file drop
    dropZone.addEventListener('drop', handleDrop, false);
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFileSelect(e) {
        const files = e.target.files;
        handleFiles(files);
    }

    function validateFile(file) {
        // Check file type
        if (!file.type.startsWith('image/')) {
            throw new Error('Please upload an image file');
        }

        // Check supported formats
        const supportedTypes = ['image/jpeg', 'image/png'];
        if (!supportedTypes.includes(file.type)) {
            throw new Error('Only JPEG and PNG images are supported');
        }

        // Check file size (16MB limit)
        const maxSize = 16 * 1024 * 1024; // 16MB in bytes
        if (file.size > maxSize) {
            throw new Error('Image size must be less than 16MB');
        }
    }

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            try {
                validateFile(file);
                showPreview(file);
            } catch (error) {
                showError(error.message);
            }
        }
    }

    function showPreview(file) {
        // Hide any previous errors
        error.classList.add('d-none');

        // Create URL for preview
        const reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.src = e.target.result;
            previewContainer.classList.remove('d-none');
            dropZone.classList.add('d-none');
        };
        reader.readAsDataURL(file);
    }

    removePreviewBtn.addEventListener('click', function() {
        // Clear the preview
        imagePreview.src = '';
        previewContainer.classList.add('d-none');
        dropZone.classList.remove('d-none');
        fileInput.value = ''; // Reset file input
    });

    processImageBtn.addEventListener('click', function() {
        if (fileInput.files.length === 0) {
            showError('Please select an image first');
            return;
        }
        uploadFile(fileInput.files[0]);
    });

    function uploadFile(file) {
        const formData = new FormData();
        formData.append('image', file);

        // Show processing state
        processing.classList.remove('d-none');
        results.classList.add('d-none');
        error.classList.add('d-none');

        fetch('/process', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            processing.classList.add('d-none');
            if (data.error) {
                showError(data.error);
            } else {
                showResults(data);
            }
        })
        .catch(err => {
            processing.classList.add('d-none');
            showError('An error occurred while processing the image');
        });
    }

    function showResults(data) {
        document.getElementById('extracted-text').textContent = data.text;
        document.getElementById('avg-price').textContent = 
            `$${data.prices.average_price.toFixed(2)}`;
        document.getElementById('low-price').textContent = 
            `$${data.prices.lowest_price.toFixed(2)}`;
        document.getElementById('high-price').textContent = 
            `$${data.prices.highest_price.toFixed(2)}`;

        results.classList.remove('d-none');
        error.classList.add('d-none');
    }

    function showError(message) {
        errorMessage.textContent = message;
        error.classList.remove('d-none');
        results.classList.add('d-none');
    }
});