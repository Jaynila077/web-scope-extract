import requests
import pdfplumber
import io

def extract_text_from_pdf_url(pdf_url, max_pages=3):
    """
    Downloads a PDF from a given URL and extracts clean text from its pages.
    """
    print(f"Downloading PDF from: {pdf_url}...")
    
    try:
        # Fetch the PDF file
        response = requests.get(pdf_url, stream=True)
        response.raise_for_status()
        
        # Load the PDF content into memory (avoiding local file saves for pipeline speed)
        pdf_memory_file = io.BytesIO(response.content)
        
        extracted_text = ""
        
        # Parse the PDF using pdfplumber
        with pdfplumber.open(pdf_memory_file) as pdf:
            total_pages = len(pdf.pages)
            pages_to_process = min(max_pages, total_pages)
            
            print(f"PDF loaded successfully. Processing first {pages_to_process} pages...\n")
            
            for i in range(pages_to_process):
                page = pdf.pages[i]
                # extract_text() pulls the raw semantic text from the page layout
                page_text = page.extract_text()
                
                if page_text:
                    extracted_text += f"--- PAGE {i + 1} ---\n"
                    extracted_text += page_text + "\n\n"
                    
        return extracted_text

    except requests.exceptions.RequestException as e:
        print(f"Network error fetching the PDF: {e}")
        return None
    except Exception as e:
        print(f"Error parsing the PDF: {e}")
        return None

# --- Testing the extraction ---
if __name__ == "__main__":
    # Example: A sample public domain PDF link (replace with a real WHO advisory URL in production)
    sample_who_report_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf" 
    
    document_text = extract_text_from_pdf_url(sample_who_report_url, max_pages=2)
    
    if document_text:
        print("=== EXTRACTED ADVISORY TEXT ===")
        print(document_text[:500]) # Truncating the output for readability
        print("===============================")