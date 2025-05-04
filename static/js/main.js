/**
 * YouTube GPT Analyzer - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Toggle summary show more/less
    const summaryToggles = document.querySelectorAll('.summary-toggle');
    summaryToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const summaryContainer = this.closest('.summary-container');
            const preview = summaryContainer.querySelector('.summary-preview');
            const fullSummary = summaryContainer.querySelector('.full-summary');
            
            if (this.getAttribute('data-action') === 'expand') {
                preview.classList.add('d-none');
                fullSummary.classList.remove('d-none');
            } else {
                preview.classList.remove('d-none');
                fullSummary.classList.add('d-none');
            }
        });
    });
    // Form submission handling with loading state
    const videoForm = document.getElementById('videoForm');
    if (videoForm) {
        videoForm.addEventListener('submit', function() {
            // Add YouTube-style loading progress bar
            const progressBar = document.createElement('div');
            progressBar.className = 'youtube-progress';
            document.body.appendChild(progressBar);
            
            // Disable submit button and show loading state
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Analyzing...';
            }
        });
    }
    
    // Video URL validation
    const videoUrlInput = document.getElementById('video_url');
    if (videoUrlInput) {
        videoUrlInput.addEventListener('input', function() {
            validateYouTubeUrl(this.value);
        });
    }
    
    // Function to validate YouTube URL
    function validateYouTubeUrl(url) {
        const videoForm = document.getElementById('videoForm');
        const submitBtn = document.getElementById('analyzeBtn');
        
        if (!url) {
            submitBtn.disabled = false;
            return;
        }
        
        // Simple regex for YouTube URL validation
        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
        
        if (youtubeRegex.test(url)) {
            submitBtn.disabled = false;
            videoUrlInput.classList.remove('is-invalid');
            videoUrlInput.classList.add('is-valid');
        } else {
            submitBtn.disabled = true;
            videoUrlInput.classList.remove('is-valid');
            videoUrlInput.classList.add('is-invalid');
            
            // Add validation feedback if not already present
            if (!document.querySelector('.invalid-feedback')) {
                const feedbackDiv = document.createElement('div');
                feedbackDiv.className = 'invalid-feedback';
                feedbackDiv.textContent = 'Please enter a valid YouTube URL';
                videoUrlInput.parentNode.appendChild(feedbackDiv);
            }
        }
    }
    
    // Enable Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-resize textarea inputs
    const textareas = document.querySelectorAll('textarea.auto-resize');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Initial resize
        textarea.dispatchEvent(new Event('input'));
    });
});

// Format duration helper function
function formatDuration(seconds) {
    if (!seconds) return "0:00";
    
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hrs > 0) {
        return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}
