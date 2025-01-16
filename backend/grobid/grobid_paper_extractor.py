import requests
from bs4 import BeautifulSoup
import grobid_tei_xml
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the GROBID server URL
GROBID_BASE_URL = os.getenv("GROBID_BASE_URL")

# Keywords for filtering section titles
HEAD_KEYWORDS = [
    "evaluation", "methodology", "related work", "conclusion", "baseline"
]

def send_request_to_grobid(endpoint, pdf_path):
    """
    Sends a request to the GROBID server for a specified endpoint.

    Parameters:
        endpoint (str): GROBID endpoint (e.g., processFulltextDocument).
        pdf_path (str): Path to the PDF file.

    Returns:
        response: Response object from the GROBID server.
    """
    url = f"{GROBID_BASE_URL}/{endpoint}"
    files = {'input': open(pdf_path, 'rb')}
    headers = {'Accept': 'application/xml'}

    return requests.post(url, files=files, headers=headers)

def extract_tei_from_pdf(pdf_path):
    """
    Extract TEI XML from a PDF using GROBID.

    Parameters:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: TEI XML as a string if successful, otherwise None.
    """
    response = send_request_to_grobid("processFulltextDocument", pdf_path)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Error extracting TEI XML: {response.status_code}")
        return None

def extract_filtered_sections_from_tei(tei_xml, keywords=HEAD_KEYWORDS):
    """
    Extract filtered sections (titles and content) based on keywords from the TEI XML.

    Parameters:
        tei_xml (str): The TEI XML content as a string.
        keywords (list): List of keywords to filter section titles.

    Returns:
        dict: A dictionary with filtered section titles as keys and full <div> content as values.
    """
    soup = BeautifulSoup(tei_xml, "xml")
    filtered_sections = {}

    for div in soup.find_all("div", xmlns="http://www.tei-c.org/ns/1.0"):
        head = div.find("head")
        if head and head.text.strip():
            title = head.text.strip()
            if any(keyword.lower() in title.lower() for keyword in keywords):
                filtered_sections[title] = div.text.strip()

    return filtered_sections

def extract_metadata(pdf_path, metadata_type):
    """
    Extract metadata (title, abstract, or references) from a PDF using GROBID.

    Parameters:
        pdf_path (str): Path to the PDF file.
        metadata_type (str): The type of metadata to extract (e.g., "processHeaderDocument", "processReferences").

    Returns:
        str or list: Extracted metadata or an error message.
    """
    response = send_request_to_grobid(metadata_type, pdf_path)

    if response.status_code == 200:
        if metadata_type == "processHeaderDocument":
            doc = grobid_tei_xml.parse_document_xml(response.text)
            return {
                "title": doc.header.title if doc.header.title else "Title not found.",
                "abstract": doc.abstract if doc.abstract else "Abstract not found.",
                "authors": doc.header.authors if doc.header.authors else [],
                "doi": doc.header.doi if doc.header.doi else "DOI not found.",
                "citations": doc.citations if doc.citations else []
            }
        elif metadata_type == "processReferences":
            citations = grobid_tei_xml.parse_citation_list_xml(response.text)
            return [citation.title for citation in citations if citation.title] or ["No reference titles found."]
    else:
        print(f"Error extracting {metadata_type}: {response.status_code}")
        return None

def format_extracted_data(title, abstract, references, sections):
    """
    Format the extracted data into a structured output.

    Parameters:
        title (str): The paper title.
        abstract (str): The paper abstract.
        references (list): List of reference titles.
        sections (dict): Dictionary of filtered section titles and content.

    Returns:
        str: Formatted string of the extracted data.
    """
    formatted_data = [f"Title: {title}", f"Abstract: {abstract}"]

    formatted_data.append("\nReferences:")
    for ref in references:
        formatted_data.append(f"- {ref}")

    formatted_data.append("\nFiltered Sections:")
    for section_title, content in sections.items():
        formatted_data.append(f"\n{section_title}:\n{content[len(section_title):]}")  # Truncate content for brevity

    return "\n".join(formatted_data)


# Extract everything metadata, title, abstract, references, and filtered sections then format the output
def extract_all_metadata(pdf_path):
    """
    Extract all metadata, title, abstract, references, and filtered sections from a PDF.

    Parameters:
        pdf_path (str): Path to the PDF file.

    Returns:
        str: Formatted string of the extracted data.
    """
    # Extract TEI XML
    tei_xml = extract_tei_from_pdf(pdf_path)

    if tei_xml:
        # Extract filtered sections
        filtered_sections = extract_filtered_sections_from_tei(tei_xml, HEAD_KEYWORDS)

    # Extract title and abstract
    metadata = extract_metadata(pdf_path, "processHeaderDocument")
    title = metadata["title"] if metadata else "Title extraction failed."
    abstract = metadata["abstract"] if metadata else "Abstract extraction failed."

    # Extract reference titles
    references = extract_metadata(pdf_path, "processReferences") or []

    # Format and return the extracted data
    return format_extracted_data(title, abstract, references, filtered_sections)

# Example usage
if __name__ == "__main__":
    pdf_path = "resources/papers/A Compiler for Throughput Optimization of Graph Algorithms on GPUs.pdf"

    if not os.path.exists(pdf_path):
        print(f"PDF file not found at: {pdf_path}")
    else:
        # Extract TEI XML
        tei_xml = extract_tei_from_pdf(pdf_path)

        if tei_xml:
            # Extract filtered sections
            filtered_sections = extract_filtered_sections_from_tei(tei_xml, HEAD_KEYWORDS)

        # Extract title and abstract
        metadata = extract_metadata(pdf_path, "processHeaderDocument")
        title = metadata["title"] if metadata else "Title extraction failed."
        abstract = metadata["abstract"] if metadata else "Abstract extraction failed."

        # Extract reference titles
        references = extract_metadata(pdf_path, "processReferences") or []

        # Format and print the extracted data
        formatted_output = format_extracted_data(title, abstract, references, filtered_sections)
        print("\nFormatted Extracted Data:\n")
        print(formatted_output)
