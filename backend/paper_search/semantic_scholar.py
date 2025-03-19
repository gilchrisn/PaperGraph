import os
import time
import requests
import logging
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

from supabase import Client, create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-supabase-url.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-supabase-api-key")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)




SEMANTIC_SCHOLAR_BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/"
SEMANTIC_SCHOLAR_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", None)

# Maximum recursion depth for processing citations
MAX_DEPTH = 4

# A set to track processed Semantic Scholar paper ids to avoid duplicates
processed_papers = set()

# Directory to save downloaded PDFs (adjust as needed)
PDF_SAVE_DIRECTORY = "downloaded_papers"


def fetch_semantic_scholar_metadata(paper_id: str, api_key: str = None) -> dict:
    """
    Given a paper identifier (e.g., a Semantic Scholar paper id or DOI),
    fetch metadata using the Semantic Scholar API.
    """
    fields = (
        "paperId,title,year,venue,externalIds,openAccessPdf,"
        "references,citations"
    )
    url = f"{SEMANTIC_SCHOLAR_BASE_URL}{paper_id}?fields={fields}"
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    logger.info(f"Fetching metadata from: {url}")
    
    while True:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 429:
            logger.warning("Rate limit reached. Waiting 10 seconds before retrying...")
            time.sleep(10)
            continue
        elif response.status_code != 200:
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
        
        time.sleep(1)  # Respect rate limits
        return response.json()


def search_papers_by_title(title: str, limit: int = 10, api_key = SEMANTIC_SCHOLAR_API_KEY) -> dict:
    """
    Search for papers on Semantic Scholar by title and return the top 'limit' results.
    """
    search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    print("search_url", search_url)
    params = {
        "query": title,
        "limit": limit,
        "fields": "paperId,title,year,venue,externalIds,openAccessPdf"
    }
    print("params", params)
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    logger.info(f"Searching for papers with title: {title}")
    response = requests.get(search_url, params=params, headers=headers, timeout=10)
    if response.status_code == 429:
        logger.warning("Rate limit reached during search. Waiting 10 seconds before retrying...")
        time.sleep(10)
        return search_papers_by_title(title, limit, api_key)
    elif response.status_code != 200:
        logger.error(f"Search request failed: {response.status_code} - {response.text}")
        raise Exception(f"Search request failed: {response.status_code} - {response.text}")
    
    time.sleep(1)  # Respect rate limits
    return response.json()


def download_arxiv_pdf(arxiv_id: str) -> str:
    """
    Given an ArXiv ID, download the PDF from ArXiv and save it locally.
    Returns the local file path or None if download fails.
    """
    filename = f"{arxiv_id}.pdf"
    file_path = os.path.join(PDF_SAVE_DIRECTORY, filename)
    if os.path.exists(file_path):
        logger.info(f"PDF already exists as {file_path}.")
        return file_path

    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    try:
        logger.info(f"Downloading PDF from {pdf_url} ...")
        response = requests.get(pdf_url, timeout=15)
        response.raise_for_status()
        if not os.path.exists(PDF_SAVE_DIRECTORY):
            os.makedirs(PDF_SAVE_DIRECTORY)
        with open(file_path, "wb") as f:
            f.write(response.content)
        logger.info(f"Saved PDF as {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to download PDF for {arxiv_id}: {e}")
        return None


def download_pdf_from_url(url: str, paper_id: str) -> str:
    """
    Download a PDF from the given URL and save it locally using paper_id as filename.
    """
    filename = f"{paper_id}.pdf"
    file_path = os.path.join(PDF_SAVE_DIRECTORY, filename)
    try:
        logger.info(f"Attempting to download PDF from {url} ...")
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        if not os.path.exists(PDF_SAVE_DIRECTORY):
            os.makedirs(PDF_SAVE_DIRECTORY)
        with open(file_path, "wb") as f:
            f.write(response.content)
        logger.info(f"Saved PDF as {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to download PDF from {url}: {e}")
        return None


def get_pdf_page_count(file_path: str) -> int:
    try:
        reader = PdfReader(file_path)
        return len(reader.pages)
    except Exception as e:
        logger.error(f"Failed to read PDF '{file_path}': {e}")
        return None


def insert_paper(db_client, paper: dict):
    """
    Insert a paper record into the papers table.
    Expected keys:
      - semantic_id, title, year, venue, external_ids, open_access_pdf, local_filepath
    """
    try:
        response = db_client.table("papers").insert(paper).execute()
        logger.info(f"Inserted paper: {paper['semantic_id']} - {paper['title']}")
    except Exception as e:
        if "23505" in str(e):
            logger.info(f"Paper {paper['semantic_id']} already exists, skipping insertion.")
        else:
            logger.error(f"Error inserting paper {paper['semantic_id']}: {e}")


def insert_citation(db_client, source_id: str, cited_id: str, remarks: dict = None, relevance_score: float = None):
    """
    Insert a citation relationship into the citations table.
    The relationship_type is left as null.
    """
    try:
        payload = {
            "source_paper_id": source_id,
            "cited_paper_id": cited_id,
            "relationship_type": None,  # Left as null
            "remarks": remarks or {},
            "relevance_score": relevance_score
        }
        response = db_client.table("citations").insert(payload).execute()
        logger.info(f"Inserted citation: {source_id} -> {cited_id}")
    except Exception as e:
        logger.error(f"Error inserting citation from {source_id} to {cited_id}: {e}")


