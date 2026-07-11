import requests
import json

def fetch_wiki_data(query, lang="en"):
    """
    Fetches structured data from Wikipedia for a given query using the MediaWiki API.
    """
    # MediaWiki API endpoint for Wikipedia
    url = f"https://{lang}.wikipedia.org/w/api.php"
    
    # Parameters for the API request
    params = {
        "action": "query",
        "format": "json",
        "titles": query,
        "prop": "extracts|extlinks|links",
        "explaintext": True, # Returns plain text instead of HTML
        "exsectionformat": "plain",
        "pllimit": "max" # Get maximum number of internal links
    }
    
    headers = {
        # Wikipedia asks for a descriptive User-Agent
        "User-Agent": "WebScopeExtract_CDAC_Project/1.0 (mahak@example.com)"
    }
    
    print(f"Scraping Wikipedia for: '{query}'...")
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Extract the page data from the JSON response
        pages = data.get("query", {}).get("pages", {})
        
        # The API returns a dictionary with the page ID as the key
        for page_id, page_info in pages.items():
            if page_id == "-1":
                return {"error": f"No Wikipedia page found for '{query}'"}
            
            # Structuring the payload for your LLM pipeline
            structured_payload = {
                "title": page_info.get("title"),
                "content": page_info.get("extract", "No content available."),
                "internal_links_count": len(page_info.get("links", [])),
                "source_url": f"https://{lang}.wikipedia.org/wiki/{query.replace(' ', '_')}"
            }
            
            return structured_payload

    except requests.exceptions.RequestException as e:
        return {"error": f"API Request failed: {e}"}

# --- Execution ---
if __name__ == "__main__":
    test_query = "Artificial intelligence"
    result = fetch_wiki_data(test_query)
    
    # Print the resulting JSON structure that would be fed to the LLM
    print(json.dumps(result, indent=4))