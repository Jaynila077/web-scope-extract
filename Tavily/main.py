import os
from dotenv import load_dotenv
from tavily import TavilyClient

# Load variables from .env file into environment
load_dotenv()

# Retrieve API key from environment
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY not found! Please check your .env file.")

# Initialize Tavily client
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


def experiment_basic_search():
    """1. Basic Search - Get structured results with title, URL, snippet, and relevance score."""
    print("=== EXPERIMENT 1: Basic Search ===")
    response = tavily_client.search(
        query="What are the main causes of solar flares?",
        max_results=3
    )

    for result in response.get("results", []):
        print(f"\nTitle: {result['title']}")
        print(f"URL:   {result['url']}")
        print(f"Score: {result['score']}")
        print(f"Text:  {result['content'][:150]}...")


def experiment_qna_search():
    """2. Direct Q&A Search - Returns a single synthesized AI answer instead of full lists."""
    print("\n=== EXPERIMENT 2: Quick Q&A Search ===")
    answer = tavily_client.qna_search(
        query="What is the distance between the Earth and the Moon in kilometers?"
    )
    print(f"Direct Answer: {answer}")


def experiment_advanced_filtering():
    """3. Advanced Search - Filter by domain, search depth, and get AI-generated summary answers."""
    print("\n=== EXPERIMENT 3: Advanced Deep Search ===")
    response = tavily_client.search(
        query="Latest news on fusion energy milestones",
        search_depth="advanced",          # "basic" (fast) or "advanced" (deeper, higher quality)
        topic="news",                    # "general", "news", or "finance"
        include_answer=True,             # Generates a summary answer inside the response
        max_results=3,
        include_domains=["nature.com", "sciencedaily.com"]  # Limit to trusted sites
    )

    print(f"\nAI Summary Answer: {response.get('answer')}\n")
    print("Top Filtered Results:")
    for res in response.get("results", []):
        print(f"- {res['title']} ({res['url']})")


def experiment_web_extract():
    print("\n=== EXPERIMENT 4: Webpage Extraction ===")
    target_urls = [
        "https://en.wikipedia.org/wiki/James_Webb_Space_Telescope"
    ]
    
    # Passing a query strips boilerplate navigation and extracts only relevant text
    extraction = tavily_client.extract(
        urls=target_urls, 
        extract_depth="advanced",
        query="What are the main scientific instruments on the James Webb Space Telescope?"
    )
    
    for item in extraction.get("results", []):
        print(f"URL: {item['url']}")
        print(f"Extracted Content:\n{item['raw_content'][:]}...\n")


if __name__ == "__main__":
    # Run experiments
    experiment_basic_search()
    experiment_qna_search()
    experiment_advanced_filtering()
    experiment_web_extract()
