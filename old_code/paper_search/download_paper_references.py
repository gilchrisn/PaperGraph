import os
import time
import random
import traceback
import argparse
import signal
from paper_search.get_research_paper import search_and_download_google_paper
from grobid.grobid_paper_extractor import extract_metadata

def safe_execute(func, *args, **kwargs):
    """Execute a function safely, catching and logging exceptions."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Error during {func.__name__}: {e}")
        traceback.print_exc()
        return None

def save_progress(last_processed, current_reference, reference_list):
    """Save the name of the last processed file and reference to a checkpoint file."""
    # Save progress checkpoint
    with open("resources/checkpoints/progress_checkpoint.txt", "w", encoding="utf-8") as checkpoint:
        checkpoint.write(f"{last_processed}\n{current_reference}\n")
    
    # Save reference list checkpoint
    with open("resources/checkpoints/reference_list_checkpoint.txt", "w", encoding="utf-8") as ref_list_file:
        ref_list_file.write("\n".join(reference_list))

def load_progress():
    """Load the name of the last processed file and reference from a checkpoint file."""
    last_processed, current_reference = None, None
    if os.path.exists("resources/checkpoints/progress_checkpoint.txt"):
        with open("resources/checkpoints/progress_checkpoint.txt", "r") as checkpoint:
            lines = checkpoint.readlines()
            if lines:
                last_processed = lines[0].strip()
                if len(lines) > 1:
                    current_reference = lines[1].strip()
    reference_list = []
    if os.path.exists("resources/checkpoints/reference_list_checkpoint.txt"):
        with open("resources/checkpoints/reference_list_checkpoint.txt", "r") as ref_list_file:
            reference_list = [line.strip() for line in ref_list_file.readlines()]
    return last_processed, current_reference, reference_list

def signal_handler(sig, frame):
    """Handle interruption signal to save progress."""
    print("\nProcess interrupted. Saving progress...")
    save_progress(current_paper, current_reference, remaining_references)
    print("Progress saved. Exiting.")
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract references from papers and download them.")
    parser.add_argument("papers_dir", type=str, help="Directory containing PDF papers.")
    parser.add_argument("save_dir", type=str, help="Directory to save downloaded references.")
    args = parser.parse_args()

    # Ensure save directory exists
    os.makedirs(args.save_dir, exist_ok=True)

    # Load the last processed file, reference, and reference list
    last_processed, current_reference, reference_list = load_progress()
    process_next = last_processed is None

    current_paper = None
    remaining_references = []

    # Process each PDF in the papers directory
    for file in os.listdir(args.papers_dir):
        if file.endswith(".pdf"):
            if not process_next:
                if file == last_processed:
                    process_next = True
                else: 
                    continue

            current_paper = file
            print(f"Processing paper: {file}")
            references = safe_execute(extract_metadata, os.path.join(args.papers_dir, file), "processReferences")

            if references:
                # Resume from the last incomplete reference if applicable
                if reference_list:
                    references = reference_list
                remaining_references = references

                for ref in list(references):  # Iterate over a copy of the references list
                    if current_reference and ref != current_reference:
                        continue  # Skip references until we reach the last saved one

                    current_reference = ref
                    print(f"Parent paper: {file}")
                    print(f"Downloading reference: {ref}")

                    # Save progress
                    save_progress(file, ref, references)

                    # Optional delay to respect rate limits, etc.
                    random_delay = random.uniform(2, 5)
                    print(f"Adding a delay of {random_delay:.2f} seconds before download.")
                    time.sleep(random_delay)

                    success = safe_execute(search_and_download_google_paper, ref, args.save_dir)
                    if success:
                        references.remove(ref)  # Remove from the original list after successful download
                    else:
                        print(f"Failed to download reference: {ref}")

                    current_reference = None  # Reset after successfully downloading

                # Clear reference list after all references are processed
                reference_list = []
                remaining_references = []
                save_progress(file, None, reference_list)

    print("Processing complete. Checkpoint file saved.")
