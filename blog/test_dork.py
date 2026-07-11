from ddgs import DDGS

def dork_blog_scout(domain, user_query, max_results=3):

    dork_query = f"site:{domain} {user_query}"
    
    
    try:
        # 2. Execute the search
        with DDGS() as ddgs:
            results = list(ddgs.text(dork_query, max_results=max_results))
            
            if not results:
                print(f"No articles found on {domain} for that query.")
                return

            print(f"Found {len(results)} highly targeted links!\n")
            print("=" * 70)
            
            # 3. Output the results for the Extractor Agent
            for index, result in enumerate(results, start=1):
                title = result.get('title', 'No Title')
                link = result.get('href', 'No Link')
                snippet = result.get('body', 'No Snippet')
                
                print(f"📰 Post {index}: {title}")
                print(f"🔗 Link: {link}")
                print(f"📝 Snippet: {snippet}...")
                print("-" * 70)
                
    except Exception as e:
        print(f"Search failed. Anti-bot protection might have blocked the request. Error: {e}")

if __name__ == "__main__":

    TARGET_DOMAIN = "scrapfly.io/blog" 
    
    USER_PROMPT = "residential proxies bypass cloudflare"
    
    dork_blog_scout(TARGET_DOMAIN, USER_PROMPT)