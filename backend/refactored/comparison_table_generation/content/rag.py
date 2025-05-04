"""
comparison_table_generation/content/rag.py

Implementation of the RAG (Retrieval-Augmented Generation) content generation strategy
"""

import logging
from typing import List, Dict, Callable, Any
from ..core.models import Paper, Criterion, TableCell
from .base import ContentGenerator

logger = logging.getLogger(__name__)


class RAGContentGenerator(ContentGenerator):
    """
    Implements the RAG approach for generating content:
    1. For each criterion, retrieve relevant chunks from each paper
    2. Generate content for each paper-criterion combination using these chunks
    """
    
    def __init__(self, prompt_chatgpt: Callable, generate_embedding: Callable, top_k: int = 3, **kwargs):
        super().__init__(prompt_chatgpt, **kwargs)
        self.generate_embedding = generate_embedding
        self.top_k = top_k
    
    def generate(self, papers: List[Paper], criteria: List[Criterion]) -> List[TableCell]:
        """Generate content with the RAG approach"""
        logger.info(f"Generating content with RAG for {len(papers)} papers and {len(criteria)} criteria")
        
        table_cells = []
        
        # Process each criterion separately
        for criterion in criteria:
            logger.debug(f"Processing criterion: {criterion.criterion}")
            
            # Get relevant excerpts for each paper
            papers_excerpts = {}
            for paper in papers:
                excerpts = self._get_relevant_excerpts(criterion, paper)
                papers_excerpts[paper.id] = excerpts
            
            # Generate comparison table cells for this criterion
            criterion_cells = self._generate_criterion_cells(criterion, papers, papers_excerpts)
            table_cells.extend(criterion_cells)
        
        return table_cells
    
    def _get_relevant_excerpts(self, criterion: Criterion, paper: Paper) -> str:
        """Get relevant excerpts from a paper for a specific criterion"""
        query_text = f"{criterion.criterion} - {criterion.description}"
        
        # Use embeddings to find relevant chunks
        from ..embedding.retriever import retrieve_relevant_chunks
        relevant_chunks = retrieve_relevant_chunks(
            query_text=query_text,
            chunks=paper.chunks,
            generate_embedding=self.generate_embedding,
            top_k=self.top_k
        )
        
        # If no relevant chunks found
        if not relevant_chunks:
            return "No relevant details found."
        
        # Combine the relevant chunks into a single excerpt
        excerpt_text = "\n".join(f"{c.section_title}: {c.chunk_text}" for c in relevant_chunks)
        return excerpt_text
    
    def _generate_criterion_cells(
        self, 
        criterion: Criterion, 
        papers: List[Paper],
        papers_excerpts: Dict[str, str]
    ) -> List[TableCell]:
        """Generate table cells for a specific criterion across all papers"""
        
        # Build the consolidated excerpts for the prompt
        consolidated_excerpts = "\n\n".join(
            f"Paper {pid}: {text}" for pid, text in papers_excerpts.items()
        )
        
        prompt = f"""
        You are an expert research assistant tasked with comparing multiple research papers 
        based on a specific evaluation criterion.
        
        Instructions:
        - Compare each paper based on the given criterion.
        - Each cell should only be true, false or "N/A".
        - Your response MUST be valid JSON (with no additional text) and follow the exact format provided below.
        
        Note: If the criterion is not applicable to a paper, you can mark it as "N/A".
        
        Example Output (do not include this in your answer):
        ```json
        {{
            "criterion": "criterion_name",
            "description": "criterion_description",
            "comparisons": {{
                "<paper_1 id>": true,
                "<paper_2 id>": false,  
                "<paper_3 id>": "N/A"
            }}
        }}
        ```
        
        Now, please provide your response in valid JSON format.
        
        Comparison Criterion:
        Criterion: {criterion.criterion}
        Description: {criterion.description}
        
        Relevant Excerpts:
        {consolidated_excerpts}
        """
        
        messages = [
            {"role": "system", "content": "You are an expert research assistant."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.prompt_chatgpt(messages, model="gpt-4o")
        
        from ..utils.parsers import parse_json_response
        try:
            parsed = parse_json_response(response)
            comparisons = parsed.get("comparisons", {})
            
            cells = []
            for paper in papers:
                value = comparisons.get(paper.id)
                
                # Create a table cell
                cell = TableCell(
                    paper_id=paper.id,
                    criterion=criterion.criterion,
                    value=value
                )
                cells.append(cell)
            
            return cells
        except Exception as e:
            logger.error(f"Error generating cells for criterion {criterion.criterion}: {e}")
            
            # Create default cells if parsing fails
            cells = []
            for paper in papers:
                cell = TableCell(
                    paper_id=paper.id,
                    criterion=criterion.criterion,
                    value=None  # Null value indicates an error
                )
                cells.append(cell)
            
            return cells