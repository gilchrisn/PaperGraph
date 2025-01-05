from fastapi import HTTPException
from database import init_db_connection
from grobid.grobid_paper_extractor import extract_metadata
from compare_paper.similarity_computation import get_similarity
from fastapi import WebSocket

SIMILARITY_THRESHOLD = 0.88

def fetch_paper(cursor, paper_id: str):
    """
    Fetches a paper from the database by its ID.

    :param cursor: Database cursor
    :param paper_id: ID of the paper to fetch
    :return: Paper data as a dictionary or None if not found
    """
    cursor.execute("SELECT * FROM papers WHERE id = %s;", (paper_id,))
    return cursor.fetchone()

def fetch_or_insert_reference(cursor, source_paper_id: str, cited_paper_id: str):
    """
    Checks if a reference relationship exists, and if not, inserts it.

    :param cursor: Database cursor
    :param source_paper_id: ID of the source paper
    :param cited_paper_id: ID of the cited paper
    :return: Reference entry from the database if exists, None otherwise
    """
    cursor.execute(
        "SELECT * FROM reference WHERE source_paper_id = %s AND cited_paper_id = %s;",
        (source_paper_id, cited_paper_id)
    )
    ref_entry = cursor.fetchone()

    if not ref_entry:
        cursor.execute(
            "INSERT INTO reference (source_paper_id, cited_paper_id) VALUES (%s, %s);",
            (source_paper_id, cited_paper_id)
        )
    return ref_entry

def process_reference(cursor, root_paper_id: str, cited_paper_id: str, ref_paper, explored_papers: set):
    """
    Processes a single reference: checks relationships, computes similarity, and updates the database.

    :param cursor: Database cursor
    :param root_paper_id: ID of the root paper
    :param cited_paper_id: ID of the paper currently being explored
    :param ref_paper: Reference paper data
    :param explored_papers: Set of already explored paper IDs
    :return: Similarity score between the root paper and the reference paper
    """
    ref_id = ref_paper["id"]
    ref_entry = fetch_or_insert_reference(cursor, root_paper_id, ref_id)

    if ref_entry:
        if ref_entry.get("similarity_score") != None:
            return ref_entry.get("similarity_score")

    root_paper = fetch_paper(cursor, root_paper_id)
    if not root_paper or "filepath" not in root_paper:
        print(f"Root paper with ID {root_paper_id} not found")
        raise HTTPException(status_code=500, detail="Root paper filepath not found")

    similarity_score, relationship_type, remarks = get_similarity(
        root_paper["filepath"], ref_paper["filepath"]
    )

    cursor.execute(
        """
        INSERT INTO reference (source_paper_id, cited_paper_id, relationship_type, remarks, similarity_score)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (source_paper_id, cited_paper_id) DO UPDATE
        SET relationship_type = EXCLUDED.relationship_type,
            remarks = EXCLUDED.remarks,
            similarity_score = EXCLUDED.similarity_score;
        """,
        (root_paper_id, ref_id, relationship_type, remarks, float(similarity_score))
    )

    explored_papers.add(ref_id)
    return similarity_score

def process_references(cursor, root_paper_id: str, cited_paper_id: str, explored_papers: set):
    """
    Processes all references of a given paper.

    :param cursor: Database cursor
    :param root_paper_id: ID of the root paper
    :param cited_paper_id: ID of the paper whose references are being processed
    :param explored_papers: Set of already explored paper IDs
    :return: List of references that meet the similarity threshold
    """
    paper = fetch_paper(cursor, cited_paper_id)
    if not paper:
        # TODO: handle missing paper
        # for now we will log the error and return an empty list
        print(f"Paper with ID {cited_paper_id} not found")
        return []
    
    reference_titles = extract_metadata(paper["filepath"], "processReferences")
    reference_ids = {}

    if (reference_titles is None) or (len(reference_titles) == 0):
        print(f"Paper Title: {paper['title']} has no references")

    for reference in reference_titles:
        # Use PostgreSQL trigram similarity to find matching papers
        cursor.execute(
            """
            SELECT *, similarity(title, %s) AS similarity
            FROM papers
            WHERE similarity(title, %s) > 0.5
            ORDER BY similarity DESC
            LIMIT 1;
            """,
            (reference, reference)
        )
        ref_paper = cursor.fetchone()

        if ref_paper and ref_paper["id"] not in explored_papers:
            similarity_score = process_reference(cursor, root_paper_id, cited_paper_id, ref_paper, explored_papers)

            if similarity_score < SIMILARITY_THRESHOLD:
                explored_papers.add(ref_paper["id"])

            reference_ids[ref_paper["id"]] = similarity_score

    return reference_ids

