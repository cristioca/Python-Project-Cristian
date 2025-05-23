from flask import Flask, render_template, request, jsonify, redirect, url_for
import pandas as pd
import os
from scraper.movie_scraper import scrape_movies, create_sample_dataset, get_movie_description
from datetime import datetime, timedelta

app = Flask(__name__)

# Ensure data directory exists
os.makedirs('data', exist_ok=True)
os.makedirs('static/images', exist_ok=True)

# Path to the CSV file
DATA_FILE = 'data/movies.csv'
UPDATE_INTERVAL = timedelta(days=1)  # Update database every day

def should_update_database():
    """Check if database should be updated based on last modification time"""
    if not os.path.exists(DATA_FILE):
        return True
    
    last_modified = datetime.fromtimestamp(os.path.getmtime(DATA_FILE))
    return datetime.now() - last_modified > UPDATE_INTERVAL

@app.route('/update_database')
def update_database():
    """Manual route to update the movie database"""
    try:
        success = scrape_movies()
        if success:
            return redirect(url_for('index'))
        return render_template('index.html', error="Failed to update database. Please make sure Chrome is installed.")
    except Exception as e:
        return render_template('index.html', error=f"Error updating database: {str(e)}")

@app.route('/movie/<path:movie_url>')
def get_description(movie_url):
    """Get and update movie description"""
    try:
        # Get description from Letterboxd
        description = get_movie_description(f"/{movie_url}")
        
        # Update CSV file
        df = pd.read_csv(DATA_FILE)
        df.loc[df['movie_url'] == f"/{movie_url}", 'description'] = description
        df.to_csv(DATA_FILE, index=False)
        
        return jsonify({'description': description})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
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
                                db_status=db_status)
        
        # Extract all unique genres from the comma-separated lists
        all_genres = []
        for genre_list in df['genre'].dropna():
            genres = [g.strip() for g in genre_list.split(',')]
            all_genres.extend(genres)
        genres = sorted(list(set(all_genres)))
        
        if not genres:
            genres = ['Action', 'Drama', 'Comedy', 'Thriller', 'Horror', 'Science Fiction', 
                     'Romance', 'Adventure', 'Crime', 'Documentary']
            db_status['status'] = 'No genres found'
    except Exception as e:
        db_status['status'] = 'Error reading data'
        return render_template('index.html', error=f"Error loading data: {str(e)}",
                            db_status=db_status)
        
    return render_template('index.html', genres=genres, db_status=db_status)

@app.route('/recommend', methods=['POST'])
def recommend():
    selected_genre = request.form.get('genre')
    
    try:
        # Load the data
        df = pd.read_csv(DATA_FILE)
        
        # Filter by genre
        movies = df[df['genre'].str.contains(selected_genre, case=False)]
        
        # Sort by rating (assuming you have a rating column)
        if 'rating' in df.columns:
            movies = movies.sort_values(by='rating', ascending=False)
        
        # Get top 5 recommendations
        recommendations = movies.head(5).to_dict('records')
        
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
    query = request.args.get('query', '').lower()
    min_year = request.args.get('min_year', '')
    max_year = request.args.get('max_year', '')
    min_rating = request.args.get('min_rating', '')
    
    try:
        df = pd.read_csv(DATA_FILE)
        
        # Filter by search query (title or description)
        if query:
            df = df[df['title'].str.lower().str.contains(query, na=False) | 
                   df['description'].str.lower().str.contains(query, na=False)]
        
        # Filter by year range
        if min_year and min_year.isdigit():
            df = df[df['year'].astype(str).str.extract(r'(\d+)', expand=False).astype(float) >= float(min_year)]
        
        if max_year and max_year.isdigit():
            df = df[df['year'].astype(str).str.extract(r'(\d+)', expand=False).astype(float) <= float(max_year)]
        
        # Filter by minimum rating
        if min_rating and min_rating.replace('.', '', 1).isdigit():
            df = df[df['rating'] >= float(min_rating)]
        
        # Get results
        results = df.sort_values(by='rating', ascending=False).head(10).to_dict('records')
        
        # Get all genres for the filter dropdown
        all_genres = []
        for genre_list in df['genre'].dropna():
            genres = [g.strip() for g in genre_list.split(',')]
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)