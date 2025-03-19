import os
import time
import logging
from supabase import create_client, Client
from paper_search.semantic_scholar import process_and_cite_paper

# ----------------------------
# Logging Configuration
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        # logging.FileHandler("paper_repository.log")
    ]
)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-supabase-url.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-supabase-api-key")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class PaperRepository:
    def __init__(self):
        self.client = supabase

    # ----- Papers CRUD -----
    def create_paper(self, paper: dict) -> dict:
        """
        Insert a new paper record into the papers table.
        Expected keys: semantic_id, title, year, venue, external_ids, open_access_pdf, local_filepath.
        """
        try:
            response = self.client.table("papers").insert(paper).execute()
            logger.info(f"Created paper: {paper.get('semantic_id')} - {paper.get('title')}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating paper: {e}")
            raise

    def get_all_papers(self) -> dict:
        """
        Retrieve all paper records from the papers table.
        """
        try:
            response = self.client.table("papers").select("*").execute()
            logger.info("Retrieved all papers")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting all papers: {e}")
            raise

    def get_paper_by_semantic_id(self, semantic_id: str) -> dict:
        """
        Retrieve a paper by its semantic_id.
        """
        try:
            response = self.client.table("papers").select("*").eq("semantic_id", semantic_id).execute()
            logger.info(f"Retrieved paper {semantic_id}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting paper {semantic_id}: {e}")
            raise

    def get_paper_by_title(self, title: str) -> dict:
        """
        Retrieve a paper by its title.
        """
        try:
            response = self.client.table("papers").select("*").ilike("title", title).execute()
            logger.info(f"Retrieved paper with title {title}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting paper with title {title}: {e}")
            raise

    def update_paper_by_semantic_id(self, semantic_id: str, updated_fields: dict) -> dict:
        """
        Update a paper's fields based on its semantic_id.
        """
        try:
            response = self.client.table("papers").update(updated_fields).eq("semantic_id", semantic_id).execute()
            logger.info(f"Updated paper {semantic_id} with {updated_fields}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating paper {semantic_id}: {e}")
            raise

    def delete_paper_by_semantic_id(self, semantic_id: str) -> dict:
        """
        Delete a paper by its semantic_id.
        """
        try:
            response = self.client.table("papers").delete().eq("semantic_id", semantic_id).execute()
            logger.info(f"Deleted paper {semantic_id}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error deleting paper {semantic_id}: {e}")
            raise

    # ----- Citations CRUD -----
    def create_citation(self, citation: dict) -> dict:
        """
        Insert a new citation record into the citations table.
        Expected keys: source_paper_id, cited_paper_id.
        (Extra fields can be included if needed.)
        """
        try:
            response = self.client.table("citations").insert(citation).execute()
            logger.info(f"Created citation: {citation.get('source_paper_id')} -> {citation.get('cited_paper_id')}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating citation: {e}")
            raise

    def get_citations_by_source(self, source_paper_id: str) -> dict:
        """
        Retrieve all citation records for a given source paper.
        """
        try:
            response = self.client.table("citations").select("*").eq("source_paper_id", source_paper_id).execute()
            logger.info(f"Retrieved citations for source paper {source_paper_id}")
            return response.data
        except Exception as e:
            logger.error(f"Error getting citations for {source_paper_id}: {e}")
            raise

    def update_citation_by_source_and_cited(self, source_paper_id: str, cited_paper_id: str, updated_fields: dict) -> dict:
        """
        Update a citation record by its source and cited paper IDs.
        """
        try:
            response = self.client.table("citations") \
                .update(updated_fields) \
                .eq("source_paper_id", source_paper_id) \
                .eq("cited_paper_id", cited_paper_id) \
                .execute()
            logger.info(f"Updated citation {source_paper_id} -> {cited_paper_id} with {updated_fields}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating citation {source_paper_id} -> {cited_paper_id}: {e}")
            raise

    def delete_citation_by_source_and_cited(self, source_paper_id: str, cited_paper_id: str) -> dict:
        """
        Delete a citation record by its source and cited paper IDs.
        """
        try:
            response = self.client.table("citations") \
                .delete() \
                .eq("source_paper_id", source_paper_id) \
                .eq("cited_paper_id", cited_paper_id) \
                .execute()
            logger.info(f"Deleted citation {source_paper_id} -> {cited_paper_id}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error deleting citation {source_paper_id} -> {cited_paper_id}: {e}")
            raise

    # ----- Relations CRUD -----
    def create_relation(self, relation: dict) -> dict:
        """
        Insert a new relation record into the relations table.
        Expected keys: source_paper_id, target_paper_id, relationship_type, remarks, relevance_score.
        """
        try:
            response = self.client.table("relations").insert(relation).execute()
            logger.info(f"Created relation: {relation.get('source_paper_id')} -> {relation.get('target_paper_id')}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating relation: {e}")
            raise

    def get_relations_by_source(self, source_paper_id: str) -> dict:
        """
        Retrieve all relation records for a given source paper.
        """
        try:
            response = self.client.table("relations").select("*").eq("source_paper_id", source_paper_id).execute()
            logger.info(f"Retrieved relations for source paper {source_paper_id}")
            return response.data
        except Exception as e:
            logger.error(f"Error getting relations for {source_paper_id}: {e}")
            raise

    def get_relation_by_source_and_target(self, source_paper_id: str, target_paper_id: str) -> dict:
        """
        Retrieve relation records for a given source paper and target paper.
        """
        try:
            response = self.client.table("relations").select("*") \
                .eq("source_paper_id", source_paper_id) \
                .eq("target_paper_id", target_paper_id) \
                .execute()
            logger.info(f"Retrieved relations for {source_paper_id} -> {target_paper_id}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting relations for {source_paper_id} and {target_paper_id}: {e}")
            raise

    def update_relation_by_source_and_target(self, source_paper_id: str, target_paper_id: str, updated_fields: dict) -> dict:
        """
        Update a relation record by its source and target paper IDs.
        """
        try:
            response = self.client.table("relations").update(updated_fields) \
                .eq("source_paper_id", source_paper_id) \
                .eq("target_paper_id", target_paper_id) \
                .execute()
            logger.info(f"Updated relation {source_paper_id} -> {target_paper_id} with {updated_fields}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating relation {source_paper_id} -> {target_paper_id}: {e}")
            raise

    def delete_relation_by_source_and_target(self, source_paper_id: str, target_paper_id: str) -> dict:
        """
        Delete a relation record by its source and target paper IDs.
        """
        try:
            response = self.client.table("relations").delete() \
                .eq("source_paper_id", source_paper_id) \
                .eq("target_paper_id", target_paper_id) \
                .execute()
            logger.info(f"Deleted relation {source_paper_id} -> {target_paper_id}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error deleting relation {source_paper_id} -> {target_paper_id}: {e}")
            raise

    def get_cited_papers(self, source_paper_id: str) -> dict:
        """
        Retrieve all cited papers for a given source paper.
        This method queries the citations table for records with the given source_paper_id,
        then fetches the corresponding paper details for each cited paper.
        Returns a dictionary with the list of cited papers.
        """
        try:
            response = self.client.table("citations").select("cited_paper_id").eq("source_paper_id", source_paper_id).execute()
            logger.info(f"Retrieved citations for source paper {source_paper_id}")
            cited_papers = []
            for citation in response.get("data", []):
                cited_id = citation.get("cited_paper_id")
                paper_response = self.get_paper_by_semantic_id(cited_id)
                # If the paper exists, add its details to the list.
                if paper_response.get("data"):
                    cited_papers.append(paper_response.get("data")[0])
            return cited_papers
        except Exception as e:
            logger.error(f"Error getting cited papers for {source_paper_id}: {e}")
            raise

    def get_citations_by_cited(self, cited_paper_id: str) -> dict:
        """
        Retrieve all citation records for a given cited paper.
        """
        try:
            response = self.client.table("citations").select("*").eq("cited_paper_id", cited_paper_id).execute()
            logger.info(f"Retrieved citations for cited paper {cited_paper_id}")
            return response.data
        except Exception as e:
            logger.error(f"Error getting citations for {cited_paper_id}: {e}")

    def get_citing_papers(self, cited_paper_id: str) -> dict:
        """
        Retrieve all citing papers for a given cited paper.
        This method queries the citations table for records with the given cited_paper_id,
        then fetches the corresponding paper details for each source paper.
        Returns a dictionary with the list of citing papers.
        """
        try:
            response = self.client.table("citations").select("source_paper_id").eq("cited_paper_id", cited_paper_id).execute()
            logger.info(f"Retrieved citations for cited paper {cited_paper_id}")
            citing_papers = []
            for citation in response.get("data", []):
                source_id = citation.get("source_paper_id")
                paper_response = self.get_paper_by_semantic_id(source_id)
                # If the paper exists, add its details to the list.
                if paper_response.get("data"):
                    citing_papers.append(paper_response.get("data")[0])
            return citing_papers
        except Exception as e:
            logger.error(f"Error getting citing papers for {cited_paper_id}: {e}")
            raise

    def process_and_cite_paper(self, start_paper_id: str):
        """
        Process a paper using Semantic Scholar API and insert its details into the database.
        Optionally, cite the paper's references and update the citations table.
        """
        try:
            process_and_cite_paper(start_paper_id, self.client)
            logger.info("Processing complete.")
        except Exception as e:
            logger.error(f"Error processing paper {start_paper_id}: {e}")
            raise

    def get_paper_summary_by_semantic_id(self, semantic_id: str) -> dict:
        """
        Retrieve the summary columns for a given paper.
        """

        try:
            response = self.client.table("papers").select("summary").eq("semantic_id", semantic_id).execute()
            logger.info(f"Retrieved paper summary for {semantic_id}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting paper summary for {semantic_id}: {e}")
            raise

    def get_chunks_by_semantic_id(self, semantic_id: str) -> dict:
        """
        Retrieve all chunks for a given paper.
        """

        try:
            response = self.client.table("paper_chunks").select("*").eq("semantic_id", semantic_id).execute()
            logger.info(f"Retrieved chunks for paper {semantic_id}")
            return response.data
        except Exception as e:
            logger.error(f"Error getting chunks for paper {semantic_id}: {e}")
            raise
    
    def create_chunk(self, chunk: dict) -> dict:
        """
        Insert a new chunk record into the paper_chunks table.
        Expected keys: semantic_id, section_title, chunk_text.
        """
        try:
            response = self.client.table("paper_chunks").insert(chunk).execute()
            logger.info(f"Created chunk for paper {chunk.get('semantic_id')}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating chunk: {e}")
            raise

    def create_paper_comparison(self, paper_comparison: dict) -> dict:
        """
        Insert a new paper comparison record into the paper_comparisons table.
        Expected keys: semantic_id, comparison.
        """
        try:
            response = self.client.table("paper_comparisons").insert(paper_comparison).execute()
            logger.info(f"Created comparison for paper")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating comparison: {e}")
            raise

    def get_paper_comparison_by_semantic_id(self, semantic_id: str) -> dict:
        """
        Retrieve the comparison columns for a given paper.
        """

        try:
            response = self.client.table("paper_comparisons").select("comparison_data").eq("semantic_id", semantic_id).execute()
            logger.info(f"Retrieved paper comparison for {semantic_id}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting paper comparison for {semantic_id}: {e}")
            raise