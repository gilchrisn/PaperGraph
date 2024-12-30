import os
import time
import random
import traceback
import argparse
from get_research_paper import search_and_download_google_paper

def safe_execute(func, *args, **kwargs):
    """Execute a function safely, catching and logging exceptions."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Error during {func.__name__}: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download papers from a list of titles.")
    parser.add_argument("titles_file", type=str, help="Path to the text file containing paper titles.")
    parser.add_argument("save_dir", type=str, help="Directory to save downloaded papers.")
    args = parser.parse_args()

    # Ensure save directory exists
    os.makedirs(args.save_dir, exist_ok=True)

    # Read the titles from the file
    with open(args.titles_file, "r", encoding="utf-8") as f:
        titles = [line.strip() for line in f if line.strip()]

    # Download each paper
    for title in titles:
        print(f"Downloading paper: {title}")

        # Optional delay to respect rate limits, etc.
        random_delay = random.uniform(2, 5)
        print(f"Adding a delay of {random_delay:.2f} seconds before download.")
        time.sleep(random_delay)

        file_path = safe_execute(search_and_download_google_paper, title, args.save_dir)
        if file_path:
            print(f"Downloaded '{title}' successfully.")
        else:
            print(f"Failed to download '{title}'.")
