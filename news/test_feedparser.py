import feedparser
from datetime import datetime

def monitor_rss_feed(feed_url, max_articles=5):
    print(f"Scanning RSS Feed: {feed_url}...\n")
    

    feed = feedparser.parse(feed_url)
    
    if feed.bozo:
        print("Error: Could not parse the feed. Check the URL.")
        return

    articles = feed.entries[:max_articles]
    
    if not articles:
        print("No articles found in this feed.")
        return

    print(f"Found {len(articles)} recent articles. Extracting data...\n")
    print("-" * 50)


    for index, article in enumerate(articles, start=1):
      
        title = article.get('title', 'No Title')
        link = article.get('link', 'No Link')
     
        published = article.get('published', 'Unknown Time')

        print(f"Article {index}: {title}")
        print(f"Published: {published}")
        print(f"Link: {link}")
        print("-" * 50)

if __name__ == "__main__":

    TARGET_FEED = "http://feeds.bbci.co.uk/news/technology/rss.xml"
    
    # Run the function
    monitor_rss_feed(TARGET_FEED)