import requests
import json

def fetch_clinical_trials(search_term, limit=5):
    """
    Fetches recent clinical trials for a given search term using the ClinicalTrials.gov API.
    """
    # The official API endpoint for ClinicalTrials.gov
    url = "https://clinicaltrials.gov/api/v2/studies"
    
    # Parameters to filter the search and limit results
    params = {
        "query.term": search_term,
        "pageSize": limit,
        "format": "json"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        extracted_trials = []
        
        # Parse the structured JSON data
        for study in data.get("studies", []):
            protocol = study.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            status = protocol.get("statusModule", {})
            description = protocol.get("descriptionModule", {})
            
            trial_info = {
                "NCT_ID": identification.get("nctId", "N/A"),
                "Title": identification.get("briefTitle", "N/A"),
                "Status": status.get("overallStatus", "N/A"),
                "Summary": description.get("briefSummary", "No summary provided.")
            }
            extracted_trials.append(trial_info)
            
        return extracted_trials

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# --- Testing the extraction ---
if __name__ == "__main__":
    query = "mRNA vaccine"
    print(f"--- Extracting Clinical Trials for: {query} ---")
    
    trials = fetch_clinical_trials(query, limit=3)
    
    if trials:
        for i, trial in enumerate(trials, 1):
            print(f"\nTrial {i}: {trial['Title']}")
            print(f"Status: {trial['Status']}")
            print(f"Summary: {trial['Summary'][:200]}...") # Truncated for readability