let progressInterval;

function startProgress(operation) {
    // Show progress bar
    document.getElementById('progress-container').style.display = 'block';
    document.getElementById('progress-operation').textContent = operation;
    document.getElementById('progress-bar').style.width = '0%';
    document.getElementById('progress-text').textContent = '0%';
    
    // Start polling for progress updates
    progressInterval = setInterval(checkProgress, 1000);
    return false;
}

function checkProgress() {
    fetch('/progress')
        .then(response => response.json())
        .then(data => {
            if (data.complete) {
                clearInterval(progressInterval);
                // Redirect to home page when complete
                window.location.href = '/';
            } else {
                // Update progress bar
                const percent = Math.round(data.progress * 100);
                document.getElementById('progress-bar').style.width = percent + '%';
                document.getElementById('progress-text').textContent = percent + '%';
                document.getElementById('progress-status').textContent = data.status;
            }
        });
}