import os
import time
import random
import signal
import traceback
import argparse
from grobid.grobid_paper_extractor import extract_tei_from_pdf, extract_filtered_sections_from_tei, extract_metadata

# Define the GROBID server URL (adjust if needed)
GROBID_BASE_URL = "http://localhost:8070/api"

# Keywords for filtering section titles
HEAD_KEYWORDS = ["evaluation", "methodology", "related work", "conclusion", "baseline"]

# Statistics dictionary
stats = {
    "papers_processed": 0,
    "extraction_times": [],
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
    total_papers = stats["papers_processed"]
    avg_extraction_time = total_extraction_time / max(total_papers, 1)

    print("\nSummary Statistics:")
    print(f"Papers Processed: {stats['papers_processed']}")
    print(f"Total Extraction Time: {total_extraction_time:.2f} seconds")
    print(f"Average Extraction Time per Paper: {avg_extraction_time:.2f} seconds")
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

def process_paper(pdf_path):
    """Process a single paper: extract metadata and filtered sections (no downloading references)."""
    try:
        # Extract TEI XML
        tei_xml = safe_execute(extract_tei_from_pdf, pdf_path)
        if not tei_xml:
            print(f"Failed to extract TEI XML for {pdf_path}")
            return None, None, None, None

        # Extract metadata
        metadata = safe_execute(extract_metadata, pdf_path, "processHeaderDocument")
        title = metadata["title"] if metadata and "title" in metadata else "Title extraction failed."
        abstract = metadata["abstract"] if metadata and "abstract" in metadata else "Abstract extraction failed."

        references_data = safe_execute(extract_metadata, pdf_path, "processReferences") or []

        # Extract filtered sections
        filtered_sections = safe_execute(extract_filtered_sections_from_tei, tei_xml, HEAD_KEYWORDS)

        print(filtered_sections)

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

        # Just return extracted metadata (no downloads)
        return title, abstract, filtered_sections, references_data

    except Exception as e:
        print(f"Error processing paper {pdf_path}: {e}")
        traceback.print_exc()
        return None, None, None, None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract metadata (title, abstract, references) from research papers without downloading references.")
    parser.add_argument("input_dir", type=str, help="Directory containing PDF papers.")
    args = parser.parse_args()

    # Process all PDF files in the input directory
    pdf_files = [f for f in os.listdir(args.input_dir) if f.lower().endswith(".pdf")]

    for filename in pdf_files:
        pdf_path = os.path.join(args.input_dir, filename)
        print(f"Processing: {pdf_path}")

        stats["papers_processed"] += 1

        # Measure extraction time (metadata + sections)
        start_extraction = time.time()
        title, abstract, filtered_sections, references_data = process_paper(pdf_path)
        extraction_time = time.time() - start_extraction
        stats["extraction_times"].append(extraction_time)
        print(f"Extraction time: {extraction_time:.2f} seconds")

        # Optionally, you can print out the extracted data for verification
        print(f"Title: {title}")
        print(f"Abstract: {abstract}")
        if references_data:
            print(f"Number of References: {len(references_data)}")
        if filtered_sections:
            print("Filtered Sections:")
            for sec_title, sec_content in filtered_sections.items():
                print(f"  {sec_title}")

    # Display final statistics after processing
    display_statistics()
