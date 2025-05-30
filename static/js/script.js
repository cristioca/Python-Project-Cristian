function showMovieDetails(movieUrl) {
    console.log("Fetching details for:", movieUrl);
    const movieCard = document.querySelector(`[data-movie-url="${movieUrl}"]`);
    if (movieCard) {
        const descElement = movieCard.querySelector('.movie-description');
        const detailsLink = movieCard.querySelector('.details-link');
        if (descElement && detailsLink) {
            // Check if description is already loaded
            if (descElement.innerHTML !== 'Click Details to view description' && 
                descElement.innerHTML !== 'Loading...' &&
                descElement.innerHTML !== 'Error loading description' &&
                !descElement.innerHTML.includes('loading-spinner')) {
                // Toggle the display of details
                movieCard.classList.toggle('details-shown');
                return;
            }
            
            detailsLink.style.display = 'none';
            // Show loading spinner
            descElement.innerHTML = '<div class="loading-spinner"></div> Loading details from Letterboxd, this may take about 10 seconds...';
            
            // Fix URL encoding - don't remove the leading slash
            const fetchUrl = `/movie/${encodeURIComponent(movieUrl)}`;
            console.log("Fetching from URL:", fetchUrl);
            
            fetch(fetchUrl)
                .then(response => {
                    console.log("Response status:", response.status);
                    if (!response.ok) throw new Error(`Network response was not ok: ${response.status}`);
                    return response.json();
                })
                .then(data => {
                    console.log("Received data:", data);
                    if (data.error) throw new Error(data.error);
                    
                    // Letterboxd link is already added in the template
                    
                    // Update description - use innerHTML to render HTML formatting
                    descElement.innerHTML = data.description;
                    
                    // Update image if available
                    if (data.large_image_path) {
                        const imgElement = movieCard.querySelector('.movie-poster img');
                        if (imgElement) {
                            const newImgSrc = `/static/${data.large_image_path}`;
                            console.log("Setting new image src:", newImgSrc);
                            imgElement.src = newImgSrc;
                        }
                    }
                    
                    // Add class to show this card has details displayed
                    movieCard.classList.add('details-shown');
                })
                .catch(error => {
                    console.error('Error:', error);
                    descElement.textContent = 'Error loading description';
                    detailsLink.style.display = 'inline';
                });
        }
    }
}