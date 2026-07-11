import requests
import json

def substack_newsletter_scout(substack_domain, max_posts=5):
    print(f"[SUBSTACK SCOUT] Intercepting backend API for: {substack_domain}...\n")
    
   
    api_url = f"https://{substack_domain}/api/v1/posts"
    
    params = {
        "limit": max_posts,
        "offset": 0
    }
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status() 
        
        posts = response.json()
        
        if not posts:
            print("No posts found or the API structure changed.")
            return

        print(f"Success! Extracted {len(posts)} posts directly from the database.\n")
        print("=" * 70)
        
        for index, post in enumerate(posts, start=1):
            title = post.get('title', 'No Title')
            post_url = post.get('canonical_url', 'No URL')
            date = post.get('post_date', 'Unknown Date')
            
            audience = post.get('audience', 'everyone')
            is_paywalled = "Paywalled" if audience != 'everyone' else "Not Paywalled"
            
            description = post.get('description', 'No description available.')
            
            print(f"Post {index}: {title}")
            print(f"URL: {post_url}")
            print(f"Date: {date}")
            print(f"Paywalled: {is_paywalled}")
            print(f"Subtitle: {description}")
            print("-" * 70)
            
    except Exception as e:
        print(f"Failed to extract data. Error: {e}")

if __name__ == "__main__":
    
    TARGET_NEWSLETTER = "blog.pragmaticengineer.com" 
    
    substack_newsletter_scout(TARGET_NEWSLETTER, max_posts=3)