import os
import time
from paper_search.paper_search import search_and_download_single_paper
from grobid.grobid_paper_extractor import extract_reference_titles

def download_referenced_papers(initial_title, save_directory):
    """
    Given a paper title, download the paper PDF, extract references, and download PDFs of all references.
    
    Parameters:
        initial_title (str): The title of the starting paper.
        save_directory (str): Directory to save all downloaded PDFs.
    
    Returns:
        dict: A dictionary with keys as paper titles and values as paths to the downloaded PDFs.
    """
    # Dictionary to store downloaded papers and their paths
    downloaded_papers = {}

    # Step 1: Download the initial paper
    print(f"Searching and downloading the initial paper: '{initial_title}'")
    initial_pdf_path = search_and_download_single_paper(initial_title, save_directory)
    
    if not initial_pdf_path:
        print(f"Failed to download the initial paper: '{initial_title}'")
        return downloaded_papers  # Exit if the initial paper can't be downloaded

    # Store the initial paper path
    downloaded_papers[initial_title] = initial_pdf_path
    print(f"Downloaded initial paper: '{initial_title}' -> {initial_pdf_path}")

    # Step 2: Extract references from the initial paper
    print("Extracting references from the initial paper...")
    reference_titles = extract_reference_titles(initial_pdf_path)
    
    if not reference_titles or reference_titles == ["No reference titles found."]:
        print(f"No references found in the initial paper: '{initial_title}'")
        return downloaded_papers  # Exit if no references are found

    print(f"Found {len(reference_titles)} references in the initial paper.")

    # Step 3: Download each referenced paper
    for ref_title in reference_titles:
        print(f"\nSearching and downloading referenced paper: '{ref_title}'")
        ref_pdf_path = search_and_download_single_paper(ref_title, save_directory)
        
        if ref_pdf_path:
            # Store each successfully downloaded reference
            downloaded_papers[ref_title] = ref_pdf_path
            print(f"Downloaded referenced paper: '{ref_title}' -> {ref_pdf_path}")
        else:
            print(f"Failed to download referenced paper: '{ref_title}'")
        
        # Adding a short delay to avoid overwhelming the search services
        time.sleep(2)

    return downloaded_papers

# Example usage
if __name__ == "__main__":
    initial_paper_title = "GPU-based Graph Traversal on Compressed Graphs"
    save_dir = "prototype_test_v2"

    # Ensure the save directory exists
    os.makedirs(save_dir, exist_ok=True)

    # Download the initial paper and its references
    all_downloaded_papers = download_referenced_papers(initial_paper_title, save_dir)

    # Print summary of downloaded papers
    print("\nSummary of Downloaded Papers:")
    for title, path in all_downloaded_papers.items():
        print(f"'{title}' -> {path}")
