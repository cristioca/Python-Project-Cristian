from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
# import functions from custom package
from scraper.movie_scraper import scrape_movies, get_movie_description
from datetime import datetime, timedelta
import requests
import threading

app = Flask(__name__)
app.secret_key = 'movie_bot_secret_key'  # Required for session

# Ensure data directory exists
os.makedirs('data', exist_ok=True)
os.makedirs('static/images', exist_ok=True)

# Path to the CSV file
DATA_FILE = 'data/movies.csv'
UPDATE_INTERVAL = timedelta(days=1)  # Update database every day

# Global progress tracking
progress_data = {
    'progress': 0.0,
    'status': 'Not started',
    'complete': False
}

# Flag to signal stopping the update process
stop_update_flag = False

def should_update_database():
    """Check if database should be updated based on last modification time"""
    if not os.path.exists(DATA_FILE):
        return True
    
    last_modified = datetime.fromtimestamp(os.path.getmtime(DATA_FILE))
    return datetime.now() - last_modified > UPDATE_INTERVAL

def update_progress(progress, status):
    """Update the global progress data"""
    global progress_data
    progress_data['progress'] = progress
    progress_data['status'] = status
    
def reset_progress():
    """Reset progress tracking"""
    global progress_data, stop_update_flag
    progress_data = {
        'progress': 0.0,
        'status': 'Not started',
        'complete': False
    }
    stop_update_flag = False

def run_quick_update():
    """Run quick update in a separate thread with progress tracking"""
    try:
        from scraper.movie_scraper import quick_update_titles
        success = quick_update_titles(update_progress, lambda: stop_update_flag)
        progress_data['complete'] = True
        progress_data['progress'] = 1.0
        progress_data['status'] = 'Complete' if success else 'Stopped' if stop_update_flag else 'Failed'
    except Exception as e:
        progress_data['status'] = f"Error: {str(e)}"
        progress_data['complete'] = True

def run_full_update():
    """Run full update in a separate thread with progress tracking"""
    try:
        success = scrape_movies(update_progress, lambda: stop_update_flag)
        progress_data['complete'] = True
        progress_data['progress'] = 1.0
        progress_data['status'] = 'Complete' if success else 'Stopped' if stop_update_flag else 'Failed'
    except Exception as e:
        progress_data['status'] = f"Error: {str(e)}"
        progress_data['complete'] = True

@app.route('/progress')
def get_progress():
    """Return current progress data as JSON"""
    return jsonify(progress_data)

@app.route('/stop_update')
def stop_update():
    """Stop the update process"""
    global stop_update_flag
    stop_update_flag = True
    return jsonify({"status": "stopping"})

@app.route('/quick_update')
def quick_update():
    """Start quick update process and show progress page"""
    reset_progress()
    # Start update in background thread
    thread = threading.Thread(target=run_quick_update)
    # daemon - a background thread that automatically terminates when the main program exits
    thread.daemon = True
    thread.start()
    return render_template('progress.html', operation='Quick Update (only titles)')

@app.route('/update_database')
def update_database():
    """Start full update process and show progress page"""
    reset_progress()
    # Start update in background thread
    thread = threading.Thread(target=run_full_update)
    thread.daemon = True
    thread.start()
    return render_template('progress.html', operation='Full Database Update')

