from exa_py import Exa
import os

def neural_scout_pipeline(semantic_query, max_links=2):
    
    EXA_API_KEY = "add api key to test" 
    exa = Exa(api_key=EXA_API_KEY)
    
    try:
        response = exa.search(
            semantic_query,
            type="auto",
            num_results=max_links,
            contents={"highlights": True}
        )
        
        results = response.results
        
        if not results:
            print("No semantic matches found.")
            return

        print(f"Found {len(results)} deep-web matches. Outputting extracted highlights...\n")
        print("=" * 70)
        
        for index, article in enumerate(results, start=1):
            print(f"Article {index}: {article.title}")
            print(f"URL: {article.url}")
            
            print(f"EXTRACTED HIGHLIGHTS:")
            
            if article.highlights:
                for highlight in article.highlights:
                    clean_highlight = highlight.replace('\n', ' ').strip()
                    print(f"   > \"{clean_highlight}\"")
            else:
                print("   > No highlights returned for this page.")
                
            print("-" * 70)
            
    except Exception as e:
        print(f"API call failed. Did you paste your API key? Error: {e}")

if __name__ == "__main__":
    USER_PROMPT = "Here is a highly detailed, technical engineering blog post about bypassing Cloudflare for web scraping:"
    
    neural_scout_pipeline(USER_PROMPT)