import feedparser
from newspaper import Article
import asyncio
from redis_client import redis_client
import json

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.xml",
    "https://feeds.feedburner.com/NDTV-LatestNews.xml",
    
]

async def fetch_article(url: str):
    """Download and parse a single article using a thread to avoid blocking."""
    try:
        def download_parse():
            article = Article(url)
            article.download()
            article.parse()
            return article

        article = await asyncio.to_thread(download_parse)

        if article.title and article.text:
            return {
                "title": article.title,
                "text": article.text,
                "url": url
            }
    except Exception as e:
        print(f" Failed to fetch {url}: {e}")
    return None

async def fetch_news_from_rss(max_articles_per_feed: int = 12):
    """Fetch news and store in Redis cache."""
    
    # Check cache first
    cached_articles = redis_client.get("news")
    if cached_articles:
        print(f"Returning {len(json.loads(cached_articles))} cached articles from Redis")
        return json.loads(cached_articles)
    
    tasks = []
    for rss_url in RSS_FEEDS:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:max_articles_per_feed]:
            tasks.append(fetch_article(entry.link))

    # Run all fetches concurrently
    results = await asyncio.gather(*tasks)
    articles = [a for a in results if a]

    # Cache results in Redis
    if articles:
        redis_client.set("news", json.dumps(articles), ex=1800)
        print(f"✅ Fetched and cached {len(articles)} articles in Redis")
    
    return articles
