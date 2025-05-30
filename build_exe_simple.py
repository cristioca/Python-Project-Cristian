import PyInstaller.__main__
import os
import shutil

# Create a temporary directory for the build
if os.path.exists('build_temp'):
    shutil.rmtree('build_temp')
os.makedirs('build_temp', exist_ok=True)

# Ensure data directory exists with a sample CSV
os.makedirs('data', exist_ok=True)
if not os.path.exists('data/movies.csv'):
    with open('data/movies.csv', 'w') as f:
        f.write('title,year,rating,genre,description,image_path,movie_url\n')
        f.write('Sample Movie,2023,4.5,Drama,Details,None,/film/sample-movie/\n')

# Define PyInstaller arguments
args = [
    'app.py',                          # Use app.py directly
    '--onefile',                       # Create a single executable
    '--name=MoviePickerBot',           # Name of the executable
    '--add-data=templates;templates',  # Include templates folder
    '--add-data=static;static',        # Include static folder
    '--add-data=data;data',            # Include data folder
    '--add-data=scraper;scraper',      # Include scraper folder
    '--hidden-import=selenium',        # Include hidden imports
    '--hidden-import=bs4',
    '--hidden-import=pandas',
    '--hidden-import=flask',
    '--hidden-import=requests',
    '--hidden-import=webbrowser',
    '--console',                       # Show console window for debugging
    '--clean',                         # Clean PyInstaller cache
    '--workpath=build_temp',           # Temporary build directory
    '--distpath=dist',                 # Output directory
]

# Run PyInstaller
PyInstaller.__main__.run(args)

# Clean up temporary build directory
if os.path.exists('build_temp'):
    shutil.rmtree('build_temp')

print("Build complete! Executable is in the 'dist' folder.")