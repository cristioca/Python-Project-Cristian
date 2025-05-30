from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import random
import requests
from pathlib import Path
import concurrent.futures
import threading

# Thread-local storage for browser instances
thread_local = threading.local()

def get_driver():
    """Get a thread-local Chrome driver instance"""
    if not hasattr(thread_local, "driver"):
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        thread_local.driver = webdriver.Chrome(options=chrome_options)
    return thread_local.driver

def close_drivers():
    """Close all thread-local drivers"""
    if hasattr(thread_local, "driver"):
        try:
            thread_local.driver.quit()
        except:
            pass

def scrape_genre(genre, max_movies=3, progress_callback=None, progress_start=0, progress_range=0.1, should_stop=None):
    """Scrape movies for a specific genre"""
    try:
        driver = get_driver()
        url = f"https://letterboxd.com/films/genre/{genre}/size/small/"
        print(f"Scraping {genre} movies...")
        
        # Check if we should stop
        if should_stop and should_stop():
            print(f"Stopping scrape for genre {genre}")
            return []
            
        driver.get(url)
        time.sleep(2)
        
        # Get movie containers
        movie_containers = BeautifulSoup(driver.page_source, 'html.parser').find_all('li', class_='poster-container')
        print(f"Found {len(movie_containers)} movies for {genre}")
        
        movie_data = []
        
        # Process each movie (limit to max_movies per genre)
        for j, container in enumerate(movie_containers[:max_movies]):
            try:
                # Check if we should stop
                if should_stop and should_stop():
                    print(f"Stopping scrape for genre {genre} at movie {j+1}")
                    break
                    
                if progress_callback:
                    sub_progress = progress_start + (j / max_movies) * progress_range
                    progress_callback(sub_progress, f"Processing {genre} movie {j+1}/{max_movies}")
                    
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
                    'description': "Details",
                    'image_path': image_path,
                    'movie_url': movie_url
                })
                print(f"Scraped: {title} ({year})")
                
            except Exception as e:
                print(f"Error processing movie: {e}")
                continue
                
        return movie_data
        
    except Exception as e:
        print(f"Error scraping genre {genre}: {e}")
        return []

def scrape_movies(progress_callback=None, should_stop=None):
    """
    Scrape basic movie data from Letterboxd main genre pages using multithreading
    """
    try:
        # Create directories if they don't exist
        os.makedirs('static/images', exist_ok=True)
        
        if progress_callback:
            progress_callback(0.05, "Initializing scraper")
        
        # List of genres to scrape
        genres = ['action', 'drama', 'comedy', 'thriller', 'horror', 'romance', 'adventure', 'crime', 'sci-fi',
                 'animation', 'family', 'fantasy', 'history', 'mystery', 'science-fiction', 'war', 'western']
        movie_data = []
        
        # Calculate progress segments
        progress_per_genre = 0.8 / len(genres)
        
        # Use ThreadPoolExecutor for parallel scraping
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Create a dictionary to track futures
            future_to_genre = {}
            
            # Submit scraping tasks for each genre
            for i, genre in enumerate(genres):
                # Check if we should stop before submitting more tasks
                if should_stop and should_stop():
                    print("Stopping before submitting more genres")
                    break
                    
                progress_start = 0.1 + (i * progress_per_genre)
                future = executor.submit(
                    scrape_genre, 
                    genre, 
                    max_movies=3,  # Adjust limit as needed
                    progress_callback=progress_callback,
                    progress_start=progress_start,
                    progress_range=progress_per_genre,
                    should_stop=should_stop
                )
                future_to_genre[future] = genre
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_genre):
                genre = future_to_genre[future]
                try:
                    # Check if we should stop before processing more results
                    if should_stop and should_stop():
                        print("Stopping before processing more results")
                        break
                        
                    genre_data = future.result()
                    movie_data.extend(genre_data)
                    print(f"Completed scraping {genre} with {len(genre_data)} movies")
                except Exception as e:
                    print(f"Error in genre {genre}: {e}")
        
        # Check if we should stop before saving data
        if should_stop and should_stop():
            print("Update stopped. No data will be written to CSV.")
            if progress_callback:
                progress_callback(1.0, "Update stopped. No changes made.")
            return False
            
        # Save data to CSV only if not stopped
        if progress_callback:
            progress_callback(0.9, "Saving data to CSV")
            
        if movie_data:
            df = pd.DataFrame(movie_data)
            df.to_csv('data/movies.csv', index=False)
            print(f"Successfully scraped {len(df)} movies")
            
            if progress_callback:
                progress_callback(1.0, f"Successfully scraped {len(df)} movies")
                
            return True
        else:
            print("No movie data collected")
            create_sample_dataset()
            
            if progress_callback:
                progress_callback(1.0, "Created sample dataset")
                
            return False
            
    except Exception as e:
        print(f"Scraping error: {e}")
        create_sample_dataset()
        
        if progress_callback:
            progress_callback(1.0, f"Error: {str(e)}")
            
        return False
        
    finally:
        close_drivers()

