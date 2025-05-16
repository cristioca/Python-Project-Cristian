import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import random

def scrape_movies():
    """
    Scrape movie data from Letterboxd and save to CSV file
    """
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # List of genres to scrape from Letterboxd
    genres = ['action', 'drama', 'comedy', 'thriller']
    movie_data = []
    
    # User agent to mimic a browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        # Loop through each genre
        for genre in genres:
            # URL for Letterboxd popular movies by genre
            url = f"https://letterboxd.com/films/genre/{genre}/size/small/"
            
            print(f"Scraping {genre} movies from Letterboxd...")
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find movie containers (poster items)
            movie_containers = soup.find_all('div', class_='film-poster')
            
            print("length = ",len(movie_containers))
            # Limit to 10 movies per genre to avoid overloading
            for container in movie_containers[:10]:
                
                try:
                    # Get movie details page URL
                    film_link = container.find('a')
                    if not film_link or not film_link.get('href'):
                        continue
                        
                    # Extract movie ID and title from data attributes
                    title = container.get('data-film-name', "Unknown")
                    year = container.get('data-film-release-year', "Unknown")
                    
                    # Get rating if available
                    rating_element = container.find('span', class_='rating')
                    rating = float(rating_element.text) if rating_element else 0.0
                    
                    # Visit the movie's page to get more details
                    film_url = f"https://letterboxd.com{film_link.get('href')}"
                    
                    # Add a small delay to avoid rate limiting
                    time.sleep(random.uniform(1, 2))
                    
                    film_response = requests.get(film_url, headers=headers)
                    if film_response.status_code == 200:
                        film_soup = BeautifulSoup(film_response.text, 'html.parser')
                        
                        # Get description
                        description_element = film_soup.find('div', class_='film-text-content')
                        description = description_element.text.strip() if description_element else "No description available"
                        
                        # Get more accurate genre information
                        genre_elements = film_soup.select('div.text-sluglist a')
                        film_genres = ", ".join([g.text for g in genre_elements]) if genre_elements else genre
                        
                        # Add to movie data list
                        movie_data.append({
                            'title': title,
                            'year': year,
                            'rating': rating,
                            'genre': film_genres,
                            'description': description
                        })
                        print(f"Scraped: {title} ({year})")
                    
                except Exception as e:
                    print(f"Error extracting movie data: {e}")
                    continue
            
            # Add a delay between genre pages
            time.sleep(random.uniform(2, 3))
        
        # Create DataFrame and save to CSV
        if movie_data:
            df = pd.DataFrame(movie_data)
            df.to_csv('data/movies.csv', index=False)
            print(f"Successfully scraped {len(df)} movies")
            return True
        else:
            print("No movie data was collected. Creating sample dataset.")
            create_sample_dataset()
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        # Create a sample dataset if scraping fails
        create_sample_dataset()
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Create a sample dataset if scraping fails
        create_sample_dataset()
        return False

def create_sample_dataset():
    """Create a sample dataset if web scraping fails"""
    sample_data = [
        {'title': 'The Shawshank Redemption', 'year': '1994', 'rating': 9.3, 'genre': 'Drama', 
         'description': 'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.'},
        {'title': 'The Godfather', 'year': '1972', 'rating': 9.2, 'genre': 'Crime, Drama', 
         'description': 'The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.'},
        {'title': 'The Dark Knight', 'year': '2008', 'rating': 9.0, 'genre': 'Action, Crime, Drama', 
         'description': 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.'},
        {'title': 'Pulp Fiction', 'year': '1994', 'rating': 8.9, 'genre': 'Crime, Drama', 
         'description': 'The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.'},
        {'title': 'Fight Club', 'year': '1999', 'rating': 8.8, 'genre': 'Drama', 
         'description': 'An insomniac office worker and a devil-may-care soapmaker form an underground fight club that evolves into something much, much more.'},
        {'title': 'Inception', 'year': '2010', 'rating': 8.8, 'genre': 'Action, Adventure, Sci-Fi', 
         'description': 'A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.'},
        {'title': 'The Matrix', 'year': '1999', 'rating': 8.7, 'genre': 'Action, Sci-Fi', 
         'description': 'A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.'},
        {'title': 'Goodfellas', 'year': '1990', 'rating': 8.7, 'genre': 'Biography, Crime, Drama', 
         'description': 'The story of Henry Hill and his life in the mob, covering his relationship with his wife Karen Hill and his mob partners Jimmy Conway and Tommy DeVito.'},
        {'title': 'The Silence of the Lambs', 'year': '1991', 'rating': 8.6, 'genre': 'Crime, Drama, Thriller', 
         'description': 'A young F.B.I. cadet must receive the help of an incarcerated and manipulative cannibal killer to help catch another serial killer.'},
        {'title': 'Star Wars: Episode V', 'year': '1980', 'rating': 8.7, 'genre': 'Action, Adventure, Fantasy', 
         'description': 'After the Rebels are brutally overpowered by the Empire on the ice planet Hoth, Luke Skywalker begins Jedi training with Yoda.'}
    ]
    
    df = pd.DataFrame(sample_data)
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/movies.csv', index=False)
    print("Created sample dataset with 10 movies")

if __name__ == "__main__":
    scrape_movies()