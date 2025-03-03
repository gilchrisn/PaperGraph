from fastapi import APIRouter, HTTPException, Query, WebSocket
from fastapi.responses import FileResponse
from paper_service import PaperService
from paper_search.semantic_scholar import search_papers_by_title, process_and_cite_paper
import os

router = APIRouter()

# Initialize the service instance
paper_service = PaperService()

# 1. Get All Papers
@router.get("/papers/", tags=["Papers"])
def get_all_papers():
    """
    Retrieve all papers from the database.
    """
    try:
        papers = paper_service.get_all_papers()
        if not papers:
            raise HTTPException(status_code=404, detail="No papers found")
        return {"papers": papers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 2. Get Paper by Title
@router.get("/papers/search/", tags=["Papers"])
def search_paper_by_title(title: str = Query(..., description="Paper title to search")):
    """
    Retrieve papers by title from semantic scholar. Return top 5 results.
    """
    print("Searching for papers with title:", title)
    try:
        papers = search_papers_by_title(title, limit=5)
        if not papers:
            raise HTTPException(status_code=404, detail=f"No papers found for title '{title}'")
        print(papers.keys())
        return {"papers": papers['data']} if papers['data'] else {"papers": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
# 3. Get a Specific Paper by ID
@router.get("/papers/{paper_id}", tags=["Papers"])
def get_paper_by_id(paper_id: str):
    """
    Retrieve a specific paper by its ID. If paper doesn't exist, use download_paper_and_create_record method, then return the paper.
    """
    try:
        paper = paper_service.get_paper_by_id(paper_id)
        if not paper:
            # Download the paper and create a record in the database
            paper_service.download_paper_and_create_record(paper_id)
            paper = paper_service.get_paper_by_id(paper_id)
            if not paper:
                raise HTTPException(status_code=404, detail=f"Paper with ID '{paper_id}' not found")
        return {"paper": paper}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Exploration Method
@router.websocket("/papers/{paper_id}/explore/")
async def explore_paper(
    websocket: WebSocket,
    paper_id: str,
    max_depth: int = Query(5),  
    similarity_threshold: float = Query(0.88),
    traversal_type: str = Query("bfs")
):
    await websocket.accept()
    try:
        await paper_service.explore_paper(
            websocket, 
            root_paper_id=paper_id, 
            start_paper_id=paper_id,
            max_depth=max_depth, 
            similarity_threshold=similarity_threshold,
            traversal_type=traversal_type,
        )
    except Exception as e:
        await websocket.send_json({"status": "error", "message": str(e)})
    finally:
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
        file_path = paper_service.get_pdf_path(paper_id) 
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")
        return FileResponse(
            file_path,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={paper_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
