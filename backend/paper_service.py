import logging
import json
import os

from fastapi import HTTPException, WebSocket

# Example imports; adjust to match your code
from paper_comparison import generate_embedding_for_paper_chunks, compare_two_papers

# Import your PaperRepository, which handles the DB logic
from paper_repository import PaperRepository
from util.frontier import Queue, PriorityQueue, Stack



logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Adjust as needed

class PaperService:
    def __init__(self):
        self.repository = PaperRepository()  # Ensure your repository class is properly initialized

    def download_paper_and_create_record(self, paper_id: str):
        """
        Download the paper using the Semantic Scholar API and create a record in the database.
        """
        try:
            # Download the paper and create a recordy
            self.repository.process_and_cite_paper(paper_id)
        except Exception as e:
            logger.exception(f"Error downloading paper with ID: {paper_id}")
            raise HTTPException(status_code=500, detail=str(e))


    def get_all_papers(self):
        """
        Retrieve all papers from the database.
        """
        try:
            papers_response = self.repository.get_all_papers()
            return papers_response
        except Exception as e:
            logger.exception("Error fetching all papers")
            raise HTTPException(status_code=500, detail=str(e))
        
    def search_paper_by_title(self, title: str):
        """
        Retrieve papers by title.
        """
        try:
            papers_response = self.repository.get_paper_by_title(title)
            return papers_response
        except Exception as e:
            logger.exception("Error searching papers by title")
            raise HTTPException(status_code=500, detail=str(e))
        
    def get_paper_by_id(self, paper_id: str):
        """
        Retrieve a specific paper by its ID.
        """
        try:
            paper_response = self.repository.get_paper_by_semantic_id(paper_id)
            return paper_response
        except Exception as e:
            logger.exception(f"Error fetching paper with ID: {paper_id}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_pdf_path(self, paper_id: str) -> str:
        """
        Get the local_filepath for a given paper_id (semantic_id).
        Returns None if the paper does not exist or has no local_filepath.
        """
        paper_response = self.repository.get_paper_by_semantic_id(paper_id)
        if not paper_response:
            return None
        # paper_response["data"] is usually a list
        return paper_response.get("local_filepath", None)

    # ----------------------------------------------------------------
    # Relations Handling
    # ----------------------------------------------------------------
    def fetch_or_insert_relation(self, source_paper_id: str, target_paper_id: str):
        """
        Fetch an existing relation between source_paper_id and target_paper_id
        from the relations table. If none exists, create one with NULL fields
        for relationship_type, remarks, and relevance_score.
        Returns the relation record (Supabase response).
        """
        try:
            existing_relation_resp = self.repository.get_relation_by_source_and_target(
                source_paper_id, target_paper_id
            )
            if not existing_relation_resp:
                # No existing relation, create a blank one
                relation = {
                    "source_paper_id": source_paper_id,
                    "target_paper_id": target_paper_id,
                    "relevance_score": None,
                }
                self.repository.create_relation(relation)
                # Re-fetch to confirm
                return self.repository.get_relation_by_source_and_target(
                    source_paper_id, target_paper_id
                )
            else:
                return existing_relation_resp
        except Exception as e:
            logger.exception("Error fetching or inserting relation")
            raise HTTPException(status_code=500, detail=str(e))

    def process_citation(self, root_paper_id: str, target_paper_id: str) -> tuple:
        """
        Process a citation or reference relationship from root_paper_id to target_paper_id:
          - Check or create a record in the `relations` table.
          - If no relevance_score is stored, compute it using get_relevance.
          - Store the computed relevance_score in the relations table.
        Returns (relevance_score, relationship_type, remarks).
        """
        try:
            # Make sure the target paper exists in the 'papers' table
            target_paper_resp = self.repository.get_paper_by_semantic_id(target_paper_id)
            if not target_paper_resp:
                logger.error(f"Paper with ID {target_paper_id} not found")
                return 0.0

            # Check or create the relation row
            relation = self.fetch_or_insert_relation(root_paper_id, target_paper_id)
            if not relation:
                logger.warning(f"Relation row could not be created for {root_paper_id} -> {target_paper_id}")
                return 0.0

            if relation.get("relevance_score") is not None:
                # Already computed
                return relation["relevance_score"]
                

            # Generate embeddings for the papers and compare
            # Check whether the embeddings are already computed
            # Assume that having the chunks in the DB implies the embeddings are also present
            if not self.repository.get_chunks_by_semantic_id(root_paper_id):
                generate_embedding_for_paper_chunks(root_paper_id)
            if not self.repository.get_chunks_by_semantic_id(target_paper_id):
                generate_embedding_for_paper_chunks(target_paper_id)

            relevance_score = compare_two_papers(root_paper_id, target_paper_id)
            
            # Update the relation row
            updated_fields = {
                "relevance_score": relevance_score,
            }
            self.repository.update_relation_by_source_and_target(
                root_paper_id, target_paper_id, updated_fields
            )

            return relevance_score
        except Exception as e:
            logger.exception("Error processing citation")
            raise HTTPException(status_code=500, detail=str(e))

    def process_citations(self, root_paper_id: str, current_paper_id: str, explored_papers: set, similarity_threshold: float = 0.88) -> dict:
        """
        For the given current_paper_id, look up its citations in the 'citations' table,
        compute or retrieve the relevance score for each cited paper, and filter out
        citations that fall below the threshold.
        Returns a dict of {target_paper_id: { 'relevance_score': ..., 'relationship_type': ..., 'remarks': ...}}
        """
        try:
            logger.debug(f"Processing references for paper ID: {current_paper_id}")
            # Check that the current paper is in the DB
            paper_resp = self.repository.get_paper_by_semantic_id(current_paper_id)

            if not paper_resp:
                logger.error(f"Paper with ID {current_paper_id} not found in DB")
                return {}

            # Get all citations from the 'citations' table where source_paper_id = current_paper_id
            citations_resp = self.repository.get_citations_by_source(current_paper_id)
            if not citations_resp:
                logger.debug(f"Paper {current_paper_id} has no citations in 'citations' table")
                return {}

            filtered_citations = {}
            for citation_row in citations_resp:
                target_id = citation_row["cited_paper_id"]
                if target_id in explored_papers:
                    continue

                relevance_score = self.process_citation(root_paper_id, target_id)
                if relevance_score < similarity_threshold:
                    # Mark as explored to skip in future
                    explored_papers.add(target_id)
                    continue

                filtered_citations[target_id] = {
                    "relevance_score": relevance_score,
                }

            return filtered_citations
        except Exception as e:
            logger.exception("Error processing citations")
            raise HTTPException(status_code=500, detail=str(e))

    # ----------------------------------------------------------------
    # Handling "Parent" Papers (i.e., who cites this paper?)
    # ----------------------------------------------------------------

    def process_parents(self, root_paper_id: str, child_paper_id: str, explored_papers: set, similarity_threshold: float = 0.88) -> dict:
        """
        For each paper that cites child_paper_id, compute or retrieve the relevance score in the 'relations' table,
        skipping if it is below similarity_threshold or if the PDF paths are missing, etc.
        Returns a dict of {parent_id: { 'relevance_score': ..., 'relationship_type': ..., 'remarks': ... }}
        """
        try:
            parent_citations = self.repository.get_citations_by_cited(child_paper_id)
            if not parent_citations:
                return {}

            parents_dict = {}
            for citation in parent_citations:
                parent_id = citation["source_paper_id"]
                if parent_id in explored_papers:
                    continue

                # Compute or retrieve the relevance_score for root_paper_id -> parent_id
                relevance_score = self.process_citation(root_paper_id, parent_id)
                if relevance_score < similarity_threshold:
                    explored_papers.add(parent_id)
                    continue

                parents_dict[parent_id] = {
                    "relevance_score": relevance_score,
                }

            return parents_dict
        except Exception as e:
            logger.exception("Error processing parents")
            raise HTTPException(status_code=500, detail=str(e))

    # ----------------------------------------------------------------
    # Downward Exploration
    # ----------------------------------------------------------------
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
    ) -> set:
        """
        Recursively explores the 'downward' citations from a paper,
        i.e., the papers that it cites. If the relevance score is below
        similarity_threshold, it is skipped. Otherwise, it's added to frontier
        for further exploration.
        """
        try:
            if current_depth > max_depth:
                await websocket.send_json({"status": "Max exploration depth reached"})
                return set()

            if start_paper_id in explored_papers:
                return set()

            explored_papers.add(start_paper_id)

            # Gather references that pass the threshold
            reference_ids = self.process_citations(root_paper_id, start_paper_id, explored_papers, similarity_threshold)

            # Build nodes from discovered references
            nodes = []
            for ref_id, ref_data in reference_ids.items():
                ref_paper_resp = self.repository.get_paper_by_semantic_id(ref_id)
                if not ref_paper_resp:
                    continue
                ref_paper = ref_paper_resp
                nodes.append({
                    "id": ref_id,
                    "title": ref_paper.get("title"),
                    "year": ref_paper.get("year"),
                    "relevance_score": ref_data.get("relevance_score"),
                })

            # Also include the current paper node
            current_paper_resp = self.repository.get_paper_by_semantic_id(start_paper_id)
            if current_paper_resp:
                current_paper = current_paper_resp
                print(current_paper)
                nodes.append({
                    "id": start_paper_id,
                    "title": current_paper.get("title"),
                    "year": current_paper.get("year"),
                    "relevance_score": current_paper.get("relevance_score"),
                })

            # Build links from the current paper to each reference
            links = [{"source": start_paper_id, "target": ref_id} for ref_id in reference_ids.keys()]

            await websocket.send_json({
                "phase": "downward",
                "nodes": nodes,
                "links": links,
            })

            # Insert discovered references into the frontier for further exploration
            for node in nodes:
                frontier.insert(node)

            discovered_nodes = {start_paper_id}
            discovered_nodes.update(reference_ids.keys())

            # Continue exploring
            while not frontier.is_empty():
                next_paper = frontier.pop()
                # 'id' should match the 'semantic_id'
                paper_id = next_paper.get("id")
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
        except Exception as e:
            logger.exception("Error during downward exploration")
            await websocket.send_json({"status": "error", "message": str(e)})
            return set()

    # ----------------------------------------------------------------
    # Upward Exploration
    # ----------------------------------------------------------------
    async def explore_upward(
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
    ) -> set:
        """
        Recursively explores 'parent' papers that cite the current paper.
        Similar approach to downward, but we call process_parents.
        """
        try:
            if current_depth > max_depth:
                await websocket.send_json({"status": "Max upward depth reached"})
                return set()

            if start_paper_id in explored_papers:
                return set()

            explored_papers.add(start_paper_id)

            # Find parent papers with relevance above threshold
            parents_dict = self.process_parents(root_paper_id, start_paper_id, explored_papers, similarity_threshold)

            nodes = []
            for parent_id, parent_data in parents_dict.items():
                if parent_id in explored_papers:
                    continue
                parent_paper_resp = self.repository.get_paper_by_semantic_id(parent_id)
                if not parent_paper_resp:
                    continue
                parent_paper = parent_paper_resp
                nodes.append({
                    "id": parent_id,
                    "title": parent_paper.get("title"),
                    "year": parent_paper.get("year"),
                    "relevance_score": parent_data.get("relevance_score"),
                })

            # Create links from each parent to the current paper
            links = [{"source": parent_id, "target": start_paper_id} for parent_id in parents_dict.keys()]

            # Also include the current paper node
            current_paper_resp = self.repository.get_paper_by_semantic_id(start_paper_id)
            if current_paper_resp:
                current_paper = current_paper_resp
                nodes.append({
                    "id": start_paper_id,
                    "title": current_paper.get("title"),
                    "year": current_paper.get("year"),
                    "relevance_score": current_paper.get("relevance_score"),
                })

            if nodes or links:
                await websocket.send_json({
                    "phase": "upward",
                    "nodes": nodes,
                    "links": links,
                })

            discovered_nodes = {start_paper_id}
            discovered_nodes.update(parents_dict.keys())

            # Add found parent papers to the frontier
            for node in nodes:
                frontier.insert(node)

            while not frontier.is_empty():
                next_paper = frontier.pop()
                pid = next_paper["id"]
                if pid not in explored_papers:
                    child_nodes = await self.explore_upward(
                        websocket=websocket,
                        root_paper_id=root_paper_id,
                        start_paper_id=pid,
                        explored_papers=explored_papers,
                        frontier=frontier,
                        max_depth=max_depth,
                        current_depth=current_depth + 1,
                        similarity_threshold=similarity_threshold,
                        traversal_type=traversal_type
                    )
                    discovered_nodes.update(child_nodes)

            return discovered_nodes
        except Exception as e:
            logger.exception("Error during upward exploration")
            await websocket.send_json({"status": "error", "message": str(e)})
            return set()

    # ----------------------------------------------------------------
    # Primary Exploration Method
    # ----------------------------------------------------------------
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
        Orchestrates downward (papers cited by start_paper_id) exploration
        and then upward (papers citing the discovered papers) exploration.

        Data is sent to the WebSocket as it is discovered. e.g.,
        {
            "phase": "downward",
            "nodes": [{...}, {...}],
            "links": [{...}, {...}]
        }

        The generated graph will have 
        """
        try:
            # Choose your data structure
            if traversal_type == "bfs":
                frontier_down = Queue()
            elif traversal_type == "dfs":
                frontier_down = Stack()
            else:
                # For a priority-based approach
                frontier_down = PriorityQueue(lambda x: -x.get("relevance_score", 0))

            # Downward exploration
            explored_papers_downward = set()
            discovered_nodes_downward = await self.explore_downward(
                websocket=websocket,
                root_paper_id=root_paper_id,
                start_paper_id=start_paper_id,
                explored_papers=explored_papers_downward,
                frontier=frontier_down,
                max_depth=max_depth,
                current_depth=0,
                similarity_threshold=similarity_threshold,
                traversal_type=traversal_type,
            )

            # For each discovered node (excluding root), we may explore upward
            # if the relevance score is above the threshold
            qualified_nodes = []
            for node_id in discovered_nodes_downward:
                if node_id == root_paper_id:
                    continue
                # Check the relation row for root_paper_id -> node_id
                rel_resp = self.repository.get_relation_by_source_and_target(root_paper_id, node_id)
                if rel_resp:
                    rel_data = rel_resp
                    # We consider "relevance_score" to see if it is above threshold
                    if rel_data.get("relevance_score", 0) >= similarity_threshold:
                        qualified_nodes.append(node_id)

            # Upward exploration for qualified nodes
            if traversal_type == "bfs":
                frontier_up = Queue()
            elif traversal_type == "dfs":
                frontier_up = Stack()
            else:
                frontier_up = PriorityQueue(lambda x: -x.get("relevance_score", 0))

            explored_upwards = set(explored_papers_downward)  # Start with downward set
            all_upward_nodes = set()

            for qnode_id in qualified_nodes:
                if qnode_id in explored_upwards:
                    # We remove it so the upward exploration can process it again
                    explored_upwards.remove(qnode_id)

                upward_discovered = await self.explore_upward(
                    websocket=websocket,
                    root_paper_id=root_paper_id,
                    start_paper_id=qnode_id,
                    explored_papers=explored_upwards,
                    frontier=frontier_up,
                    max_depth=1,  # or some limit for upward expansion
                    current_depth=0,
                    similarity_threshold=similarity_threshold,
                    traversal_type=traversal_type,
                )
                all_upward_nodes.update(upward_discovered)

            return {
                "downward_discovered": discovered_nodes_downward,
                "upward_discovered": all_upward_nodes
            }
        except Exception as e:
            logger.exception("Error during paper exploration")
            await websocket.send_json({"status": "error", "message": str(e)})
            return {}
        


# =======================================================================================================


if __name__ == "__main__":
    # Example usage
    paper_service = PaperService()
    # Set up a WebSocket instance
    # TypeError: WebSocket.__init__() missing 3 required positional arguments: 'scope', 'receive', and 'send'
    ws = WebSocket()
    ws = WebSocket()
    # Call the explore_paper method
    result = paper_service.explore_paper(
        websocket=ws,
        root_paper_id="001534ec4e6d656722fddc81ba532779cea76875",
        start_paper_id="001534ec4e6d656722fddc81ba532779cea76875",
        max_depth=1,
        similarity_threshold=0.88,
        traversal_type="bfs"
    )
    print(result)



