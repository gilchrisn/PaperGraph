from fastapi import APIRouter, HTTPException, Query
from database import init_db_connection

router = APIRouter()

# 1. Get All Papers
@router.get("/papers/", tags=["Papers"])
def get_all_papers():
    """
    Retrieve all papers from the database.
    """
    try:
        conn = init_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM papers;")
            papers = cursor.fetchall()
        conn.close()
        if not papers:
            raise HTTPException(status_code=404, detail="No papers found")
        return {"papers": papers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 2. Get Paper by Title
@router.get("/papers/search/", tags=["Papers"])
def search_paper_by_title(title: str = Query(..., description="Paper title to search")):
    """
    Retrieve papers by title.
    """
    try:
        conn = init_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM papers WHERE title ILIKE %s;", (f"%{title}%",))
            papers = cursor.fetchall()
        conn.close()
        if not papers:
            raise HTTPException(status_code=404, detail="Paper not found")
        return {"papers": papers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 3. Get a Specific Paper by ID
@router.get("/papers/{paper_id}", tags=["Papers"])
def get_paper_by_id(paper_id: str):
    """
    Retrieve a specific paper by its ID.
    """
    try:
        conn = init_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM papers WHERE id = %s;", (paper_id,))
            paper = cursor.fetchone()
        conn.close()
        if not paper:
            raise HTTPException(status_code=404, detail=f"Paper with ID '{paper_id}' not found")
        return {"paper": paper}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 4. Exploration Method
@router.get("/papers/{paper_id}/explore/", tags=["Exploration"])
def get_related_papers(paper_id: str):
    """
    Retrieve related papers using exploration (references traversal).
    """
    try:
        conn = init_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT citations FROM papers WHERE id = %s;", (paper_id,))
            citations = cursor.fetchone()
        conn.close()
        if not citations or citations[0] is None:
            raise HTTPException(status_code=404, detail="No references found for this paper")
        return {"paper_id": paper_id, "related_papers": citations[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 5. Search Method (Placeholder)
@router.get("/papers/{paper_id}/search/", tags=["Search"])
def search_similar_papers(paper_id: str):
    """
    Placeholder for search method to retrieve similar papers based on embeddings.
    """
    return {"message": "This feature is under development.", "paper_id": paper_id}
