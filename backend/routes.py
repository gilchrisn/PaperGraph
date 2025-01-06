from fastapi import APIRouter, HTTPException, Query
from database import init_db_connection
from fastapi import FastAPI
from fastapi.websockets import WebSocket
from paper_service import get_related_papers
from fastapi.responses import FileResponse
import os

app = FastAPI()
router = APIRouter()

# Include the router in the FastAPI app
app.include_router(router)

# 1. Get All Papers
@router.get("/papers/", tags=["Papers"])
def get_all_papers():
    """
    Retrieve all papers from the database.
    """
    try:
        with init_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM papers;")
                papers = cursor.fetchall()
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
        with init_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM papers WHERE title ILIKE %s;", (f"%{title}%",))
                papers = cursor.fetchall()
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
        with init_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM papers WHERE id = %s;", (paper_id,))
                paper = cursor.fetchone()
        if not paper:
            raise HTTPException(status_code=404, detail=f"Paper with ID '{paper_id}' not found")
        return {"paper": paper}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# 4. Exploration Method
@router.websocket("/papers/{paper_id}/explore/")
async def explore_paper(websocket: WebSocket, paper_id: str):
    await websocket.accept()
    try:
        # Start the exploration process with WebSocket updates
        await get_related_papers(websocket, paper_id, paper_id)
    except Exception as e:
        # Handle errors gracefully
        await websocket.send_json({"status": "error", "message": str(e)})
    finally:
        # Close the WebSocket connection
        await websocket.close()


# 5. Search Method (Placeholder)
@router.get("/papers/{paper_id}/search/", tags=["Search"])
def search_similar_papers(paper_id: str):
    """
    Placeholder for search method to retrieve similar papers based on embeddings.
    """
    return {"message": "This feature is under development.", "paper_id": paper_id}

# 6. Get Paper PDF
@router.get("/papers/{paper_id}/pdf/", tags=["Papers"])
def fetch_pdf(paper_id: str):
    """
    Retrieve the PDF file for a specific paper.
    """

    try:
        with init_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT filepath FROM papers WHERE id = %s;", (paper_id,))
                pdf_path = cursor.fetchone()["filepath"]
        if not pdf_path:
            raise HTTPException(status_code=404, detail=f"PDF for paper with ID '{paper_id}' not found")
        
        file_path = os.path.join(os.getcwd(), pdf_path)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"PDF file not found")
        
        return FileResponse(
            file_path,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={paper_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))