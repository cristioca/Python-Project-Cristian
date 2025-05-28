# Letterboxd Movie Recommendation Bot

A Flask-based web application that recommends movies based on genres, using data scraped from Letterboxd. This project demonstrates web scraping, data processing, and web application development using Python.

## Features

- **Web Scraping**: Scrapes movie data from Letterboxd using Beautiful Soup
- **Data Processing**: Uses Pandas for efficient data manipulation and storage
- **User-friendly Interface**: Clean web interface with responsive design
- **Background Processing**: Handles long-running tasks in background threads
- **Progress Tracking**: Real-time progress updates for data operations
- **Search & Filter**: Find movies by title, description, year, and rating
- **Random Recommendations**: Get random movie suggestions within a genre or from all genres
- **Movie Details**: View movie descriptions and images fetched dynamically

## Technical Implementation

- **Web Framework**: Flask for the backend server
- **Data Storage**: CSV files for persistent storage
- **Scraping Library**: Beautiful Soup for HTML parsing
- **Data Analysis**: Pandas for data manipulation
- **Concurrency**: Threading for background operations
- **Error Handling**: Exception handling for robustness

## Project Structure

```
Python-Project-Cristian/
├── README.md               # Project documentation
├── requirements.txt        # Dependencies
├── app.py                  # Main Flask application
├── scraper/                # Scraping module
│   ├── __init__.py
│   └── movie_scraper.py    # BS4 scraping code
├── data/                   # Data storage
│   └── movies.csv          # Scraped movie data
├── static/                 # Static assets
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── images/             # Movie images
└── templates/              # HTML templates
    ├── index.html          # Home page
    ├── results.html        # Recommendation results
    ├── search_results.html # Search results
    └── progress.html       # Progress tracking
```

## How to Run

### Prerequisites
- Python 3.7+
- pip (Python package installer)

### Installation on Windows

1. Clone this repository
   ```
   git clone https://github.com/yourusername/Python-Project-Cristian.git
   cd Python-Project-Cristian
   ```

2. Install dependencies
   ```
   pip install -r requirements.txt
   ```

3. Run the application
   ```
   python app.py
   ```

4. Open your browser and go to http://localhost:5000

### Running on Linux

1. Make sure you have Python 3.7+ installed:
   ```
   sudo apt update
   sudo apt install python3 python3-pip
   ```

2. Clone the repository and navigate to the project directory:
   ```
   git clone https://github.com/yourusername/Python-Project-Cristian.git
   cd Python-Project-Cristian
   ```

3. Create a virtual environment (recommended):
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Run the application:
   ```
   python3 app.py
   ```

6. Access the application by opening a browser and navigating to:
   ```
   http://localhost:5000
   ```

7. To run the application in the background:
   ```
   nohup python3 app.py &
   ```

## Usage

1. **Home Page**: Select a genre from the dropdown menu
2. **List Top Movies**: Click "List Top Movies" to see top-rated movies in one genre or any genres
3. **Random Pick**: Toggle "Random Pick" to get a random movie suggestion from one genre or any genres
4. **Search**: Use the search bar to find movies by title or description / actor
5. **Filter**: Apply filters for year range and minimum rating
6. **Movie Details**: Click on a movie to see its full description, cast and larger image

## Implementation Details

- **Data Collection**: The application can scrape movie data from Letterboxd, storing titles, ratings, genres, descriptions and URLs
- **Error Handling**: Comprehensive error handling ensures the application remains stable
- **Background Processing**: Long-running operations like database updates run in background threads
- **Progress Tracking**: Real-time progress updates for operations like database updates
- **Safe File Handling**: Ensures filenames are safe for all operating systems
- **Responsive Design**: Works on both desktop and mobile browsers

## License

This project is created as part of the RBS Tech Training Python Course.

## Author

Cristian Olariu