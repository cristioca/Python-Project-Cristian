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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
