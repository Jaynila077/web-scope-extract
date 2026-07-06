import feedparser
from datetime import datetime

def monitor_rss_feed(feed_url, max_articles=5):
    print(f"Scanning RSS Feed: {feed_url}...\n")
    
    # Parse the live feed
    feed = feedparser.parse(feed_url)
    
    # Check if the feed is valid
    if feed.bozo:
        print("Error: Could not parse the feed. Check the URL.")
        return

    # Extract the top articles
    articles = feed.entries[:max_articles]
    
    if not articles:
        print("No articles found in this feed.")
        return

    print(f"Found {len(articles)} recent articles. Extracting data...\n")
    print("-" * 50)

    # Loop through and print the clean data
    for index, article in enumerate(articles, start=1):
        # Extract metadata safely (using .get in case a field is missing)
        title = article.get('title', 'No Title')
        link = article.get('link', 'No Link')
        
        # Published dates can be formatted weirdly, we just grab the raw string for now
        published = article.get('published', 'Unknown Time')

        print(f"Article {index}: {title}")
        print(f"Published: {published}")
        print(f"Link: {link}")
        print("-" * 50)

if __name__ == "__main__":
    # Target: BBC News - Technology
    TARGET_FEED = "http://feeds.bbci.co.uk/news/technology/rss.xml"
    
    # Run the function
    monitor_rss_feed(TARGET_FEED)