from fastapi import HTTPException, WebSocket
from grobid.grobid_paper_extractor import extract_metadata
from compare_paper.similarity_computation import get_similarity
import os
from paper_repository import PaperRepository
from util.frontier import Queue, PriorityQueue, Stack

class PaperService:
    def __init__(self):
        self.repository = PaperRepository()

    def get_all_papers(self):
        """
        Fetch all papers from the database.
        """
        return self.repository.get_all_papers()

    def search_paper_by_title(self, title: str):
        """
        Search for papers by title.
        """
        return self.repository.get_papers_by_title(title)

    def get_paper_by_id(self, paper_id: str):
        """
        Fetch a specific paper by ID.
        """
        return self.repository.get_paper_by_id(paper_id)

    def get_pdf_path(self, paper_id: str):
        """
        Get the file path for a paper's PDF.
        """
        path = self.repository.get_pdf_path_by_id(paper_id)
        return os.path.join(os.getcwd(), path) if path else None

    def fetch_or_insert_reference(self, source_paper_id: str, cited_paper_id: str):
        """
        Fetch or insert a reference relationship into the database.
        """
        ref_entry = self.repository.get_reference_by_paper_ids(source_paper_id, cited_paper_id)
        if not ref_entry:
            self.repository.insert_reference(source_paper_id, cited_paper_id, None, None, None)
        return self.repository.get_reference_by_paper_ids(source_paper_id, cited_paper_id)

    def process_reference(self, root_paper_id: str, ref_paper: dict, explored_papers: set):
        """
        Process a single reference: check relationships, compute similarity, and update the database.
        """
        print("checkpoint 3")
        ref_id = ref_paper["id"]
        ref_entry = self.fetch_or_insert_reference(root_paper_id, ref_id)

        print("checkpoint 4")
        print(ref_entry)
        print(type(ref_entry))
        print(ref_entry["similarity_score"])
        if ref_entry and ref_entry["similarity_score"] is not None:
            print("checkpoint 4.1")
            return ref_entry["similarity_score"], ref_entry["relationship_type"], ref_entry["remarks"]

        print("checkpoint 5")
        root_paper = self.repository.get_paper_by_id(root_paper_id)
        if not root_paper or "filepath" not in root_paper:
            raise HTTPException(status_code=500, detail="Root paper filepath not found")


        print("checkpoint 6")
        similarity_score, relationship_type, remarks = get_similarity(
            root_paper["filepath"], ref_paper["filepath"]
        )
        print("checkpoint 7")
        self.repository.insert_reference(root_paper_id, ref_id, relationship_type, remarks, float(similarity_score))
        explored_papers.add(ref_id)


        print("checkpoint 8")
        return similarity_score, relationship_type, remarks

    def process_references(self, root_paper_id: str, cited_paper_id: str, explored_papers: set, similarity_threshold = 0.88):
        """
        Process all references of a given paper.
        """
        print(f"Processing references for paper ID: {cited_paper_id}")
        paper = self.repository.get_paper_by_id(cited_paper_id)
        if not paper:
            print(f"Paper with ID {cited_paper_id} not found")
            return {}
        print("checkpoint 1")

        reference_titles = extract_metadata(paper["filepath"], "processReferences")
        if not reference_titles:
            print(f"Paper Title: {paper['title']} has no references")
            return {}

        print("checkpoint 2")
        reference_ids = {}
        for reference in reference_titles:
            print("checkpoint 2.1")
            ref_paper = self.repository.find_similar_papers_by_title(reference, 0.5)
    
            if ref_paper and ref_paper["id"] not in explored_papers:
                similarity_score, relationship_type, remarks = self.process_reference(root_paper_id, ref_paper, explored_papers)
                print("checkpoint 9")
                if similarity_score < similarity_threshold:
                    print("checkpoint 9.1")
                    explored_papers.add(ref_paper["id"])
                    print("checkpoint 9.2")
                reference_ids[ref_paper["id"]] = {"similarity_score": similarity_score, "relationship_type": relationship_type, "remarks": remarks}
                print("checkpoint 9.3")
        print("checkpoint 10")
        return reference_ids

    async def explore_paper(
            self, websocket: WebSocket, 
            root_paper_id: str, 
            cited_paper_id: str, 
            explored_papers: set = None, 
            frontier = None,
            max_depth: int = 5, 
            current_depth: int = 0, 
            similarity_threshold = 0.88,
            traversal_type = "bfs"
            ):
        """
        Real-time exploration of related papers with WebSocket updates.

        Parameters:
            websocket (WebSocket): WebSocket connection for real-time updates.
            root_paper_id (str): ID of the root paper for the exploration.
            cited_paper_id (str): ID of the current paper being explored.
            explored_papers (set, optional): Set of papers already explored. Defaults to None.
            frontier (Queue|Stack|PriorityQueue, optional): Data structure for managing traversal. Defaults to None.
            max_depth (int): Maximum depth of exploration. Defaults to 5.
            current_depth (int): Current depth of exploration. Defaults to 0.
            similarity_threshold (float): Threshold for similarity scores. Defaults to SIMILARITY_THRESHOLD.
            traversal_type (str): Type of traversal ('bfs', 'dfs', 'priority'). Defaults to "bfs".

        Returns:
            None
        """

        if traversal_type not in ["bfs", "dfs", "priority"]:
            raise ValueError("Invalid traversal_type. Use 'bfs', 'dfs', or 'priority'.")
        
        if explored_papers is None:
            explored_papers = set()

        if frontier is None:
            frontier = Queue() if traversal_type == "bfs" else Stack() if traversal_type == "dfs" else PriorityQueue(lambda x: -x['similarity_score'])
  
        if cited_paper_id in explored_papers:
            return

        if current_depth > max_depth:
            await websocket.send_json({"status": "Max exploration depth reached"})
            return

        try:
            explored_papers.add(cited_paper_id)
            reference_ids = self.process_references(root_paper_id, cited_paper_id, explored_papers, similarity_threshold)

            print("checkpoint 11")
            nodes = [{
                    "id": ref_id,
                    "title": self.repository.get_paper_by_id(cited_paper_id)["title"],
                    "similarity_score": float(ref_data["similarity_score"]),
                    "relationship_type": ref_data["relationship_type"],
                    "remarks": ref_data["remarks"],
                    } for ref_id, ref_data in reference_ids.items()]
            print("checkpoint 12")
            nodes.append({
                "id": root_paper_id,
                "title": self.repository.get_paper_by_id(root_paper_id)["title"],
                "similarity_score": 1.0,
                "relationship_type": None,
                "remarks": None,
            })
            print("checkpoint 13")
            await websocket.send_json({
                "nodes": nodes,
                "links": [{"source": cited_paper_id, "target": ref_id} for ref_id in reference_ids.keys()],
            })
            print("checkpoint 14")
            # Insert new nodes into the frontier
            for node in nodes:
                frontier.insert(node)
            
            print("checkpoint 15")
            print(frontier.is_empty)
            while not frontier.is_empty():
                print("checkpoint 15.1")
                next_paper = frontier.pop()
                print()
                print("checkpoint 15.2")
                if next_paper["id"] not in explored_papers:
                    print("checkpoint 15.3")
                    await self.explore_paper(websocket, root_paper_id, next_paper["id"], explored_papers, frontier, max_depth, current_depth + 1, similarity_threshold, traversal_type)

        except Exception as e:
            await websocket.send_json({"status": "error", "message": str(e)})
            raise HTTPException(status_code=500, detail=str(e))

