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
        ref_id = ref_paper["id"]
        ref_entry = self.fetch_or_insert_reference(root_paper_id, ref_id)

        if ref_entry and ref_entry["similarity_score"] is not None:
            return ref_entry["similarity_score"], ref_entry["relationship_type"], ref_entry["remarks"]

        root_paper = self.repository.get_paper_by_id(root_paper_id)
        if not root_paper or "filepath" not in root_paper:
            raise HTTPException(status_code=500, detail="Root paper filepath not found")

        similarity_score, relationship_type, remarks = get_similarity(
            root_paper["filepath"], ref_paper["filepath"]
        )
        self.repository.insert_reference(
            root_paper_id, ref_id, relationship_type, remarks, float(similarity_score)
        )
        explored_papers.add(ref_id)
        return similarity_score, relationship_type, remarks

    def process_references(self, root_paper_id: str, cited_paper_id: str, explored_papers: set, similarity_threshold=0.88):
        """
        Process all references of a given paper to build downward links.
        """
        print(f"Processing references for paper ID: {cited_paper_id}")
        paper = self.repository.get_paper_by_id(cited_paper_id)
        if not paper:
            print(f"Paper with ID {cited_paper_id} not found")
            return {}

        reference_titles = extract_metadata(paper["filepath"], "processReferences")
        if not reference_titles:
            print(f"Paper Title: {paper['title']} has no references")
            return {}

        reference_ids = {}
        for reference in reference_titles:
            ref_paper = self.repository.find_similar_papers_by_title(reference, 0.5)
            if ref_paper and ref_paper["id"] not in explored_papers:
                similarity_score, relationship_type, remarks = self.process_reference(
                    root_paper_id, ref_paper, explored_papers
                )
                # Only proceed if we haven't permanently excluded this paper
                # after discovering extremely low similarity
                if similarity_score < similarity_threshold:
                    explored_papers.add(ref_paper["id"])

                reference_ids[ref_paper["id"]] = {
                    "similarity_score": similarity_score,
                    "relationship_type": relationship_type,
                    "remarks": remarks,
                }

        return reference_ids

    def get_referencing_papers(self, paper_id: str):
        """
        Fetch all papers that reference a given paper (parents).
        """
        return self.repository.get_referencing_papers(paper_id)

    async def explore_paper(
        self,
        websocket: WebSocket,
        root_paper_id: str,
        cited_paper_id: str,
        explored_papers: set = None,
        frontier=None,
        max_depth: int = 5,
        current_depth: int = 0,
        similarity_threshold=0.88,
        traversal_type="bfs",
    ):
        """
        Real-time exploration of related papers with WebSocket updates.

        This method divides exploration into two phases:
        1) Downward search (references)
        2) Upward search (referencing/parent papers)

        Parameters:
            websocket (WebSocket): WebSocket connection for real-time updates.
            root_paper_id (str): ID of the root paper for the exploration.
            cited_paper_id (str): ID of the current paper being explored.
            explored_papers (set, optional): Set of papers already explored. Defaults to None.
            frontier (Queue|Stack|PriorityQueue, optional): Data structure for managing traversal. Defaults to None.
            max_depth (int): Maximum depth of exploration for downward traversal. Defaults to 5.
            current_depth (int): Current depth of exploration. Defaults to 0.
            similarity_threshold (float): Threshold for similarity scores.
            traversal_type (str): Type of traversal ('bfs', 'dfs', 'priority').
        """

        # Validate traversal type
        if traversal_type not in ["bfs", "dfs", "priority"]:
            raise ValueError("Invalid traversal_type. Use 'bfs', 'dfs', or 'priority'.")

        # Initialize explored_papers and frontier
        if explored_papers is None:
            explored_papers = set()
        if frontier is None:
            if traversal_type == "bfs":
                frontier = Queue()
            elif traversal_type == "dfs":
                frontier = Stack()
            else:
                frontier = PriorityQueue(lambda x: -x["similarity_score"])

        # ---------------
        # DOWNWARD SEARCH
        # ---------------
        if cited_paper_id in explored_papers:
            return

        # If we have exceeded the max depth, notify and return
        if current_depth > max_depth:
            await websocket.send_json({"status": "Max exploration depth reached"})
            return

        try:
            explored_papers.add(cited_paper_id)

            # 1. Process references to find downward links
            reference_ids = self.process_references(
                root_paper_id, cited_paper_id, explored_papers, similarity_threshold
            )

            # 2. Build and send node/link data for downward references
            nodes = []
            for ref_id, ref_data in reference_ids.items():
                paper_info = self.repository.get_paper_by_id(ref_id)
                if not paper_info:
                    continue
                nodes.append(
                    {
                        "id": ref_id,
                        "title": paper_info["title"],
                        "similarity_score": float(ref_data["similarity_score"]),
                        "relationship_type": ref_data["relationship_type"],
                        "remarks": ref_data["remarks"],
                    }
                )

            # Also include the current paper itself (and root, if needed)
            current_paper_info = self.repository.get_paper_by_id(cited_paper_id)
            if current_paper_info:
                nodes.append(
                    {
                        "id": cited_paper_id,
                        "title": current_paper_info["title"],
                        "similarity_score": 1.0 if cited_paper_id == root_paper_id else 0.999,
                        "relationship_type": None,
                        "remarks": None,
                    }
                )

            # Send downwards links => (cited_paper_id -> each ref_id)
            await websocket.send_json(
                {
                    "phase": "downward",
                    "nodes": nodes,
                    "links": [
                        {"source": cited_paper_id, "target": ref_id}
                        for ref_id in reference_ids.keys()
                    ],
                }
            )

            # Insert newly discovered nodes into the frontier
            for node in nodes:
                frontier.insert(node)

            # Continue the downward traversal until the frontier is exhausted
            while not frontier.is_empty():
                next_paper = frontier.pop()
                if next_paper["id"] not in explored_papers:
                    await self.explore_paper(
                        websocket,
                        root_paper_id,
                        next_paper["id"],
                        explored_papers,
                        frontier,
                        max_depth,
                        current_depth + 1,
                        similarity_threshold,
                        traversal_type,
                    )

            # ----------------
            # UPWARD SEARCH
            # ----------------
            # Once the downward exploration is complete, we can search upwards.
            # For each paper (except the root) that has similarity above threshold,
            # find its 'parent' papers (referencing papers).

            # We can do a separate BFS or direct retrieval. Here, we do a single-step BFS
            # as a demonstration. Adjust if you need a multi-level upward search with depth limits.

            upward_frontier = Queue()  # or PriorityQueue/Stack if you'd like
            upward_explored = set()

            # 1. Gather all the "qualified" nodes from downward exploration
            #    For simplicity, we reuse the `explored_papers` set and
            #    check any references in the DB that have similarity > threshold.
            #    You might want a separate collection if you'd prefer a different approach.
            all_papers_downward = explored_papers.copy()
            for paper_id in all_papers_downward:
                if paper_id == root_paper_id:
                    continue
                # Check the similarity of (root->paper_id) from DB
                ref_entry = self.repository.get_reference_by_paper_ids(root_paper_id, paper_id)
                if ref_entry and ref_entry["similarity_score"] >= similarity_threshold:
                    upward_frontier.insert(paper_id)

            # 2. Process BFS upward
            while not upward_frontier.is_empty():
                current_up_paper_id = upward_frontier.pop()
                if current_up_paper_id in upward_explored:
                    continue

                upward_explored.add(current_up_paper_id)

                # Find referencing papers => "parents"
                referencing_papers = self.get_referencing_papers(current_up_paper_id)
                if not referencing_papers:
                    continue

                # Build node/link data
                up_nodes = []
                up_links = []
                for parent_paper in referencing_papers:
                    parent_id = parent_paper["id"]

                    # If we want to filter by the same threshold relative to root, check reference
                    ref_entry = self.repository.get_reference_by_paper_ids(root_paper_id, parent_id)
                    # If no reference record found or similarity is None, skip
                    if not ref_entry or ref_entry["similarity_score"] is None:
                        continue

                    # If similarity passes threshold, add to BFS
                    if ref_entry["similarity_score"] >= similarity_threshold:
                        up_nodes.append(
                            {
                                "id": parent_id,
                                "title": parent_paper["title"],
                                "similarity_score": float(ref_entry["similarity_score"]),
                                "relationship_type": ref_entry["relationship_type"],
                                "remarks": ref_entry["remarks"],
                            }
                        )
                        up_links.append({"source": parent_id, "target": current_up_paper_id})
                        if parent_id not in upward_explored:
                            upward_frontier.insert(parent_id)

                # Add the current paper if needed for a consistent graph
                this_paper = self.repository.get_paper_by_id(current_up_paper_id)
                if this_paper:
                    up_nodes.append(
                        {
                            "id": current_up_paper_id,
                            "title": this_paper["title"],
                            # Keep some default or computed similarity to root
                            "similarity_score": 1.0 if current_up_paper_id == root_paper_id else 0.999,
                            "relationship_type": None,
                            "remarks": None,
                        }
                    )

                # Send upward expansion data
                if up_nodes or up_links:
                    await websocket.send_json(
                        {
                            "phase": "upward",
                            "nodes": up_nodes,
                            "links": up_links,
                        }
                    )

        except Exception as e:
            await websocket.send_json({"status": "error", "message": str(e)})
            raise HTTPException(status_code=500, detail=str(e))
