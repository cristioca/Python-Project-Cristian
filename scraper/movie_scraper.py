from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import random
import requests
from urllib.parse import urlparse

def scrape_movies():
    """
    Scrape movie data from Letterboxd using Selenium and save to CSV file
    """
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # List of genres to scrape from Letterboxd
    genres = ['action', 'drama', 'comedy', 'thriller']
    movie_data = []
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no browser UI)
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Initialize the driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # Loop through each genre
        for genre in genres:
            # URL for Letterboxd popular movies by genre
            url = f"https://letterboxd.com/films/genre/{genre}/size/small/"
            
            print(f"Scraping {genre} movies from Letterboxd...")
            driver.get(url)
            
            # Wait for the page to load completely
            time.sleep(3)
            
            # Get the page source after JavaScript has executed
            html_content = driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find movie containers (poster items)
            movie_containers = soup.find_all('li', class_='poster-container')

            print(f"Found {len(movie_containers)} movie containers for {genre}")

            
            # Limit to 10 movies per genre to avoid overloading
            for container in movie_containers[:10]:
                try:
                    # Find the film poster div inside the container
                    poster_div = container.find('div', class_='film-poster')
                    if not poster_div:
                        continue
                        
                    # Extract title from data attributes
                    title = poster_div.get('data-film-name', "Unknown")
                    
                    # Find the inner div with the frame that contains year info
                    frame_link = poster_div.find('a', class_='frame')
                    if not frame_link:
                        continue
                        
                    # Extract year from frame title (format: "Movie Title (YYYY)")
                    frame_title = frame_link.find('span', class_='frame-title')
                    year = "Unknown"
                    if frame_title and '(' in frame_title.text and ')' in frame_title.text:
                        year = frame_title.text.split('(')[-1].split(')')[0]
                    
                    # Get rating from data-original-title attribute (format: "Movie Title (YYYY) X.XX")
                    rating = 0.0
                    if frame_link.get('data-original-title'):
                        rating_text = frame_link.get('data-original-title')
                        if rating_text and rating_text.split(')')[-1].strip():
                            try:
                                rating = float(rating_text.split(')')[-1].strip())
                            except:
                                pass
                    
                    # Get image URL for poster
                    img_tag = poster_div.find('img')
                    image_url = img_tag.get('src') if img_tag else None
                    
                    # Get movie details page URL
                    film_link = poster_div.find('a')
                    if not film_link or not film_link.get('href'):
                        continue
                    
                    # ------ New scrape for more details -------

                    film_url = f"https://letterboxd.com{film_link.get('href')}"
                    
                    # Add a small delay to avoid rate limiting
                    time.sleep(random.uniform(1, 2))
                    
                    driver.get(film_url)
                    time.sleep(3)  # Wait for page to load
                    
                    film_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    
                    # Get description - look for the film summary
                    description_element = film_soup.find('div', class_='film-text-content')
                    description = "No description available"
                    if description_element:
                        p_element = description_element.find('p')
                        if p_element:
                            description = p_element.text.strip()
                    
                    # Get genre information - look for genres specifically
                    genre_elements = film_soup.select('div.text-sluglist.capitalize a[href*="/films/genre/"]')
                    film_genres = ", ".join([g.text for g in genre_elements]) if genre_elements else genre
                    
                    # Create images directory if it doesn't exist
                    os.makedirs('data/images', exist_ok=True)
                    
                    # Download image if URL exists
                    image_path = None
                    if image_url:
                        try:
                            import requests
                            from urllib.parse import urlparse
                            
                            # Create a safe filename from the movie title
                            safe_title = "".join([c if c.isalnum() else "_" for c in title])
                            image_filename = f"{safe_title}_{year}.jpg"
                            image_path = f"data/images/{image_filename}"
                            
                            # Download the image
                            img_response = requests.get(image_url, stream=True)
                            if img_response.status_code == 200:
                                with open(image_path, 'wb') as img_file:
                                    for chunk in img_response.iter_content(1024):
                                        img_file.write(chunk)
                                print(f"Downloaded image for {title}")
                            else:
                                image_path = None
                        except Exception as img_err:
                            print(f"Error downloading image: {img_err}")
                            image_path = None
                    
                    # Add to movie data list
                    movie_data.append({
                        'title': title,
                        'year': year,
                        'rating': rating,
                        'genre': film_genres,
                        'description': description,
                        'image_path': image_path
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
    
    except Exception as e:
        print(f"Error: {e}")
        # Create a sample dataset if scraping fails
        create_sample_dataset()
        return False
    
    finally:
        # Always close the driver
        driver.quit()

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