document.addEventListener('DOMContentLoaded', function() {
    // Initialize Feather icons
    feather.replace();

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const processing = document.getElementById('processing');
    const results = document.getElementById('results');
    const error = document.getElementById('error');
    const errorMessage = document.getElementById('error-message');

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

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            if (file.type.startsWith('image/')) {
                uploadFile(file);
            } else {
                showError('Please upload an image file');
            }
        }
    }

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
