import requests
import json
from datetime import datetime


def test_scraper():
    BASE_URL = "http://localhost:8000"

    print(f"=== IMDB Scraper Test ===")
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

            # Save results
            filename = f"imdb_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\nFull results saved to: {filename}")

            # Print sample
            print("\nSample (First 3 movies):")
            for movie in result['items'][:3]:
                print(f"\nTitle: {movie['title']}")
                print(f"Year: {movie['publish_date']}")
                print(f"Content:\n{movie['content']}")
                print("-" * 50)

        else:
            print(f"\n✗ Scraping failed (Status: {response.status_code})")
            print(f"Error: {response.json().get('detail', 'Unknown error')}")

    except requests.exceptions.Timeout:
        print("\n✗ Request timed out")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")


if __name__ == "__main__":
    test_scraper()
