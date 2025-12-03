// ==================== Configuration ====================
// UPDATE THIS URL after deploying CloudFormation!
const API_BASE_URL = 'YOUR_API_GATEWAY_URL'; // e.g., 'https://xxxxxxxx.execute-api.us-east-1.amazonaws.com/prod'

// ==================== DOM Elements ====================
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const resultsGrid = document.getElementById('resultsGrid');
const resultsTitle = document.getElementById('resultsTitle');
const resultsCount = document.getElementById('resultsCount');
const emptyState = document.getElementById('emptyState');
const fileInput = document.getElementById('fileInput');
const uploadBox = document.getElementById('uploadBox');
const uploadContent = document.getElementById('uploadContent');
const uploadPreview = document.getElementById('uploadPreview');
const previewImage = document.getElementById('previewImage');
const customLabelsInput = document.getElementById('customLabels');
const uploadBtn = document.getElementById('uploadBtn');
const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toastMessage');
const loadingOverlay = document.getElementById('loadingOverlay');

let selectedFile = null;

// ==================== Search Functions ====================
async function searchPhotos(query) {
    if (!query.trim()) {
        showToast('Please enter a search query', 'error');
        return;
    }

    showLoading(true);

    try {
        const response = await fetch(`${API_BASE_URL}/search?q=${encodeURIComponent(query)}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Search results:', data);
        
        displayResults(data.results || [], query);
    } catch (error) {
        console.error('Search error:', error);
        showToast('Search failed. Please check your API configuration.', 'error');
        displayResults([], query);
    } finally {
        showLoading(false);
    }
}

function displayResults(results, query) {
    resultsTitle.textContent = query ? `Results for "${query}"` : 'Your Photos';
    resultsCount.textContent = `${results.length} photo${results.length !== 1 ? 's' : ''} found`;

    if (results.length === 0) {
        resultsGrid.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <h3>No photos found</h3>
                <p>Try different keywords or upload new photos</p>
            </div>
        `;
        return;
    }

    resultsGrid.innerHTML = results.map((photo, index) => `
        <div class="photo-card" style="animation-delay: ${index * 0.1}s">
            <div class="image-container">
                <img src="${photo.url}" alt="Photo" onerror="this.src='https://via.placeholder.com/300x220?text=Image+Not+Found'">
            </div>
            <div class="photo-card-info">
                <div class="photo-labels">
                    ${(photo.labels || []).slice(0, 5).map(label => 
                        `<span class="label-tag">${label}</span>`
                    ).join('')}
                </div>
            </div>
        </div>
    `).join('');
}

function searchFor(keyword) {
    searchInput.value = keyword;
    searchPhotos(keyword);
}

// ==================== Upload Functions ====================
async function uploadPhoto() {
    if (!selectedFile) {
        showToast('Please select a file first', 'error');
        return;
    }

    const customLabels = customLabelsInput.value.trim();
    const filename = `${Date.now()}-${selectedFile.name.replace(/[^a-zA-Z0-9.-]/g, '_')}`;

    setUploadLoading(true);

    try {
        const headers = {
            'Content-Type': selectedFile.type || 'image/jpeg'
        };

        if (customLabels) {
            headers['x-amz-meta-customLabels'] = customLabels;
        }

        const response = await fetch(`${API_BASE_URL}/photos/${filename}`, {
            method: 'PUT',
            headers: headers,
            body: selectedFile
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.status}`);
        }

        showToast('Photo uploaded successfully! It will be indexed shortly.', 'success');
        clearPreview();
        customLabelsInput.value = '';
    } catch (error) {
        console.error('Upload error:', error);
        showToast('Upload failed. Please check your API configuration.', 'error');
    } finally {
        setUploadLoading(false);
    }
}

function handleFileSelect(file) {
    if (!file) return;

    if (!file.type.startsWith('image/')) {
        showToast('Please select an image file', 'error');
        return;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
        showToast('File size must be less than 10MB', 'error');
        return;
    }

    selectedFile = file;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        uploadContent.style.display = 'none';
        uploadPreview.style.display = 'block';
        uploadBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

function clearPreview() {
    selectedFile = null;
    fileInput.value = '';
    previewImage.src = '';
    uploadContent.style.display = 'flex';
    uploadPreview.style.display = 'none';
    uploadBtn.disabled = true;
}

// ==================== UI Helper Functions ====================
function showLoading(show) {
    loadingOverlay.classList.toggle('show', show);
}

function setUploadLoading(loading) {
    const btnText = uploadBtn.querySelector('.upload-btn-text');
    const btnLoading = uploadBtn.querySelector('.upload-btn-loading');
    
    if (loading) {
        btnText.style.display = 'none';
        btnLoading.style.display = 'inline';
        uploadBtn.disabled = true;
    } else {
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
        uploadBtn.disabled = !selectedFile;
    }
}

function showToast(message, type = 'success') {
    toast.className = `toast ${type}`;
    toastMessage.textContent = message;
    
    // Force reflow
    toast.offsetHeight;
    
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ==================== Event Listeners ====================
// Search events
searchBtn.addEventListener('click', () => searchPhotos(searchInput.value));
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        searchPhotos(searchInput.value);
    }
});

// Upload box events
uploadBox.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => handleFileSelect(e.target.files[0]));

// Drag and drop events
uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadBox.classList.add('dragover');
});

uploadBox.addEventListener('dragleave', () => {
    uploadBox.classList.remove('dragover');
});

uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadBox.classList.remove('dragover');
    handleFileSelect(e.dataTransfer.files[0]);
});

// Upload button event
uploadBtn.addEventListener('click', uploadPhoto);

// ==================== Initialize ====================
document.addEventListener('DOMContentLoaded', () => {
    // Check if API URL is configured
    if (API_BASE_URL === 'YOUR_API_GATEWAY_URL') {
        console.warn('⚠️ API_BASE_URL not configured! Update the API_BASE_URL in script.js');
        showToast('Configure API_BASE_URL in script.js', 'error');
    }
    
    // Display initial empty state
    displayResults([], '');
});

