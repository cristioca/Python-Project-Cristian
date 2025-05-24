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

def scrape_movies(progress_callback=None):
    """
    Scrape basic movie data from Letterboxd main genre pages
    """
    try:
        # Create directories if they don't exist
        os.makedirs('static/images', exist_ok=True)
        
        if progress_callback:
            progress_callback(0.05, "Initializing Chrome driver")
        
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
        genres = ['action', 'drama', 'comedy', 'thriller', 'horror', 'romance', 'adventure', 'crime', 'sci-fi']
        movie_data = []
        
        # Loop through each genre
        for i, genre in enumerate(genres):
            if progress_callback:
                progress = 0.1 + (i / len(genres) * 0.7)  # Progress from 10% to 80%
                progress_callback(progress, f"Scraping {genre} movies...")
                
            url = f"https://letterboxd.com/films/genre/{genre}/size/small/"
            print(f"Scraping {genre} movies...")
            
            try:
                driver.get(url)
                time.sleep(2)
                
                # Get movie containers
                movie_containers = BeautifulSoup(driver.page_source, 'html.parser').find_all('li', class_='poster-container')
                print(f"Found {len(movie_containers)} movies for {genre}")
                
                # Process each movie (limit to 3 per genre)
                for j, container in enumerate(movie_containers[:3]):  # Adjust limit as needed
                    try:
                        if progress_callback:
                            sub_progress = progress + (j / 3) * (0.7 / len(genres))
                            progress_callback(sub_progress, f"Processing {genre} movie {j+1}/3")
                            
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
                
            except Exception as e:
                print(f"Error scraping genre {genre}: {e}")
                continue
        
        # Save data to CSV
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
        try:
            if 'driver' in locals():
                driver.quit()
        except:
            pass

def get_movie_description(movie_url):
    """Get movie description, cast and larger image from its details page"""
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
            driver.quit()
        except:
            pass

def quick_update_titles(progress_callback=None):
    """
    Quickly extract movie titles and genres from the current page without fetching detailed information
    """
    try:
        # Create directories if they don't exist
        os.makedirs('data', exist_ok=True)
        
        if progress_callback:
            progress_callback(0.05, "Initializing Chrome driver")
        
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
        genres = ['action', 'drama', 'comedy', 'thriller', 'horror', 'romance', 'adventure', 'crime', 'sci-fi']
        movie_data = []
        
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
        
        # Loop through each genre
        for i, genre in enumerate(genres):
            if progress_callback:
                progress = 0.15 + (i / len(genres) * 0.7)  # Progress from 15% to 85%
                progress_callback(progress, f"Scraping {genre} movies...")
                
            url = f"https://letterboxd.com/films/genre/{genre}/size/small/"
            print(f"Scraping {genre} movies (titles only)...")
            
            try:
                driver.get(url)
                time.sleep(2)
                
                # Get movie containers
                movie_containers = BeautifulSoup(driver.page_source, 'html.parser').find_all('li', class_='poster-container')
                print(f"Found {len(movie_containers)} movies for {genre}")
                
                # Process each movie (limit to 10 per genre for quick update)
                for j, container in enumerate(movie_containers[:10]):  # Adjust limit as needed
                    try:
                        if progress_callback:
                            sub_progress = progress + (j / 10) * (0.7 / len(genres))
                            progress_callback(sub_progress, f"Processing {genre} movie {j+1}/10")
                            
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
                        if movie_url in existing_movies:
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
                            'rating': rating,  # Use extracted rating
                            'genre': genre,
                            'description': "Details",  # Default description
                            'image_path': image_path,
                            'movie_url': movie_url
                        })
                        print(f"Quick scraped: {title} ({year})")
                        
                    except Exception as e:
                        print(f"Error processing movie: {e}")
                        continue
                
            except Exception as e:
                print(f"Error scraping genre {genre}: {e}")
                continue
        
        # Save data to CSV (append to existing or create new)
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
        try:
            if 'driver' in locals():
                driver.quit()
        except:
            pass

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