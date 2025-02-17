
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

def scrape_imdb_top():
    url = "https://www.imdb.com/chart/top/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        movies = []
        movie_elements = soup.select('td.titleColumn')
        rating_elements = soup.select('td.ratingColumn strong')
        
        for movie_elem, rating in zip(movie_elements, rating_elements):
            title = movie_elem.a.text
            year = movie_elem.span.text.strip('()')
            rating = float(rating.text)
            
            movies.append({
                "title": title,
                "year": year,
                "rating": rating
            })
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result = {
            "status": "success",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "url": url,
            "movies": movies
        }
        
        with open(f'imdb_results_{timestamp}.json', 'w') as f:
            json.dump(result, f, indent=2)
            
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "url": url,
            "error": str(e)
        }
