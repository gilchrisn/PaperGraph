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

# Global list of paper titles to process
paper_titles = [
    'Worst-Case Optimal Graph Joins in Almost No Space',
    'Densest Subgraph in Streaming and MapReduce',
    'Counting distinct elements in a data stream',
    'On Synopses for Distinct-Value Estimation under Multiset Operations',
    'Flowless: Extracting Densest Subgraphs Without Flow Computations',
    'Greedy approximation algorithms for finding dense components in a graph',
    'Atrapos: Real-time Evaluation of Metapath Query Workloads',
    'Reachability and distance queries via 2-hop labels',
    'Effective and Efficient Community Search over Large Heterogeneous Information Networks',
    'Efficient algorithms for densest subgraph discovery',
    'Adopting Worst-Case Optimal Joins in Relational Database Systems',
    'Piggybacking on Social Networks',
    'Finding a Maximum Density Subgraph',
    'Efficient Core Decomposition over Large Heterogeneous Information Networks',
    'Effective Community Search over Large Star-Schema Heterogeneous Information Networks',
    'The Densest Subgraph Problem with a Convex/Concave Size Function',
    'Query-based outlier detection in heterogeneous information networks',
    'On a Quest for Combating Filter Bubbles and Misinformation',
    'A Survey on the Densest Subgraph Problem and its Variants',
    'Anytime Bottom-Up Rule Learning for Knowledge Graph Completion',
    'Characterizing covid-19 misinformation communities using a novel twitter dataset',
    'Discovering meta-paths in large heterogeneous information networks',
    'Scalable large near-clique detection in large-scale networks via sampling',
    'Worst-case Optimal Join Algorithms',
    'Discovering personalized characteristic communities in attributed graphs',
    'Semantic path based personalized recommendation on weighted heterogeneous information networks',
    'A Survey of Computational Methods for protein Complex Prediction from protein Interaction Networks',
    'Core discovery in hidden networks',
    'Path-Sim: Meta Path-Based Top-K Similarity Search in Heterogeneous Information Networks',
    'The K-clique Densest Subgraph Problem',
    'Triejoin: A Simple, Worst-Case Optimal Join Algorithm',
    'The Generalized Mean Densest Subgraph Problem',
    'A survey of typical attributed graph queries',
    'A core-attachment based method to detect protein complexes in PPI networks',
    'Extracting and Analyzing Hidden Graphs from Relational Databases',
    'Efficient and effective algorithms for generalized densest subgraph discovery',
    'Effective and Efficient Truss Computation over Large Heterogeneous Information Networks',
    'Contextaware outstanding fact mining from knowledge graphs',
    'Local Clustering over Labeled Graphs: An Index-Free Approach',
    'Influential Community Search over Large Heterogeneous Information Networks',
    'A Countingbased Approach for Efficient k-Clique Densest Subgraph Discovery',
    'In-depth Analysis of Densest Subgraph Discovery in a Unified Framework'
]

def fetch_semantic_scholar_metadata(paper_id: str, api_key: str = None) -> dict:
    fields = (
        "paperId,title,year,venue,externalIds,openAccessPdf,"
        "references,citations"
    )
    url = f"{SEMANTIC_SCHOLAR_BASE_URL}{paper_id}?fields={fields}"
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key
    print(f"Fetching metadata from: {url}")
    while True:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 429:
            logger.warning("Rate limit reached. Waiting 10 seconds before retrying...")
            time.sleep(10)
            continue
        elif response.status_code != 200:
            print(f"API request failed: {response.status_code} - {response.text}")
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
        time.sleep(1)  # Respect rate limits
        return response.json()

def search_papers_by_title(title: str, limit: int = 10, api_key=SEMANTIC_SCHOLAR_API_KEY) -> dict:
    search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": title,
        "limit": limit,
        "fields": "paperId,title,year,venue,externalIds,openAccessPdf"
    }
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key
    print(f"Searching for papers with title: {title}")
    response = requests.get(search_url, params=params, headers=headers, timeout=10)
    if response.status_code == 429:
        logger.warning("Rate limit reached during search. Waiting 10 seconds before retrying...")
        time.sleep(10)
        return search_papers_by_title(title, limit, api_key)
    elif response.status_code != 200:
        print(f"Search request failed: {response.status_code} - {response.text}")
        raise Exception(f"Search request failed: {response.status_code} - {response.text}")
    time.sleep(1)  # Respect rate limits
    return response.json()

def download_arxiv_pdf(arxiv_id: str) -> str:
    filename = f"{arxiv_id}.pdf"
    file_path = os.path.join(PDF_SAVE_DIRECTORY, filename)
    if os.path.exists(file_path):
        print(f"PDF already exists as {file_path}.")
        return file_path
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    try:
        print(f"Downloading PDF from {pdf_url} ...")
        response = requests.get(pdf_url, timeout=15)
        response.raise_for_status()
        if not os.path.exists(PDF_SAVE_DIRECTORY):
            os.makedirs(PDF_SAVE_DIRECTORY)
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Saved PDF as {file_path}")
        return file_path
    except Exception as e:
        print(f"Failed to download PDF for {arxiv_id}: {e}")
        return None

