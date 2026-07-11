import requests
import random
import time

def find_working_searxng():
    print("Fetching instance list from searx.space...")
    try:
        r = requests.get('https://searx.space/data/instances.json', timeout=10)
        data = r.json()
        instances = data.get('instances', {})
    except Exception as e:
        print("Failed to fetch list:", e)
        return
        
    candidates = []
    for url, info in instances.items():
        if not url.startswith('https://'):
            continue
        uptime_day = info.get('uptime', {}).get('uptimeDay', 0)
        # Check if uptime is good
        if uptime_day > 90:
            candidates.append(url.rstrip('/'))
            
    print(f"Found {len(candidates)} candidate HTTPS instances. Testing...")
    
    random.shuffle(candidates)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    working_instances = []
    
    for idx, url in enumerate(candidates):
        if len(working_instances) >= 5:
            break
        print(f"[{idx+1}/{len(candidates)}] Testing {url}...")
        try:
            # We will try both format=json and HTML search
            resp = requests.get(f"{url}/search", params={'q': 'Apple Inc', 'format': 'json'}, headers=headers, timeout=5)
            if resp.status_code == 200:
                results = resp.json().get('results', [])
                if results:
                    print(f"  👉 SUCCESS (JSON): {url}")
                    working_instances.append((url, "json"))
                    continue
            
            # If JSON is blocked, test HTML search
            resp_html = requests.get(f"{url}/search", params={'q': 'Apple Inc'}, headers=headers, timeout=5)
            if resp_html.status_code == 200 and "not a bot" not in resp_html.text.lower() and "cloudflare" not in resp_html.text.lower():
                if "result" in resp_html.text.lower():
                    print(f"  👉 SUCCESS (HTML): {url}")
                    working_instances.append((url, "html"))
        except Exception as e:
            # print(f"  Failed: {e}")
            pass
            
    print("\nWorking instances found:")
    for w in working_instances:
        print(f"- {w[0]} (Type: {w[1]})")

if __name__ == "__main__":
    find_working_searxng()