def get_movie_description(movie_url):
    """Get movie description, cast and larger image from its details page"""
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)
        
        url = f"https://letterboxd.com{movie_url}"
        print(f"Fetching URL: {url}")
        driver.get(url)
        time.sleep(3)  # Increase wait time
        
        # Save the page source for debugging
        with open('data/action_full_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Get description - combine tagline and synopsis
        tagline = ""
        synopsis = ""
        
        # Try to find the tagline
        tagline_element = soup.find('h4', class_='tagline')
        if tagline_element and tagline_element.text.strip():
            tagline = tagline_element.text.strip()
        
        # Try to find the synopsis in the truncate div
        truncate_element = soup.find('div', class_='truncate')
        if truncate_element:
            p_tag = truncate_element.find('p')
            if p_tag:
                synopsis = p_tag.text.strip()
        
        # If no synopsis yet, try film-text-content
        if not synopsis:
            desc_element = soup.find('div', class_='film-text-content')
            if desc_element:
                p_tag = desc_element.find('p')
                if p_tag:
                    synopsis = p_tag.text.strip()
        
        # If still no synopsis, try review body text
        if not synopsis:
            desc_element = soup.find('div', class_='review body-text -prose -hero prettify')
            if desc_element:
                p_tag = desc_element.find('p')
                if p_tag:
                    synopsis = p_tag.text.strip()
        
        # Extract cast information
        cast_names = []
        cast_element = soup.find('div', class_='cast-list text-sluglist')
        if cast_element:
            cast_links = cast_element.find_all('a', class_='text-slug')
            for link in cast_links:
                if 'show-cast-overflow' not in link.get('id', ''):  # Skip the "Show All" link
                    cast_names.append(link.text.strip())
        
        # Combine tagline, synopsis and cast with HTML formatting
        if tagline and synopsis:
            description = f"<strong>{tagline}</strong><br>{synopsis}"
        elif tagline:
            description = f"<strong>{tagline}</strong>"
        elif synopsis:
            description = synopsis
        else:
            description = "No description available"
            
        # Add cast if available
        if cast_names:
            description += f"<br><br><strong>Cast:</strong> {', '.join(cast_names)}"
        
        # Get larger image - try multiple selectors
        image_url = None
        
        # Try poster image first
        poster_element = soup.find('img', class_='image')
        if poster_element:
            image_url = poster_element.get('src')
        
        # Try other image locations
        if not image_url:
            image_element = soup.find('img', class_='poster-img')
            if image_element:
                image_url = image_element.get('src')
        
        if not image_url:
            image_element = soup.find('div', class_='film-poster')
            if image_element:
                img_tag = image_element.find('img')
                if img_tag:
                    image_url = img_tag.get('src')
        
        print(f"Found description: {description[:50]}...")
        print(f"Found image URL: {image_url}")
        
        return {
            'description': description,
            'large_image_url': image_url,
            'letterboxd_url': url
        }
        
    except Exception as e:
        print(f"Error getting movie details: {e}")
        return {
            'description': "Error loading description",
            'large_image_url': None
        }
        
    finally:
        try:
            if driver:
                driver.quit()
        except Exception as e:
            print(f"Error closing driver: {e}")

def process_genre_quick(genre, max_movies=10, existing_movies=None, progress_callback=None, progress_start=0, progress_range=0.1, should_stop=None):
    """Process a single genre for quick update"""
    try:
        driver = get_driver()
        url = f"https://letterboxd.com/films/genre/{genre}/size/small/"
        print(f"Scraping {genre} movies (titles only)...")
        
        # Check if we should stop
        if should_stop and should_stop():
            print(f"Stopping quick update for genre {genre}")
            return []
        
        # Add rate limiting delay (1-3 seconds) before each page request
        delay = 1 + 2 * random.random()  # Random delay between 1-3 seconds
        time.sleep(delay)
            
        driver.get(url)
        time.sleep(2)
        
        # Get movie containers
        movie_containers = BeautifulSoup(driver.page_source, 'html.parser').find_all('li', class_='poster-container')
        print(f"Found {len(movie_containers)} movies for {genre}")
        
        movie_data = []
        
        # Process each movie (limit to max_movies per genre)
        for j, container in enumerate(movie_containers[:max_movies]):
            try:
                # Check if we should stop
                if should_stop and should_stop():
                    print(f"Stopping quick update for genre {genre} at movie {j+1}")
                    break
                    
                if progress_callback:
                    sub_progress = progress_start + (j / max_movies) * progress_range
                    progress_callback(sub_progress, f"Processing {genre} movie {j+1}/{max_movies}")
                    
                # Extract basic movie info
                poster_div = container.find('div', class_='film-poster')
                if not poster_div:
                    continue
                    
                title = poster_div.get('data-film-name', "Unknown")
                
                # Get year, rating and movie URL
                frame_link = poster_div.find('a', class_='frame')
                if not frame_link:
                    continue
                    
                year = "Unknown"
                frame_title = frame_link.find('span', class_='frame-title')
                if frame_title and '(' in frame_title.text and ')' in frame_title.text:
                    year = frame_title.text.split('(')[-1].split(')')[0]
                
                # Extract rating from data-original-title attribute
                rating = 0.0
                if frame_link.get('data-original-title'):
                    rating_text = frame_link.get('data-original-title')
                    if rating_text and rating_text.split(')')[-1].strip():
                        try:
                            rating = float(rating_text.split(')')[-1].strip())
                        except:
                            pass
                
                # Get movie URL
                film_link = poster_div.find('a')
                movie_url = film_link.get('href') if film_link else None
                
                # Skip if movie already exists in database
                if existing_movies and movie_url in existing_movies:
                    print(f"Skipping existing movie: {title}")
                    continue
                
                # Get image URL
                img_tag = poster_div.find('img')
                image_url = img_tag.get('src') if img_tag else None
                
                # Download image (small version only)
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
                
                # Add movie data with minimal information
                movie_data.append({
                    'title': title,
                    'year': year,
                    'rating': rating,
                    'genre': genre,
                    'description': "Details",  # Default description
                    'image_path': image_path,
                    'movie_url': movie_url
                })
                print(f"Quick scraped: {title} ({year})")
                
            except Exception as e:
                print(f"Error processing movie: {e}")
                continue
                
        return movie_data
        
    except Exception as e:
        print(f"Error scraping genre {genre}: {e}")
        return []

def quick_update_titles(progress_callback=None, should_stop=None):
    """
    Quickly extract movie titles and genres using multithreading
    """
    try:
        # Create directories if they don't exist
        os.makedirs('data', exist_ok=True)
        
        if progress_callback:
            progress_callback(0.05, "Initializing Chrome driver")
        
        # List of genres to scrape
        genres = ['action', 'drama', 'comedy', 'thriller', 'horror', 'romance', 'adventure', 'crime', 'sci-fi',
                 'animation', 'family', 'fantasy', 'history', 'mystery', 'science-fiction', 'war', 'western']
        
        # Check if existing data file exists and load it
        data_file = Path('data/movies.csv')
        existing_movies = set()
        
        if progress_callback:
            progress_callback(0.1, "Checking existing database")
            
        if data_file.exists():
            try:
                existing_df = pd.read_csv(data_file)
                # Create a set of movie URLs for quick lookup
                if 'movie_url' in existing_df.columns:
                    existing_movies = set(existing_df['movie_url'].dropna())
                    print(f"Found {len(existing_movies)} existing movies in database")
            except Exception as e:
                print(f"Error reading existing data: {e}")
        
        # Calculate progress segments
        progress_per_genre = 0.7 / len(genres)
        movie_data = []
        
        # Use ThreadPoolExecutor for parallel scraping
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # Create a dictionary to track futures
            future_to_genre = {}
            
            # Submit scraping tasks for each genre
            for i, genre in enumerate(genres):
                # Check if we should stop before submitting more tasks
                if should_stop and should_stop():
                    print("Stopping before submitting more genres for quick update")
                    break
                    
                progress_start = 0.15 + (i * progress_per_genre)
                future = executor.submit(
                    process_genre_quick, 
                    genre, 
                    max_movies=10,  # Adjust limit as needed
                    existing_movies=existing_movies,
                    progress_callback=progress_callback,
                    progress_start=progress_start,
                    progress_range=progress_per_genre,
                    should_stop=should_stop
                )
                future_to_genre[future] = genre
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_genre):
                genre = future_to_genre[future]
                try:
                    # Check if we should stop before processing more results
                    if should_stop and should_stop():
                        print("Stopping before processing more results for quick update")
                        break
                        
                    genre_data = future.result()
                    movie_data.extend(genre_data)
                    print(f"Completed quick scraping {genre} with {len(genre_data)} movies")
                except Exception as e:
                    print(f"Error in genre {genre}: {e}")
        
        # Check if we should stop before saving data
        if should_stop and should_stop():
            print("Quick update stopped. No data will be written to CSV.")
            if progress_callback:
                progress_callback(1.0, "Update stopped. No changes made.")
            return False
            
        # Save data to CSV (append to existing or create new) only if not stopped
        if progress_callback:
            progress_callback(0.9, "Saving data to database")
            
        if movie_data:
            new_df = pd.DataFrame(movie_data)
            
            if data_file.exists():
                # Append to existing data, avoiding duplicates
                existing_df = pd.read_csv(data_file)
                combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['movie_url'], keep='first')
                combined_df.to_csv(data_file, index=False)
                print(f"Successfully added {len(new_df)} new movies to database (total: {len(combined_df)})")
                
                if progress_callback:
                    progress_callback(1.0, f"Added {len(new_df)} new movies (total: {len(combined_df)})")
            else:
                # Create new file
                new_df.to_csv(data_file, index=False)
                print(f"Successfully scraped {len(new_df)} movies")
                
                if progress_callback:
                    progress_callback(1.0, f"Created database with {len(new_df)} movies")
            
            return True
        else:
            print("No new movie data collected")
            
            if progress_callback:
                progress_callback(1.0, "No new movies found")
                
            return False
            
    except Exception as e:
        print(f"Quick scraping error: {e}")
        
        if progress_callback:
            progress_callback(1.0, f"Error: {str(e)}")
            
        return False
        
    finally:
        close_drivers()

def create_sample_dataset():
    """Create a sample dataset if web scraping fails"""
    sample_data = [
        {'title': 'The Shawshank Redemption', 'year': '1994', 'rating': 9.3, 'genre': 'Drama', 
         'description': 'Details', 'image_path': None, 'movie_url': '/film/the-shawshank-redemption/'},
        {'title': 'The Godfather', 'year': '1972', 'rating': 9.2, 'genre': 'Crime, Drama', 
         'description': 'Details', 'image_path': None, 'movie_url': '/film/the-godfather/'}
    ]
    df = pd.DataFrame(sample_data)
    df.to_csv('data/movies.csv', index=False)
    print("Created sample dataset")