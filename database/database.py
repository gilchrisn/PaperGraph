import os
import re
import json
import uuid
import argparse
import hashlib
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from grobid.grobid_paper_extractor import extract_metadata

# Load environment variables from .env file
load_dotenv()

# PostgreSQL Configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def sanitize_filename(title):
    """
    Sanitize the title to create a safe filename.

    :param title: Original title of the paper
    :return: Sanitized filename
    """
    if not title:
        return "untitled_paper"
    sanitized = re.sub(r'[^\w\s-]', '', title)  # Remove non-alphanumeric characters
    sanitized = re.sub(r'\s+', '_', sanitized.strip())  # Replace spaces with underscores
    return sanitized or "untitled_paper"


def generate_deterministic_uuid(title, authors):
    """
    Generate a deterministic UUID based on title and authors.

    :param title: Title of the paper (string)
    :param authors: List of author names (list of strings)
    :return: Deterministic UUID as a string
    """
    source = f"{title}|{','.join(authors)}"
    hash_value = hashlib.sha256(source.encode()).hexdigest()
    return str(uuid.UUID(hash_value[:32]))


def init_db_connection():
    """
    Initialize a PostgreSQL database connection.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("Connected to PostgreSQL database.")
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to the database: {e}")
        exit(1)


def process_file(file_path, conn):
    """
    Process a single PDF file, extract metadata, and insert it into PostgreSQL.
    """
    try:
        if not os.path.exists(file_path):
            print(f"File {file_path} not found. Skipping.")
            return

        # Extract metadata using Grobid
        paper_metadata = extract_metadata(file_path, "processHeaderDocument")
        if not paper_metadata:
            print(f"Metadata extraction failed for {file_path}. Reason: No metadata found. Moving to 'ocr_needed' directory.")

            # Move the file to the "ocr_needed" directory
            failed_dir = os.path.join(os.path.dirname(file_path), "ocr_needed")
            os.makedirs(failed_dir, exist_ok=True)
            os.rename(file_path, os.path.join(failed_dir, os.path.basename(file_path)))
            return
        elif paper_metadata.get("title") == "Title not found." or paper_metadata.get("abstract") == "Abstract not found.":
            print(f"Metadata extraction failed for {file_path}. Reason: Missing title or abstract. Moving to 'invalid' directory.")
            
            # Move the file to the "invalid" directory
            failed_dir = os.path.join(os.path.dirname(file_path), "invalid")
            os.makedirs(failed_dir, exist_ok=True)
            os.rename(file_path, os.path.join(failed_dir, os.path.basename(file_path)))
            return

        # Rename the file to the sanitized title
        sanitized_title = sanitize_filename(paper_metadata["title"])
        new_file_path = os.path.join(os.path.dirname(file_path), f"{sanitized_title}.pdf")
        if file_path != new_file_path:
            os.rename(file_path, new_file_path)
        file_path = new_file_path

        # Generate deterministic UUID
        authors = [author.full_name.strip() for author in paper_metadata.get("authors", [])]
        paper_id = generate_deterministic_uuid(paper_metadata["title"], authors)

        # Prepare the paper data
        paper_data = (
            paper_id,
            paper_metadata["title"].strip(),
            None if paper_metadata.get("doi") == "DOI not found." else paper_metadata["doi"].strip(),
            json.dumps(authors),
            file_path,
            None  # Embedding placeholder
        )

        # Insert into PostgreSQL
        with conn.cursor() as cursor:
            insert_query = """
                INSERT INTO papers (id, title, doi, authors, filepath, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
            """
            cursor.execute(insert_query, paper_data)
            conn.commit()
            print(f"Successfully inserted: {paper_metadata['title']}")

    except Exception as e:
        print(f"Error processing file {file_path}: {e}. Rolling back transaction.")
        conn.rollback()


def process_directory(directory, conn):
    """
    Process all PDF files in a directory.
    """
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory.")
        return

    pdf_files = [f for f in os.listdir(directory) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("No PDF files found in the directory.")
        return

    print(f"Found {len(pdf_files)} PDF files in {directory}. Starting processing...")
    for file in pdf_files:
        file_path = os.path.join(directory, file)
        process_file(file_path, conn)


if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process a directory of PDF papers and upload metadata to PostgreSQL.")
    parser.add_argument(
        "--directory", type=str, default=os.getenv("DIRECTORY_PATH"),
        help="Path to the directory containing PDF files. Defaults to DIRECTORY_PATH from .env."
    )
    args = parser.parse_args()

    # Initialize PostgreSQL connection
    connection = init_db_connection()

    # Process the given directory
    try:
        process_directory(args.directory, connection)
    finally:
        connection.close()
        print("Database connection closed.")
