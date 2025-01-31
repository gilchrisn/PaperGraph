from paper_service import PaperService
from paper_repository import PaperRepository
from grobid.grobid_paper_extractor import extract_metadata

# Get all paper in the database

# For each paper:
    # Get all the reference titles, call it references_1
    
    # For each reference title:
        # Search for the reference in the database, call it references_2

        # Check if an entry of reference_1, reference_2 exist in the reference table
        # If not, create a new entry in the reference table
        # If yes, skip

paper_service = PaperService()
paper_repository = PaperRepository()

papers = paper_service.get_all_papers()
invalid_references = []
error_references = []

for i, paper in enumerate(papers):
    print(f"Processing paper {i + 1}/{len(papers)}")
    paper_path = paper["filepath"]

    paper_references = extract_metadata(paper_path, "processReferences")

    if not paper_references:
        print("No references found for paper", paper["title"])
        continue

    for reference in paper_references:
        reference_paper = paper_repository.find_similar_papers_by_title(reference)

        try:
            
            if reference_paper:
                reference_id = reference_paper["id"]
                
                paper_service.fetch_or_insert_reference(paper["id"], reference_id)

                print("Reference inserted successfully.")
            else:
                print("Reference not found in the database.")
                invalid_references.append(reference)
        except Exception as e:
            print("Error inserting reference:", e)
            error_references.append(reference)

print(len(invalid_references), "references not found in the database.")
print("Invalid references:", invalid_references)

print(len(error_references), "references failed to insert.")
print("Error references:", error_references)