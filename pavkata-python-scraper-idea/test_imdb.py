import requests
import json
from datetime import datetime
import pytz


def test_imdb_scraper():
    BASE_URL = "http://localhost:8000"
    CURRENT_USER = "gerryjekova"
    current_time = datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")

    print(f"=== IMDB Top Movies Scraper Test ===")
    print(f"Current Time (UTC): {current_time}")
    print(f"Current User: {CURRENT_USER}")
    print(f"Testing API at: {BASE_URL}\n")

    # Test health endpoint
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        print("Health Check Response:")
        print(json.dumps(health_response.json(), indent=2))
        print("\n" + "=" * 50 + "\n")
    except requests.exceptions.ConnectionError:
        print("Error: API is not running. Please start the API first.")
        return

    # Test IMDB scraping
    try:
        print("Testing IMDB Scraping...")
        response = requests.post(f"{BASE_URL}/scrape",
                                 json={
                                     "url": "https://www.imdb.com/chart/top/",
                                     "max_pages": 1
                                 },
                                 timeout=30)

        if response.status_code == 200:
            result = response.json()
            print("\n✓ Scraping successful!")
            print(f"Status: {result['status']}")
            print(f"Timestamp: {result['timestamp']}")
            print(f"User: {result['user']}")
            print(f"\nTop 10 Movies:")

            for movie in result['items'][:10]:
                print(f"\nTitle: {movie['title']}")
                print(f"Author (Director): {movie['author']}")
                print(f"Year: {movie['publish_date']}")
                print(f"Content:\n{movie['content']}")
                print(f"Media:\n  Poster: {movie['media_files']['images']}")
                print(f"  Movie Page: {movie['media_files']['embeds']}")
                print("-" * 50)

            # Save results to file
            filename = f"imdb_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nFull results saved to: {filename}")

        else:
            print(f"\n✗ Scraping failed (Status: {response.status_code})")
            print(f"Error: {response.json().get('detail', 'Unknown error')}")

    except requests.exceptions.Timeout:
        print("\n✗ Request timed out")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")


if __name__ == "__main__":
    test_imdb_scraper()
