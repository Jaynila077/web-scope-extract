from usp.tree import sitemap_tree_for_homepage

def sitemap_recon_scout(domain_url, max_results=10):
    print(f"[RECON SCOUT] Attempting to map domain: {domain_url}...\n")
    
   
    tree = sitemap_tree_for_homepage(domain_url)
    
 
    if not tree:
        print("Could not locate a sitemap for this domain.")
        return

    print("Sitemap located! Extracting structural data...\n")
    print("=" * 70)
    
    # tree.all_pages() returns an iterator containing all found URLs
    extracted_count = 0
    
    for page in tree.all_pages():
        if extracted_count >= max_results:
            break
            
        url = page.url
        last_modified = page.last_modified if page.last_modified else "Unknown"
        priority = page.priority if page.priority else "Default"
        
        print(f"Post URL: {url}")
        print(f"Last Updated: {last_modified}")
        print(f"Site Priority: {priority}")
        print("-" * 70)
        
        extracted_count += 1

if __name__ == "__main__":
  
    TARGET_DOMAIN = "https://scrapfly.io/" 
    
    sitemap_recon_scout(TARGET_DOMAIN, max_results=5)