def download_pdf_from_url(url: str, paper_id: str) -> str:
    filename = f"{paper_id}.pdf"
    file_path = os.path.join(PDF_SAVE_DIRECTORY, filename)
    try:
        print(f"Attempting to download PDF from {url} ...")
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        if not os.path.exists(PDF_SAVE_DIRECTORY):
            os.makedirs(PDF_SAVE_DIRECTORY)
        with open(file_path, "wb") as f:
            f.write(response.content)
        print(f"Saved PDF as {file_path}")
        return file_path
    except Exception as e:
        print(f"Failed to download PDF from {url}: {e}")
        return None

def get_pdf_page_count(file_path: str) -> int:
    try:
        reader = PdfReader(file_path)
        return len(reader.pages)
    except Exception as e:
        print(f"Failed to read PDF '{file_path}': {e}")
        return None

def insert_paper(db_client, paper: dict):
    try:
        response = db_client.table("papers").insert(paper).execute()
        print(f"Inserted paper: {paper['semantic_id']} - {paper['title']}")
    except Exception as e:
        if "23505" in str(e):
            print(f"Paper {paper['semantic_id']} already exists, skipping insertion.")
        else:
            print(f"Error inserting paper {paper['semantic_id']}: {e}")

def insert_citation(db_client, source_id: str, cited_id: str):
    try:
        payload = {
            "source_paper_id": source_id,
            "cited_paper_id": cited_id,
        }
        response = db_client.table("citations").insert(payload).execute()
        print(f"Inserted citation: {source_id} -> {cited_id}")
    except Exception as e:
        print(f"Error inserting citation from {source_id} to {cited_id}: {e}")

def process_and_cite_paper(paper_id: str, db_client, api_key=SEMANTIC_SCHOLAR_API_KEY):
    """
    Processes a paper:
      - Checks if already in DB.
      - If not, fetch metadata, download PDF (via ArXiv or openAccessPdf), and insert.
      - Then, process its references recursively.
    """
    try:
        result = db_client.table("papers").select("semantic_id").eq("semantic_id", paper_id).execute()
        if result.data:
            print(f"Paper {paper_id} already exists in the database; skipping processing.")
            return
    except Exception as e:
        print(f"Error checking for existing paper {paper_id}: {e}")
        return

    print(f"\nProcessing and citing paper {paper_id}")
    try:
        metadata = fetch_semantic_scholar_metadata(paper_id, api_key)
    except Exception as e:
        print(f"Failed to fetch metadata for {paper_id}: {e}")
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
        print(f"Paper {paper_id} has ArXiv id: {arxiv_id}. Attempting download from ArXiv.")
        local_filepath = download_arxiv_pdf(arxiv_id)
    elif open_access_pdf_info and open_access_pdf_info.get("url"):
        online_url = open_access_pdf_info["url"]
        print(f"Paper {paper_id} has openAccessPdf url: {online_url}. Attempting download.")
        local_filepath = download_pdf_from_url(online_url, paper_id)
    else:
        print(f"Paper {paper_id} has no available PDF source; skipping processing.")
        return

    if not local_filepath:
        print(f"Failed to download PDF for paper {paper_id} ({title}); skipping insertion.")
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

if __name__ == "__main__":
    # 1. Insert the manually defined paper (manual1)
    manual1 = {
        "semantic_id": "manual1",
        "title": "SANS: Efficient Densest Subgraph Discovery over Relational Graphs without Materialization",
        "year": 2025,
        "venue": "WWW2025",
        "external_ids": {},
        "open_access_pdf": "https://openreview.net/pdf/59081de192e38304f932062ed085a8597351e931.pdf",
        "local_filepath": os.path.join(PDF_SAVE_DIRECTORY, "manual1.pdf")
    }
    insert_paper(supabase, manual1)

    # 2. Process each paper title from the global variable "paper_titles"
    not_found_titles = []
    for title in paper_titles:
        try:
            search_results = search_papers_by_title(title)
        except Exception as e:
            print(f"Search failed for title '{title}': {e}")
            not_found_titles.append(title)
            continue

        data = search_results.get("data", [])
        if not data:
            print(f"No results found for title: {title}")
            not_found_titles.append(title)
            continue

        # Use the first search result from Semantic Scholar.
        paper_id = data[0].get("paperId")
        if not paper_id:
            print(f"No paperId found in search result for title: {title}")
            not_found_titles.append(title)
            continue

        # Process and insert the paper (download PDF, insert record, etc.)
        process_and_cite_paper(paper_id, supabase)

        # Now check if the paper exists in the DB. If it does, insert a citation from manual1.
        try:
            result = supabase.table("papers").select("semantic_id").eq("semantic_id", paper_id).execute()
            if result.data:
                insert_citation(supabase, "manual1", paper_id)
            else:
                print(f"Paper {paper_id} not found in the database after processing; skipping citation.")
        except Exception as e:
            print(f"Error checking for paper {paper_id} in database: {e}")

        time.sleep(0.5)  # Respect rate limits

    if not_found_titles:
        print("The following paper titles were not found on Semantic Scholar:")
        for t in not_found_titles:
            print(t)
