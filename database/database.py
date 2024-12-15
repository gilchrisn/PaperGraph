import os
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
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "papergraph")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "your_password_here")


def generate_deterministic_uuid(title, authors):
    """
    Generate a deterministic UUID based on title and authors.

    :param title: Title of the paper (string)
    :param authors: List of author names (list of strings)
    :return: Deterministic UUID as a string
    """
    # Concatenate the title and sorted author list for consistency
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
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        exit(1)


def process_file(file_path, conn):
    """
    Process a single PDF file, extract metadata, and insert it into PostgreSQL.
    """
    try:
        # Extract metadata using Grobid
        paper_metadata = extract_metadata(file_path, "processHeaderDocument")
        if not paper_metadata:
            print(f"Warning: Metadata extraction failed for {file_path}")
            return
        
        # Generate deterministic UUID
        authors = [author.full_name.strip() for author in paper_metadata.get("authors", [])]
        paper_id = generate_deterministic_uuid(paper_metadata["title"], authors)

        # Prepare the paper data
        paper_data = (
            paper_id,
            paper_metadata["title"].strip(),
            paper_metadata["abstract"].strip(),
            None if paper_metadata["doi"] == "DOI not found." else paper_metadata["doi"].strip(),
            json.dumps(authors),
            json.dumps(paper_metadata.get("citations", [])),
            file_path,
            None  # Embedding placeholder
        )

        # Insert into PostgreSQL
        with conn.cursor() as cursor:
            insert_query = """
                INSERT INTO papers (id, title, abstract, doi, authors, citations, filepath, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING;
            """
            cursor.execute(insert_query, paper_data)
            conn.commit()
            print(f"Successfully inserted: {paper_metadata['title']}")

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        conn.rollback()


def process_directory(directory, conn):
    """
    Process all PDF files in a directory.
    """
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory.")
        return

    pdf_files = [f for f in os.listdir(directory) if f.endswith(".pdf")]
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