# def get_related_papers(root_paper_id: str, cited_paper_id: str, explored_papers: set = None, max_depth: int = 5, current_depth: int = 0):
#         """
#         Retrieve related papers using exploration (references traversal) and update relationships incrementally.

#         :param root_paper_id: ID of the root paper
#         :param cited_paper_id: ID of the starting paper for this exploration
#         :param explored_papers: Set of already explored paper IDs
#         :param max_depth: Maximum depth to traverse
#         :param current_depth: Current depth of traversal
#         :return: Status and list of explored papers
#         """
#         if explored_papers is None:
#             explored_papers = set()

#         if current_depth > max_depth:
#             return {"status": "Max exploration depth reached", "explored_papers": list(explored_papers)}

#         try:
#             with init_db_connection() as conn:
#                 conn.autocommit = False

#                 with conn.cursor() as cursor:
#                     explored_papers.add(cited_paper_id)
#                     reference_ids = process_references(cursor, root_paper_id, cited_paper_id, explored_papers)

#                     for ref_id, similarity_score in reference_ids.items():
#                         if ref_id not in explored_papers:
#                             print(f"Exploring reference {ref_id} with similarity score {similarity_score}")
                

#                     conn.commit()

#                     for ref_id in reference_ids.keys():
#                         if ref_id not in explored_papers:
#                             get_related_papers(root_paper_id, ref_id, explored_papers, max_depth, current_depth + 1)

#             return {"status": "Exploration completed", "explored_papers": list(explored_papers)}

#         except Exception as e:
#             print(f"An error occurred during exploration: {e}")
#             raise HTTPException(status_code=500, detail=str(e))

async def get_related_papers(
    websocket: WebSocket,
    root_paper_id: str,
    cited_paper_id: str,
    explored_papers: set = None,
    max_depth: int = 5,
    current_depth: int = 0,
):
    """
    Real-time exploration of related papers with WebSocket updates.
    """
    if explored_papers is None:
        explored_papers = set()

    if current_depth > max_depth:
        await websocket.send_json({"status": "Max exploration depth reached"})
        return

    try:
        with init_db_connection() as conn:
            conn.autocommit = False
            with conn.cursor() as cursor:
                explored_papers.add(cited_paper_id)

                # Process references for the current paper
                reference_ids = process_references(cursor, root_paper_id, cited_paper_id, explored_papers)

                # Commit after processing references
                conn.commit()

                # Prepare nodes
                nodes = [
                    {"id": cited_paper_id, "label": fetch_paper(cursor, cited_paper_id)["title"], "similarity_score": reference_ids[cited_paper_id]}
                    for cited_paper_id in reference_ids.keys()
                ]
                nodes.append({"id": root_paper_id, "label": fetch_paper(cursor, root_paper_id)["title"], "similarity_score": 1.0})

                # Send incremental update for the current paper
                await websocket.send_json({
                    "nodes": nodes,
                    "links": [{"source": cited_paper_id, "target": ref_id} for ref_id in reference_ids.keys()],
                })

                # Recursively explore references
                for ref_id in reference_ids:
                    if ref_id not in explored_papers and reference_ids[ref_id] >= SIMILARITY_THRESHOLD:
                        await get_related_papers(
                            websocket, root_paper_id, ref_id, explored_papers, max_depth, current_depth + 1
                        )

    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
if __name__ == "__main__":
    root_paper_id = "20c2d916-9e7c-b52a-7555-2d2f094f2f21"
    cited_paper_id = "20c2d916-9e7c-b52a-7555-2d2f094f2f21"
    result = get_related_papers(root_paper_id, cited_paper_id)
    print(result)