def process_paper_semantic(paper_id: str, db_client, api_key: str = None, depth: int = 0) -> bool:
    """
    Process a paper using Semantic Scholar:
      - Fetch metadata.
      - Attempt to download the PDF using available sources.
      - Only insert the paper if a PDF file is successfully downloaded.
      - Recursively process its references.
    Returns True if the paper was successfully inserted (or already exists), False otherwise.
    """
    global processed_papers
    if paper_id in processed_papers:
        return True
    
    if depth > MAX_DEPTH:
        logger.info(f"Depth {depth} exceeded MAX_DEPTH for paper {paper_id}; not processing further.")
        return False

    processed_papers.add(paper_id)
    
    logger.info(f"\nProcessing paper {paper_id} at depth {depth}")
    
    try:
        metadata = fetch_semantic_scholar_metadata(paper_id, api_key)
    except Exception as e:
        logger.error(f"Failed to fetch metadata for {paper_id}: {e}")
        return False

    if not metadata:
        return False

    title = metadata.get("title", "No Title")
    year = metadata.get("year")
    venue = metadata.get("venue")
    external_ids = metadata.get("externalIds", {})
    open_access_pdf_info = metadata.get("openAccessPdf", {})

    # Try to download the PDF and only continue if successful.
    local_filepath = None
    online_url = None

    if "ArXiv" in external_ids:
        arxiv_id = external_ids["ArXiv"].strip()
        online_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        logger.info(f"Paper {paper_id} has ArXiv id: {arxiv_id}. Attempting download from arXiv.")
        local_filepath = download_arxiv_pdf(arxiv_id)
    elif open_access_pdf_info and open_access_pdf_info.get("url"):
        online_url = open_access_pdf_info["url"]
        logger.info(f"Paper {paper_id} has openAccessPdf url: {online_url}. Attempting download.")
        local_filepath = download_pdf_from_url(online_url, paper_id)
    else:
        logger.warning(f"Paper {paper_id} has no available PDF source; skipping.")
        return False

    if not local_filepath:
        logger.warning(f"Failed to download PDF for paper {paper_id} ({title}); skipping insertion.")
        return False

    paper_record = {
        "semantic_id": paper_id,
        "title": title,
        "year": year,
        "venue": venue,
        "external_ids": external_ids,
        "open_access_pdf": online_url,
        "local_filepath": local_filepath
    }

    insert_paper(db_client, paper_record)

    # Process references recursively.
    references = metadata.get("references", [])
    logger.info(f"Paper {paper_id} references {len(references)} works.")
    for ref in references:
        ref_id = ref.get("paperId")
        if ref_id:
            child_inserted = process_paper_semantic(ref_id, db_client, api_key, depth=depth+1)
            if child_inserted:
                insert_citation(db_client, paper_id, ref_id)
            time.sleep(0.5)  # Respect rate limits

    return True


def process_and_cite_paper(paper_id: str, db_client, api_key = SEMANTIC_SCHOLAR_API_KEY):
    """
    Fetches, downloads, and inserts a paper, then creates citation entries
    for its references that already exist in the database.
    """
    try:
        result = db_client.table("papers").select("semantic_id").eq("semantic_id", paper_id).execute()
        if result.data:
            logger.info(f"Paper {paper_id} already exists in the database; skipping.")
            return
    except Exception as e:
        logger.error(f"Error checking for existing paper {paper_id}: {e}")
        return
    
    logger.info(f"\nProcessing and citing paper {paper_id}")

    try:
        metadata = fetch_semantic_scholar_metadata(paper_id, api_key)
    except Exception as e:
        logger.error(f"Failed to fetch metadata for {paper_id}: {e}")
        return

    if not metadata:
        return

    title = metadata.get("title", "No Title")
    year = metadata.get("year")
    venue = metadata.get("venue")
    external_ids = metadata.get("externalIds", {})
    open_access_pdf_info = metadata.get("openAccessPdf", {})

    local_filepath = None
    online_url = None

    if "ArXiv" in external_ids:
        arxiv_id = external_ids["ArXiv"].strip()
        online_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        logger.info(f"Paper {paper_id} has ArXiv id: {arxiv_id}. Attempting download from arXiv.")
        local_filepath = download_arxiv_pdf(arxiv_id)
    elif open_access_pdf_info and open_access_pdf_info.get("url"):
        online_url = open_access_pdf_info["url"]
        logger.info(f"Paper {paper_id} has openAccessPdf url: {online_url}. Attempting download.")
        local_filepath = download_pdf_from_url(online_url, paper_id)
    else:
        logger.warning(f"Paper {paper_id} has no available PDF source; skipping.")
        return

    if not local_filepath:
        logger.warning(f"Failed to download PDF for paper {paper_id} ({title}); skipping insertion.")
        return

    paper_record = {
        "semantic_id": paper_id,
        "title": title,
        "year": year,
        "venue": venue,
        "external_ids": external_ids,
        "open_access_pdf": online_url,
        "local_filepath": local_filepath
    }

    insert_paper(db_client, paper_record)

    # Process references and create citations only if they exist.
    references = metadata.get("references", [])
    logger.info(f"Paper {paper_id} references {len(references)} works.")
    for ref in references:
        ref_id = ref.get("paperId")
        if ref_id:
            try:
                result = db_client.table("papers").select("semantic_id").eq("semantic_id", ref_id).execute()
                if result.data:
                    insert_citation(db_client, paper_id, ref_id)
                else:
                    logger.info(f"Referenced paper {ref_id} not found in database; skipping citation.")
            except Exception as e:
                logger.error(f"Error checking for referenced paper {ref_id}: {e}")

            time.sleep(0.5)  # Respect rate limits




if __name__ == "__main__":
    

    # Search papers by title, 

    # Download them and save in database

    pass