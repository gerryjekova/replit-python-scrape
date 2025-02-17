from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from datetime import datetime
import pytz
import redis
import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict


# Models
class AnimeEntry(BaseModel):
    rank: int
    title: str
    type: str
    episodes: str
    members: str
    score: float
    aired: str


class ScrapeRequest(BaseModel):
    url: HttpUrl
    max_pages: Optional[int] = 1


class ScrapeResponse(BaseModel):
    status: str
    timestamp: str
    user: str
    url: str
    anime_list: List[AnimeEntry]


# Initialize FastAPI
from fastapi import FastAPI
from app.scrapers.imdb_scraper import scrape_imdb_top

app = FastAPI()

@app.get("/scrape/imdb/top")
async def scrape_imdb():
    return scrape_imdb_top()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis
redis_client = redis.Redis(host='localhost',
                           port=6379,
                           db=0,
                           decode_responses=True)


def scrape_mal_page(url: str) -> List[AnimeEntry]:
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        anime_list = []
        anime_rows = soup.select('tr.ranking-list')

        for row in anime_rows:
            try:
                rank = int(row.select_one('.rank span').text)
                title = row.select_one('.title a').text.strip()

                info = row.select_one('.information').text.strip()
                type_eps = info.split('(')[1].split(
                    ')')[0] if '(' in info else "Unknown"

                if 'TV' in type_eps:
                    anime_type = 'TV'
                    episodes = type_eps.replace('TV', '').strip()
                elif 'Movie' in type_eps:
                    anime_type = 'Movie'
                    episodes = '1'
                else:
                    anime_type = type_eps.split()[0]
                    episodes = type_eps.split()[-1]

                members = row.select_one('.members').text.strip().replace(
                    'members', '').strip()
                score = float(row.select_one('.score').text.strip())

                aired = "Ongoing" if "?" in episodes else "Completed"

                anime_list.append(
                    AnimeEntry(rank=rank,
                               title=title,
                               type=anime_type,
                               episodes=episodes,
                               members=members,
                               score=score,
                               aired=aired))
            except Exception as e:
                print(f"Error parsing anime entry: {str(e)}")
                continue

        return anime_list

    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Failed to scrape MAL: {str(e)}")


@app.get("/")
async def root():
    return {
        "message": "Welcome to the Web Scraper API",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    current_time = datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")
    try:
        redis_client.ping()
        redis_status = "connected"
    except:
        redis_status = "disconnected"

    return {
        "status": "healthy",
        "user": "gerryjekova",
        "redis": redis_status,
        "timestamp": current_time
    }


@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_url(request: ScrapeRequest):
    try:
        current_time = datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")

        # Scrape the page
        anime_list = scrape_mal_page(str(request.url))

        # Create response
        response = ScrapeResponse(status="success",
                                  timestamp=current_time,
                                  user="gerryjekova",
                                  url=str(request.url),
                                  anime_list=anime_list)

        # Store in Redis
        task_id = f"task_{datetime.now().timestamp()}"
        redis_client.setex(
            task_id,
            3600,  # 1 hour expiration
            response.json())

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True, workers=1)