@app.route('/movie/<path:movie_url>')
def get_description(movie_url):
    """Get and update movie description, cast and image"""
    from scraper.movie_scraper import close_drivers
    
    try:
        print(f"Received request for movie URL: /{movie_url}")
        
        # Update CSV file with description
        df = pd.read_csv(DATA_FILE)
        
        # Check if the movie exists in the database
        if not any(df['movie_url'] == f"/{movie_url}"):
            print(f"Movie URL not found in database: /{movie_url}")
            return jsonify({'error': 'Movie not found in database'}), 404
        
        # Check if we already have a description that's not the default
        movie_row = df.loc[df['movie_url'] == f"/{movie_url}"]
        description = movie_row['description'].iloc[0]
        large_image_path = movie_row['large_image_path'].iloc[0] if 'large_image_path' in movie_row and not pd.isna(movie_row['large_image_path'].iloc[0]) else None
        letterboxd_url = f"https://letterboxd.com{movie_url}"
        
        # If we don't have a proper description or large image, fetch them
        if description == "Details" or not large_image_path:
            print("Description or large image not found in database, fetching from web...")
            
            # Reset progress for this operation
            reset_progress()
            update_progress(0.1, f"Fetching details for {movie_row['title'].iloc[0]}")
            
            # Get description and image from Letterboxd
            movie_details = get_movie_description(f"/{movie_url}")
            update_progress(0.5, "Processing movie details")
            print(f"Movie details: {movie_details}")
            
            # Update description if needed
            # If we only have a placeholder description, replace it with the real description we just fetched from the web, both in the database and in our current response.
            if description == "Details":
                df.loc[df['movie_url'] == f"/{movie_url}", 'description'] = movie_details['description']
                description = movie_details['description']
            
            # Download and save larger image if available and needed
            if movie_details['large_image_url'] and not large_image_path:
                try:
                    update_progress(0.7, "Downloading movie image")
                    # find the row in the DataFrame that has the matching movie URL, extract the movie title from that row, asign to movie_title
                    movie_title = df.loc[df['movie_url'] == f"/{movie_url}", 'title'].iloc[0]
                    movie_year = df.loc[df['movie_url'] == f"/{movie_url}", 'year'].iloc[0]
                    # replaces all non_alphanumerics with "_"
                    safe_title = "".join([c if c.isalnum() else "_" for c in movie_title])
                    image_filename = f"{safe_title}_{movie_year}_large.jpg"
                    large_image_path = f"images/{image_filename}"
                    
                    # Check if the image already exists
                    if not os.path.exists(os.path.join('static', large_image_path)):
                        print(f"Downloading image from: {movie_details['large_image_url']}")
                        response = requests.get(movie_details['large_image_url'], stream=True)
                        if response.status_code == 200:
                            with open(os.path.join('static', large_image_path), 'wb') as img_file:
                                for chunk in response.iter_content(1024):
                                    img_file.write(chunk)
                            print(f"Image saved to: {large_image_path}")
                        else:
                            print(f"Failed to download image: {response.status_code}")
                    else:
                        print(f"Image already exists at: {large_image_path}")
                except Exception as img_err:
                    print(f"Error downloading large image: {img_err}")
            
            # Update the large image path in the database
            if large_image_path:
                df.loc[df['movie_url'] == f"/{movie_url}", 'large_image_path'] = large_image_path
            
            # Save the updated database
            update_progress(0.9, "Saving updated database")
            df.to_csv(DATA_FILE, index=False)
            update_progress(1.0, "Complete")
            
            # Get the Letterboxd URL if available
            if 'letterboxd_url' in movie_details:
                letterboxd_url = movie_details['letterboxd_url']
        else:
            print(f"Using cached description and image for {movie_url}")
        
        response_data = {
            'description': description,
            'large_image_path': large_image_path,
            'letterboxd_url': letterboxd_url
        }
        print(f"Sending response: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        print(f"Error in get_description: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        # Ensure all browser instances are closed
        close_drivers()


@app.route('/')
def index():
    # Get current year for the search form
    current_year = datetime.now().year
    
    # Initialize status variables
    db_status = {
        'exists': os.path.exists(DATA_FILE),
        'movie_count': 0,
        'last_updated': None,
        'status': 'Not initialized'
    }
    
    # Get available genres for dropdown
    try:
        df = pd.read_csv(DATA_FILE)
        db_status['movie_count'] = len(df)
        # Format the timestamp
        timestamp = os.path.getmtime(DATA_FILE)
        db_status['last_updated'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        db_status['status'] = 'Ready'
        
        if len(df) == 0:
            default_genres = ['Action', 'Drama', 'Comedy', 'Thriller', 'Horror', 'Science Fiction', 
                            'Romance', 'Adventure', 'Crime', 'Documentary']
            db_status['status'] = 'Empty'
            return render_template('index.html', genres=default_genres, 
                                error="No movies found in database. Using default genres.",
                                db_status=db_status, current_year=current_year)
        
        # Extract all unique genres from the comma-separated lists
        all_genres = []
        for genre_list in df['genre'].dropna():
            genres = [g.strip().title() for g in genre_list.split(',')]
            all_genres.extend(genres)
        genres = sorted(list(set(all_genres)))

        
        if not genres:
            genres = ['Action', 'Drama', 'Comedy', 'Thriller', 'Horror', 'Science Fiction', 
                     'Romance', 'Adventure', 'Crime', 'Documentary']
            db_status['status'] = 'No genres found'
    except Exception as e:
        db_status['status'] = 'Error reading data'
        return render_template('index.html', error=f"Error loading data: {str(e)}",
                            db_status=db_status, current_year=current_year)
        
    return render_template('index.html', genres=genres, db_status=db_status, current_year=current_year)

@app.route('/recommend', methods=['POST'])
def recommend():
    # Get and validate genre parameter
    selected_genre = request.form.get('genre', '')
    if not selected_genre:
        return render_template('index.html', 
                              error="Please select a genre",
                              genres=sorted(pd.read_csv(DATA_FILE)['genre'].unique()),
                              current_year=datetime.now().year)
    
    # Validate random parameter
    is_random = request.form.get('random') == 'true'
    
    try:
        # Load the data
        df = pd.read_csv(DATA_FILE)
        
        # Filter by genre (unless "Any Genre" is selected)
        if selected_genre == "Any Genre":
            movies = df
        else:
            # Sanitize genre input
            selected_genre = selected_genre.strip()[:50]  # Limit length for security
            movies = df[df['genre'].str.contains(selected_genre, case=False)]
            
            # If no movies found for this genre, return to index with error
            if len(movies) == 0:
                return render_template('index.html', 
                                      error=f"No movies found for genre: {selected_genre}",
                                      genres=sorted(df['genre'].unique()),
                                      current_year=datetime.now().year)
        
        # Deduplicate movies by URL
        unique_movies = []
        seen_urls = set()
        
        for _, movie in movies.iterrows():
            if movie['movie_url'] not in seen_urls:
                movie_dict = movie.to_dict()
                # Convert genre to title case
                if 'genre' in movie_dict and movie_dict['genre']:
                    movie_dict['genre'] = ', '.join(g.strip().title() for g in movie_dict['genre'].split(','))
                unique_movies.append(movie_dict)
                seen_urls.add(movie['movie_url'])
        
        # Sort by rating
        unique_movies = sorted(unique_movies, key=lambda x: x['rating'], reverse=True)
        
        # If random pick is requested, select a random movie
        if is_random and unique_movies:
            import random
            recommendations = [random.choice(unique_movies)]
            return render_template('results.html', 
                                  recommendations=recommendations, 
                                  genre=selected_genre,
                                  is_random=True)
        else:
            # Get top 5 recommendations
            recommendations = unique_movies[:5]
            
            return render_template('results.html', 
                                  recommendations=recommendations, 
                                  genre=selected_genre)
    except Exception as e:
        return render_template('index.html', 
                              error=f"Error processing recommendation: {str(e)}",
                              genres=sorted(df['genre'].unique()))

# Search and Filtering Functionality
@app.route('/search', methods=['GET'])
def search():
    # Get and sanitize input parameters
    query = request.args.get('query', '').lower().strip()
    
    # Validate year inputs
    try:
        min_year = request.args.get('min_year', '')
        if min_year:
            min_year = int(min_year)
            if min_year < 1900 or min_year > datetime.now().year:
                min_year = 1900
    except (ValueError, TypeError):
        min_year = 1900
        
    try:
        max_year = request.args.get('max_year', '')
        if max_year:
            max_year = int(max_year)
            if max_year < 1900 or max_year > datetime.now().year:
                max_year = datetime.now().year
    except (ValueError, TypeError):
        max_year = datetime.now().year
        
    # Ensure min_year <= max_year
    if min_year and max_year and min_year > max_year:
        min_year, max_year = max_year, min_year
    
    # Validate rating input
    try:
        min_rating = request.args.get('min_rating', '')
        if min_rating:
            min_rating = float(min_rating)
            if min_rating < 0 or min_rating > 5:
                min_rating = 0
    except (ValueError, TypeError):
        min_rating = 0
    
    try:
        df = pd.read_csv(DATA_FILE)
        
        # Filter by search query (title or description)
        if query:
            # Limit query length for security
            query = query[:100]
            df = df[df['title'].str.lower().str.contains(query, na=False) | 
                   df['description'].str.lower().str.contains(query, na=False)]
        
        # Filter by year range
        if min_year:
            df = df[df['year'].astype(str).str.extract(r'(\d+)', expand=False).astype(float) >= float(min_year)]
        
        if max_year:
            df = df[df['year'].astype(str).str.extract(r'(\d+)', expand=False).astype(float) <= float(max_year)]
        
        # Filter by minimum rating
        if min_rating:
            df = df[df['rating'] >= float(min_rating)]
        
        # Deduplicate movies by URL
        unique_movies = []
        seen_urls = set()
        
        for _, movie in df.iterrows():
            if movie['movie_url'] not in seen_urls:
                movie_dict = movie.to_dict()
                # Convert genre to title case
                if 'genre' in movie_dict and movie_dict['genre']:
                    movie_dict['genre'] = ', '.join(g.strip().title() for g in movie_dict['genre'].split(','))
                unique_movies.append(movie_dict)
                seen_urls.add(movie['movie_url'])
        
        # Sort by rating
        unique_movies = sorted(unique_movies, key=lambda x: x['rating'], reverse=True)
        
        # Get top 10 results
        results = unique_movies[:10]
        
        # Get all genres for the filter dropdown
        all_genres = []
        for genre_list in df['genre'].dropna():
            genres = [g.strip().title() for g in genre_list.split(',')]
            all_genres.extend(genres)
        genres = sorted(list(set(all_genres)))
        
        return render_template('search_results.html', 
                              results=results, 
                              query=query,
                              min_year=min_year,
                              max_year=max_year,
                              min_rating=min_rating,
                              genres=genres)
    except Exception as e:
        return render_template('index.html', error=f"Error searching: {str(e)}")


@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html',
                          error_code="404",
                          error_title="Page Not Found",
                          error_description="The page you're looking for doesn't exist or has been moved.",
                          error_details=str(error)), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('error.html',
                          error_code="500",
                          error_title="Internal Server Error",
                          error_description="Something went wrong on our end. Please try again later.",
                          error_details=str(error)), 500

@app.errorhandler(Exception)
def handle_error(error):
    # Check if it's an HTTP error (has a code attribute)
    if hasattr(error, 'code'):
        if error.code == 404:
            return page_not_found(error)
        elif error.code == 500:
            return internal_server_error(error)
        else:
            description = getattr(error, 'description', str(error))
            return render_template('error.html',
                                  error_code=str(error.code),
                                  error_title="Error",
                                  error_description=description,
                                  error_details=None), error.code
    
    print(f"Unexpected error: {str(error)}")
    return render_template('error.html',
                          error_code="500",
                          error_title="Internal Server Error",
                          error_description="Something went wrong on our end. Please try again later.",
                          error_details=None), 500

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        import sys
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Create a sample CSV file if it doesn't exist
if not os.path.exists(DATA_FILE):
    try:
        bundled_csv = resource_path(os.path.join('data', 'movies.csv'))
        if os.path.exists(bundled_csv):
            import shutil
            shutil.copy(bundled_csv, DATA_FILE)
            print(f"Copied bundled movies.csv to {os.path.abspath(DATA_FILE)}")
    except Exception as e:
        print(f"Warning: Could not copy bundled data: {e}")
        # Create a minimal CSV file
        with open(DATA_FILE, 'w') as f:
            f.write('title,year,rating,genre,description,image_path,movie_url\n')
            f.write('Sample Movie,2023,4.5,Drama,Details,None,/film/sample-movie/\n')
        print("Created sample movies.csv file")

def open_browser():
    """Open browser after a short delay"""
    import time
    import webbrowser
    time.sleep(1.5)  # Wait for Flask to start
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    # Print startup message
    print("Starting Movie Picker Bot...")
    print(f"Working directory: {os.getcwd()}")
    print(f"Data directory: {os.path.abspath('data')}")
    print(f"Movies CSV path: {os.path.abspath(DATA_FILE)}")
    
    # Start browser in a separate thread
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start Flask app
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)