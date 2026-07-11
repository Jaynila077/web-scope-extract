from ddgs import DDGS

def active_news_hunter(query, max_results=3):
    print(f" Hunting the web for: '{query}'...\n")
    
    # Initialize the DuckDuckGo Search tool
    with DDGS() as ddgs:
        # We use .text() for general web search, but you can also try .news()
        results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            print("No articles found for this query.")
            return

        print(f"Found {len(results)} targeted results. Extracting data...\n")
        print("-" * 50)

        # Loop through and print the search data
        for index, article in enumerate(results, start=1):
            title = article.get('title', 'No Title')
            link = article.get('href', 'No Link')
            snippet = article.get('body', 'No Snippet')

            print(f"Result {index}: {title}")
            print(f"Link: {link}")
            print(f"Snippet: {snippet}...")
            print("-" * 50)

if __name__ == "__main__":
  
    USER_QUERY = "Microsoft cuts jobs and shrinks Xbox restructure 2026"
    
    active_news_hunter(USER_QUERY)