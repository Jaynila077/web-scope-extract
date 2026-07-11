import requests
import pdfplumber
import io

def extract_full_paper_text(pdf_url):
    """
    Downloads a PDF directly into memory and extracts its text using pdfplumber.
    """
    # arXiv PDF links sometimes lack the .pdf extension, which is fine for requests, 
    # but we ensure the connection is secure.
    secure_url = pdf_url.replace("http://", "https://")
    print(f"Downloading PDF from: {secure_url}...")
    
    response = requests.get(secure_url)
    
    if response.status_code != 200:
        print(f"Failed to download PDF. Status code: {response.status_code}")
        return None

    print("PDF downloaded successfully. Beginning extraction...")
    
    full_text = ""
    
    # Process the PDF in-memory using io.BytesIO
    try:
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            total_pages = len(pdf.pages)
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
                
                # Optional: Print progress for large papers
                if (page_num + 1) % 5 == 0 or (page_num + 1) == total_pages:
                    print(f"Extracted {page_num + 1}/{total_pages} pages...")
                    
        return full_text
    except Exception as e:
        print(f"An error occurred during PDF parsing: {e}")
        return None

# --- Execution Example ---
if __name__ == "__main__":
    # Example link extracted from the previous arXiv API script
    sample_pdf_link = "http://arxiv.org/pdf/2307.00162v1" 
    
    extracted_text = extract_full_paper_text(sample_pdf_link)
    
    if extracted_text:
        print("\n--- Extraction Complete ---")
        print(f"Total characters extracted: {len(extracted_text)}")
        print("\n--- Preview of First 500 Characters ---")
        print(extracted_text[:500])