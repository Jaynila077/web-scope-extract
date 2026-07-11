from feedsearch_crawler import search

def hidden_feed_scout(domain):

    feeds = search(domain)
    
    if not feeds:
        print(f"No syndication feeds (RSS/Atom/JSON) found for {domain}.")
        return

    print(f"Success! Discovered {len(feeds)} active feeds.\n")
    print("=" * 70)
    
    for index, feed in enumerate(feeds, start=1):
        # The library returns rich metadata about the feed itself
        # We use standard string conversion for the URL object
        feed_url = str(feed.url)
        title = feed.title if feed.title else "Untitled Feed"
        content_type = feed.content_type if feed.content_type else "Unknown Format"
        
        print(f"Feed {index}: {title}")
        print(f"URL: {feed_url}")
        print(f"Format: {content_type}")
        print("-" * 70)

if __name__ == "__main__":
    TARGET_DOMAIN = "propublica.org" 
    
    hidden_feed_scout(TARGET_DOMAIN)