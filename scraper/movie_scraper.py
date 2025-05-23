from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import random
import requests

def scrape_movies():
    """
    Scrape basic movie data from Letterboxd main genre pages
    """
    try:
        # Create directories if they don't exist
        os.makedirs('static/images', exist_ok=True)
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Error initializing Chrome driver: {e}")
            return False
        
        # List of genres to scrape
        genres = ['action', 'drama', 'comedy', 'thriller']
        movie_data = []
        
        # Loop through each genre
        for genre in genres:
            url = f"https://letterboxd.com/films/genre/{genre}/size/small/"
            print(f"Scraping {genre} movies...")
            
            try:
                driver.get(url)
                time.sleep(2)
                
                # Get movie containers
                movie_containers = BeautifulSoup(driver.page_source, 'html.parser').find_all('li', class_='poster-container')
                print(f"Found {len(movie_containers)} movies for {genre}")
                
                # Process each movie (limit to 2 per genre)
                for container in movie_containers[:2]:
                    try:
                        # Extract basic movie info
                        poster_div = container.find('div', class_='film-poster')
                        if not poster_div:
                            continue
                            
                        title = poster_div.get('data-film-name', "Unknown")
                        
                        # Get year and rating
                        frame_link = poster_div.find('a', class_='frame')
                        if not frame_link:
                            continue
                            
                        year = "Unknown"
                        frame_title = frame_link.find('span', class_='frame-title')
                        if frame_title and '(' in frame_title.text and ')' in frame_title.text:
                            year = frame_title.text.split('(')[-1].split(')')[0]
                        
                        rating = 0.0
                        if frame_link.get('data-original-title'):
                            rating_text = frame_link.get('data-original-title')
                            if rating_text and rating_text.split(')')[-1].strip():
                                try:
                                    rating = float(rating_text.split(')')[-1].strip())
                                except:
                                    pass
                        
                        # Get image URL and movie URL
                        img_tag = poster_div.find('img')
                        image_url = img_tag.get('src') if img_tag else None
                        film_link = poster_div.find('a')
                        movie_url = film_link.get('href') if film_link else None
                        
                        # Download image
                        image_path = None
                        if image_url:
                            try:
                                safe_title = "".join([c if c.isalnum() else "_" for c in title])
                                image_filename = f"{safe_title}_{year}.jpg"
                                image_path = f"images/{image_filename}"
                                full_path = os.path.join('static', image_path)
                                
                                response = requests.get(image_url, stream=True)
                                if response.status_code == 200:
                                    with open(full_path, 'wb') as img_file:
                                        for chunk in response.iter_content(1024):
                                            img_file.write(chunk)
                                    print(f"Downloaded image for {title}")
                            except Exception as img_err:
                                print(f"Error downloading image: {img_err}")
                                image_path = None
                        
                        # Add movie data
                        movie_data.append({
                            'title': title,
                            'year': year,
                            'rating': rating,
                            'genre': genre,
                            'description': "Click for description",
                            'image_path': image_path,
                            'movie_url': movie_url
                        })
                        print(f"Scraped: {title} ({year})")
                        
                    except Exception as e:
                        print(f"Error processing movie: {e}")
                        continue
                
            except Exception as e:
                print(f"Error scraping genre {genre}: {e}")
                continue
        
        # Save data to CSV
        if movie_data:
            df = pd.DataFrame(movie_data)
            df.to_csv('data/movies.csv', index=False)
            print(f"Successfully scraped {len(df)} movies")
            return True
        else:
            print("No movie data collected")
            create_sample_dataset()
            return False
            
    except Exception as e:
        print(f"Scraping error: {e}")
        create_sample_dataset()
        return False
        
    finally:
        try:
            if 'driver' in locals():
                driver.quit()
        except:
            pass

def get_movie_description(movie_url):
    """Get movie description from its details page"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=chrome_options)
        
        url = f"https://letterboxd.com{movie_url}"
        driver.get(url)
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        desc_element = soup.find('div', class_='film-text-content')
        if desc_element and desc_element.find('p'):
            return desc_element.find('p').text.strip()
        return "No description available"
        
    except Exception as e:
        print(f"Error getting description: {e}")
        return "Error loading description"
        
    finally:
        try:
            driver.quit()
        except:
            pass

def create_sample_dataset():
    """Create a sample dataset if web scraping fails"""
    sample_data = [
        {'title': 'The Shawshank Redemption', 'year': '1994', 'rating': 9.3, 'genre': 'Drama', 
         'description': 'Click for description', 'image_path': None, 'movie_url': '/film/the-shawshank-redemption/'},
        {'title': 'The Godfather', 'year': '1972', 'rating': 9.2, 'genre': 'Crime, Drama', 
         'description': 'Click for description', 'image_path': None, 'movie_url': '/film/the-godfather/'}
    ]
    df = pd.DataFrame(sample_data)
    df.to_csv('data/movies.csv', index=False)
    print("Created sample dataset")