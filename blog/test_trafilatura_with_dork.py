from ddgs import DDGS
import trafilatura
import time

def integrated_research_pipeline(domain, user_query, max_links=2):

    dork_query = f"site:{domain} {user_query}"
    
    print(f"[SCOUT] Target Domain: {domain}")
    print(f"[SCOUT] User Query: '{user_query}'")
    print(f"[SCOUT] Hunting with Dork: '{dork_query}'...\n")
    
    try:
        with DDGS() as ddgs:
            search_results = list(ddgs.text(dork_query, max_results=max_links))
            
        if not search_results:
            print(f"No articles found on {domain} for that query.")
            return

        print(f"Found {len(search_results)} highly targeted links. Handing off to Extractor...\n")
        print("=" * 70)
        
        
        for index, result in enumerate(search_results, start=1):
            url = result.get('href')
            title = result.get('title', 'No Title')
            
            print(f"[EXTRACTOR] Processing Link {index}/{max_links}: {title}")
            print(f" URL: {url}")
            
            
            downloaded_html = trafilatura.fetch_url(url)
            
            if not downloaded_html:
                print(f"Failed to download {url}. (It might be blocking scrapers.)\n")
                continue
                
            
            clean_markdown = trafilatura.extract(
                downloaded_html,
                output_format="markdown",
                include_comments=False,
                include_links=False 
            )
            
            if not clean_markdown:
                print(f"Could not extract structural text body from {url}.\n")
                continue
                
            print(f"Success! Extracted {len(clean_markdown)} characters.")
            print(f"TEXT PREVIEW:\n")
            
            preview_text = clean_markdown.strip().replace('\n', ' ')
            print(f'   "{preview_text[:400]}..."')
            print("-" * 70)
            
            time.sleep(2)
            
    except Exception as e:
        print(f"Pipeline broke down. Error details: {e}")

if __name__ == "__main__":
    BLOG_DOMAIN = "scrapfly.io/blog"
  
    USER_PROMPT = "cloudflare fingerprinting web scraping"
    
    integrated_research_pipeline(BLOG_DOMAIN, USER_PROMPT, max_links=2)