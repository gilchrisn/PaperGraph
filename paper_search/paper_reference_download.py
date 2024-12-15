import os
import time
import requests
import random
from bs4 import BeautifulSoup
from grobid.grobid_paper_extractor import extract_tei_from_pdf, extract_filtered_sections_from_tei, extract_metadata
from paper_search.get_research_paper import search_and_download_google_paper
import signal
import traceback
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the GROBID server URL
GROBID_BASE_URL = os.getenv("GROBID_BASE_URL")

# Keywords for filtering section titles
HEAD_KEYWORDS = ["evaluation", "methodology", "related work", "conclusion", "baseline"]

# Statistics
stats = {
    "papers_processed": 0,
    "references_downloaded": 0,
    "extraction_times": [],
    "download_times": [],
    "keyword_counts": {key: 0 for key in HEAD_KEYWORDS},
    "papers_with_keywords": 0,  # Count of papers with at least one matching keyword
}

def signal_handler(sig, frame):
    """Handle keyboard interrupt and display statistics."""
    print("\nInterrupted! Displaying statistics...")
    display_statistics()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

def display_statistics():
    """Display the accumulated statistics."""
    total_extraction_time = sum(stats["extraction_times"])
    total_download_time = sum(stats["download_times"])
    total_papers = stats["papers_processed"]
    avg_extraction_time = total_extraction_time / max(total_papers, 1)
    avg_download_time = total_download_time / max(total_papers, 1)

    print("\nSummary Statistics:")
    print(f"Papers Processed: {stats['papers_processed']}")
    print(f"References Downloaded: {stats['references_downloaded']}")
    print(f"Total Extraction Time: {total_extraction_time:.2f} seconds")
    print(f"Average Extraction Time per Paper: {avg_extraction_time:.2f} seconds")
    print(f"Total Download Time: {total_download_time:.2f} seconds")
    print(f"Average Download Time per Paper: {avg_download_time:.2f} seconds")
    print("Keyword Counts in Filtered Sections:")
    for keyword, count in stats["keyword_counts"].items():
        print(f"  {keyword}: {count}")
    print(f"Papers with at least one keyword match: {stats['papers_with_keywords']}")

def safe_execute(func, *args, **kwargs):
    """Execute a function safely, catching and logging exceptions."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Error during {func.__name__}: {e}")
        traceback.print_exc()
        return None

def process_paper(pdf_path, save_directory):
    """Process a single paper: extract data and download references."""
    try:
        # Extract TEI XML
        tei_xml = safe_execute(extract_tei_from_pdf, pdf_path)
        if not tei_xml:
            print(f"Failed to extract TEI XML for {pdf_path}")
            return None, None, None, None

        # Extract metadata
        metadata = safe_execute(extract_metadata, pdf_path, "processHeaderDocument")
        title = metadata["title"] if metadata else "Title extraction failed."
        abstract = metadata["abstract"] if metadata else "Abstract extraction failed."
        references = safe_execute(extract_metadata, pdf_path, "processReferences") or []

        # Extract filtered sections
        filtered_sections = safe_execute(extract_filtered_sections_from_tei, tei_xml, HEAD_KEYWORDS)

        # Update keyword statistics
        keyword_match = False
        if filtered_sections:
            for keyword in HEAD_KEYWORDS:
                for section_title in filtered_sections.keys():
                    if keyword.lower() in section_title.lower():
                        stats["keyword_counts"][keyword] += 1
                        keyword_match = True
        if keyword_match:
            stats["papers_with_keywords"] += 1

        # Download references
        downloaded_references = []
        for ref_title in references:
            print(f"Searching and downloading: {ref_title}")
            random_delay = random.uniform(2, 5)
            print(f"Adding a delay of {random_delay:.2f} seconds before the next download.")
            time.sleep(random_delay)
            file_path = safe_execute(search_and_download_google_paper, ref_title, save_directory)
            if file_path:
                downloaded_references.append(file_path)

        return title, abstract, filtered_sections, downloaded_references

    except Exception as e:
        print(f"Error processing paper {pdf_path}: {e}")
        traceback.print_exc()
        return None, None, None, None

if __name__ == "__main__":
    import argparse

    # Command-line arguments
    parser = argparse.ArgumentParser(description="Process research papers and download references.")
    parser.add_argument("input_dir", type=str, help="Directory containing PDF papers.")
    parser.add_argument("save_dir", type=str, help="Directory to save extracted references.")
    args = parser.parse_args()

    # Create save directory if it doesn't exist
    os.makedirs(args.save_dir, exist_ok=True)

    # Process all PDF files in the input directory
    for filename in os.listdir(args.input_dir):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(args.input_dir, filename)
            print(f"Processing: {pdf_path}")

            stats["papers_processed"] += 1

            # Measure extraction time
            start_time = time.time()
            title, abstract, filtered_sections, downloaded_references = process_paper(pdf_path, args.save_dir)
            extraction_time = time.time() - start_time
            stats["extraction_times"].append(extraction_time)
            print(f"Extraction time: {extraction_time:.2f} seconds")

            # Measure download time
            start_time = time.time()
            if downloaded_references != None:
                for ref in downloaded_references:
                    stats["references_downloaded"] += 1
                download_time = time.time() - start_time
                stats["download_times"].append(download_time)

    # Display final statistics after processing
    display_statistics()
