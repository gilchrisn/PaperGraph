from fastapi import HTTPException, WebSocket
import os

from grobid.grobid_paper_extractor import extract_metadata
from compare_paper.similarity_computation import get_similarity

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

    def process_references(
        self,
        root_paper_id: str,
        cited_paper_id: str,
        explored_papers: set,
        similarity_threshold=0.88
    ):
        """
        Process all references of a given paper to build downward links.
        Returns a dict of { ref_paper_id: {similarity_score, relationship_type, remarks} }
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
                # If similarity is below threshold, we won't revisit it,
                # but we still record it
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

    # -------------------------------------------------------------------------
    # DOWNWARD EXPLORATION METHOD
    # -------------------------------------------------------------------------
    async def explore_downward(
        self,
        websocket: WebSocket,
        root_paper_id: str,
        start_paper_id: str,
        explored_papers: set,
        frontier,
        max_depth: int,
        current_depth: int,
        similarity_threshold: float,
        traversal_type: str
    ):
        """
        Explore references (downwards) from a given start paper using BFS/DFS/priority.
        Sends partial updates to WebSocket (phase="downward").
        Returns the set of discovered paper IDs (including the start paper).
        """
        # If we have exceeded the max depth, notify and return
        if current_depth > max_depth:
            await websocket.send_json({"status": "Max exploration depth reached"})
            return set()

        if start_paper_id in explored_papers:
            return set()

        explored_papers.add(start_paper_id)
        reference_ids = self.process_references(
            root_paper_id, start_paper_id, explored_papers, similarity_threshold
        )

        # Build nodes for JSON
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

        # Also include current paper node
        current_paper_info = self.repository.get_paper_by_id(start_paper_id)
        if current_paper_info:
            nodes.append(
                {
                    "id": start_paper_id,
                    "title": current_paper_info["title"],
                    "similarity_score": 1.0 if start_paper_id == root_paper_id else 0.999,
                    "relationship_type": None,
                    "remarks": None,
                }
            )

        # Build links from the current paper -> references
        links = [{"source": start_paper_id, "target": ref_id} for ref_id in reference_ids.keys()]

        # Send partial update
        await websocket.send_json(
            {
                "phase": "downward",
                "nodes": nodes,
                "links": links,
            }
        )

        # Insert newly discovered nodes into the frontier
        for node in nodes:
            frontier.insert(node)

        # Recursively pop from the frontier and explore
        discovered_nodes = {start_paper_id}
        discovered_nodes.update(reference_ids.keys())

        while not frontier.is_empty():
            next_paper = frontier.pop()
            paper_id = next_paper["id"]
            if paper_id not in explored_papers:
                child_nodes = await self.explore_downward(
                    websocket,
                    root_paper_id,
                    paper_id,
                    explored_papers,
                    frontier,
                    max_depth,
                    current_depth + 1,
                    similarity_threshold,
                    traversal_type
                )
                discovered_nodes.update(child_nodes)

        return discovered_nodes

    # -------------------------------------------------------------------------
    # UPWARD EXPLORATION METHOD
    # -------------------------------------------------------------------------
    async def explore_upward(
        self,
        websocket: WebSocket,
        root_paper_id: str,
        paper_id: str,
        explored_upwards: set,
        max_depth: int,
        current_depth: int,
        similarity_threshold: float,
    ):
        """
        Explore referencing (upwards) from the given paper.
        Sends partial updates to WebSocket (phase="upward").
        Returns the set of discovered (parent) paper IDs.
        """
        if current_depth > max_depth:
            return set()

        if paper_id in explored_upwards:
            return set()

        discovered_parents = set()
        referencing_papers = self.get_referencing_papers(paper_id)

        nodes = []
        links = []

        for parent_id in referencing_papers:
            if parent_id in explored_upwards:
                continue

            parent_paper = self.repository.get_paper_by_id(parent_id)

            # Check similarity (root->parent_id)
            ref_entry = self.repository.get_reference_by_paper_ids(root_paper_id, parent_id)
            if ref_entry and ref_entry["similarity_score"] >= similarity_threshold:
                discovered_parents.add(parent_id)
                # Add node
                nodes.append(
                    {
                        "id": parent_id,
                        "title": parent_paper["title"],
                        "similarity_score": float(ref_entry["similarity_score"]),
                        "relationship_type": ref_entry["relationship_type"],
                        "remarks": ref_entry["remarks"],
                    }
                )
                # Add link from parent -> paper_id
                links.append({"source": parent_id, "target": paper_id})

        # Also add the current paper node to keep a cohesive graph
        cur_paper = self.repository.get_paper_by_id(paper_id)
        if cur_paper:
            nodes.append(
                {
                    "id": paper_id,
                    "title": cur_paper["title"],
                    "similarity_score": 0.999 if paper_id != root_paper_id else 1.0,
                    "relationship_type": None,
                    "remarks": None,
                }
            )

        # Send an update if any new nodes/links appear
        if nodes or links:
            await websocket.send_json({"phase": "upward", "nodes": nodes, "links": links})

        # Mark this paper as explored so we don't re-run
        explored_upwards.add(paper_id)

        # Recursively explore parents
        for parent_id in discovered_parents:
            await self.explore_upward(
                websocket,
                root_paper_id,
                parent_id,
                explored_upwards,
                max_depth,
                current_depth + 1,
                similarity_threshold
            )

        return discovered_parents

    # -------------------------------------------------------------------------
    # PRIMARY PUBLIC METHOD
    # -------------------------------------------------------------------------
    async def explore_paper(
        self,
        websocket: WebSocket,
        root_paper_id: str,
        start_paper_id: str,
        max_depth: int = 5,
        similarity_threshold: float = 0.88,
        traversal_type: str = "bfs",
    ):
        """
        1) Downward exploration from the start paper (references).
        2) Then, for each discovered node (above threshold), do upward exploration.
        """
        # Validate traversal type
        if traversal_type not in ["bfs", "dfs", "priority"]:
            raise ValueError("Invalid traversal_type. Use 'bfs', 'dfs', or 'priority'.")

        # Prepare BFS/DFS/priority queue for the downward pass
        if traversal_type == "bfs":
            frontier = Queue()
        elif traversal_type == "dfs":
            frontier = Stack()
        else:
            frontier = PriorityQueue(lambda x: -x["similarity_score"])

        # 1. DOWNWARD EXPLORATION
        explored_papers_downward = set()
        try:
            discovered_nodes_downward = await self.explore_downward(
                websocket=websocket,
                root_paper_id=root_paper_id,
                start_paper_id=start_paper_id,
                explored_papers=explored_papers_downward,
                frontier=frontier,
                max_depth=max_depth,
                current_depth=0,
                similarity_threshold=similarity_threshold,
                traversal_type=traversal_type,
            )
        except Exception as e:
            await websocket.send_json({"status": "error", "message": str(e)})
            raise HTTPException(status_code=500, detail=str(e))

        # 2. UPWARD EXPLORATION for all discovered nodes that meet threshold
        #    (excluding the root paper itself)
        qualified_nodes = []
        for node_id in discovered_nodes_downward:
            if node_id == root_paper_id:
                continue
            ref_entry = self.repository.get_reference_by_paper_ids(root_paper_id, node_id)
            if ref_entry and ref_entry["similarity_score"] is not None:
                if ref_entry["similarity_score"] >= similarity_threshold:
                    qualified_nodes.append(node_id)

        # We can do a multi-step BFS/DFS upward for each qualified node
        # (or you can unify them into one BFS, if you prefer).
        explored_upwards = set()
        for qnode_id in qualified_nodes:
            try:
                await self.explore_upward(
                    websocket=websocket,
                    root_paper_id=root_paper_id,
                    paper_id=qnode_id,
                    explored_upwards=explored_upwards,
                    max_depth=1,  # or some other depth limit
                    current_depth=0,
                    similarity_threshold=similarity_threshold,
                )
            except Exception as e:
                await websocket.send_json({"status": "error", "message": str(e)})
                raise HTTPException(status_code=500, detail=str(e))
