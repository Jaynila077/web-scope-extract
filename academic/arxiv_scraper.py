import requests
import xml.etree.ElementTree as ET

def fetch_arxiv_papers(query, max_results=3):
    """
    Fetches research papers from the arXiv API based on a search query.
    """
    # The arXiv API endpoint
    url = "http://export.arxiv.org/api/query"
    
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }
    
    print(f"Querying arXiv for: '{query}'...\n")
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        print(f"Failed to fetch data: {response.status_code}")
        return None

    # Parse the XML response
    root = ET.fromstring(response.content)
    
    # arXiv XML uses namespaces, which we need to define to find elements
    namespace = {'atom': 'http://www.w3.org/2005/Atom'}
    
    extracted_papers = []
    
    # Iterate through each 'entry' (paper) in the XML
    for entry in root.findall('atom:entry', namespace):
        title = entry.find('atom:title', namespace).text.replace('\n', ' ').strip()
        summary = entry.find('atom:summary', namespace).text.replace('\n', ' ').strip()
        published_date = entry.find('atom:published', namespace).text
        paper_url = entry.find('atom:id', namespace).text
        
        # Extract authors
        authors = [author.find('atom:name', namespace).text for author in entry.findall('atom:author', namespace)]
        
        # Extract the direct PDF link
        pdf_link = next((link.attrib['href'] for link in entry.findall('atom:link', namespace) if link.attrib.get('title') == 'pdf'), None)

        paper_data = {
            "title": title,
            "authors": ", ".join(authors),
            "published": published_date[:10], # Grab just the YYYY-MM-DD
            "summary": summary,
            "url": paper_url,
            "pdf_link": pdf_link
        }
        extracted_papers.append(paper_data)
        
    return extracted_papers

# --- Execution ---
if __name__ == "__main__":
    search_topic = "large language model hallucinations"
    papers = fetch_arxiv_papers(search_topic)
    
    if papers:
        for i, paper in enumerate(papers, 1):
            print(f"--- Paper {i} ---")
            print(f"Title: {paper['title']}")
            print(f"Authors: {paper['authors']}")
            print(f"Date: {paper['published']}")
            print(f"Abstract: {paper['summary'][:250]}...") # Truncated for display
            print(f"PDF Link: {paper['pdf_link']}\n")