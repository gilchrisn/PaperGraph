import re
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import argparse
import time
from PyPDF2 import PdfReader

# Sanitize title for file naming to prevent directory issues
def sanitize_title(title):
    # Remove invalid characters and replace them with underscores
    return re.sub(r'[<>:"/\\|?*]', '_', title)

def search_and_download_google_paper(title, save_directory, min_pages=2, max_pages=50, max_results=50):
    print(f"Searching for: {title}")
    from selenium.webdriver.chrome.options import Options

    # # Configure Chrome options
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run in headless mode

    # Initialize the WebDriver with options
    driver = webdriver.Chrome()

    try:
        # Step 1: Open Google
        driver.get("https://www.google.com")

        # Step 2: Accept cookies if needed (depends on location)
        try:
            consent_button = driver.find_element(By.XPATH, '//button[contains(text(),"I agree")]')
            consent_button.click()
        except Exception:
            print("No consent button found or click failed.")

        # Step 3: Search for the paper title
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(title + " pdf")  # Adding 'pdf' increases chance of finding downloadable papers
        search_box.send_keys(Keys.RETURN)

        # Use explicit wait for search results to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//a')))

        # Step 4: Extract and visit links with retry for stale element references
        while True:
            try:
                links = driver.find_elements(By.XPATH, '//a')
                print(f"Found {len(links)} links on the page.")

                # Limit to max_results number of links
                for index, link in enumerate(links[:max_results]):
                    url = link.get_attribute('href')
                    if url:
                        print(f"Checking URL #{index + 1}: {url}")
                        # Check if the URL ends with ".pdf" instead of just containing "pdf"
                        if url.lower().endswith(".pdf"):
                            print(f"Attempting to download from: {url}")
                            file_path = download_paper_from_url(url, save_directory, title, min_pages, max_pages)
                            if file_path:
                                print(f"Successfully downloaded: {title}")
                                print(f"Download link: {url}")
                                return file_path  # Return the path to the downloaded PDF file
                print(f"No PDF link found for '{title}' in the top {max_results} results.")
                return None  # Return None if no PDF link found within the limit
            except StaleElementReferenceException:
                print("Encountered stale element, retrying...")
                time.sleep(1)
                continue  # Refetch elements if stale element error occurs
    finally:
        driver.quit()

def download_paper_from_url(url, save_directory, title, min_pages, max_pages):
    try:
        # Make sure the save directory exists
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        # Sanitize title for file naming using `sanitize_title`
        sanitized_title = sanitize_title(title)
        file_path = os.path.join(save_directory, f"{sanitized_title}.pdf")

        # Download the PDF file
        response = requests.get(url, stream=True)
        if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
            with open(file_path, "wb") as file:
                file.write(response.content)

            # Check the number of pages in the downloaded PDF
            num_pages = get_pdf_page_count(file_path)
            if num_pages and min_pages <= num_pages <= max_pages:
                print(f"Downloaded '{sanitized_title}' with {num_pages} pages to '{file_path}'")
                return file_path  # Return the path to the downloaded file
            else:
                print(f"PDF '{sanitized_title}' has {num_pages} pages, outside the range {min_pages}-{max_pages}. Skipping...")
                os.remove(file_path)  # Remove the file if it doesn't meet the criteria
                return None
        else:
            print(f"Failed to download from {url}, status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred while downloading: {e}")
        return None

def get_pdf_page_count(file_path):
    try:
        reader = PdfReader(file_path)
        return len(reader.pages)
    except Exception as e:
        print(f"Failed to read PDF '{file_path}': {e}")
        return None

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Search and download a paper by title.")
    parser.add_argument("title", type=str, help="The title of the paper to search for.")
    parser.add_argument("directory", type=str, help="The directory where the PDF should be saved.")
    parser.add_argument("--min_pages", type=int, default=2, help="Minimum number of pages for the PDF (default: 2).")
    parser.add_argument("--max_pages", type=int, default=30, help="Maximum number of pages for the PDF (default: 30).")
    parser.add_argument("--max_results", type=int, default=50, help="Maximum number of search results to check (default: 50).")

    # Parse the arguments
    args = parser.parse_args()

    # Run the search and download function with the provided title and directory
    pdf_path = search_and_download_google_paper(args.title, args.directory, args.min_pages, args.max_pages, args.max_results)
    if pdf_path:
        print(f"PDF successfully downloaded to: {pdf_path}")
    else:
        print("No PDF found or downloaded.")
