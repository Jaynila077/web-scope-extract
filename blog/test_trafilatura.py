import trafilatura

def extract_blog_text(url):

    downloaded_html = trafilatura.fetch_url(url)
    
    if not downloaded_html:
        print("Failed to download the page. It might be blocking scrapers.")
        return

    print("Page downloaded successfully. Running extraction heuristics...\n")
    print("=" * 70)
    
    clean_text = trafilatura.extract(
        downloaded_html, 
        output_format="markdown",
        include_comments=False, # We don't want random user comments in our data
        include_links=True      # Keep the context of where links point
    )
    
    if not clean_text:
        print("Extraction failed. Trafilatura couldn't find the main text body.")
        return

    print("EXTRACTED CONTENT (Preview):\n")
    print(clean_text[:1000])
    print("\n" + "=" * 70)
    print(f"Total Characters Extracted: {len(clean_text)}")

if __name__ == "__main__":
   
    TARGET_URL = "https://scrapfly.io/blog/how-to-bypass-cloudflare-in-2024/"
    
    extract_blog_text(TARGET_URL)