from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from scraper.movie_scraper import scrape_movies  # Your scraper module

app = Flask(__name__)

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Path to the CSV file
DATA_FILE = 'data/movies.csv'

@app.route('/')
def index():
    # Check if we need to scrape data
    if not os.path.exists(DATA_FILE):
        try:
            scrape_movies()  # This would save data to the CSV file
        except Exception as e:
            return render_template('index.html', error=f"Error scraping data: {str(e)}")
    
    # Get available genres for dropdown
    try:
        df = pd.read_csv(DATA_FILE)
        genres = sorted(df['genre'].unique())
    except Exception as e:
        return render_template('index.html', error=f"Error loading data: {str(e)}")
        
    return render_template('index.html', genres=genres)

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
            df = df[df['year'].astype(str).str.extract('(\d+)', expand=False).astype(float) >= float(min_year)]
        
        if max_year and max_year.isdigit():
            df = df[df['year'].astype(str).str.extract('(\d+)', expand=False).astype(float) <= float(max_year)]
        
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
