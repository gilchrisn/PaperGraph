"""
comparison_table_generation/content/all_chunks.py

Implementation of the All Chunks content generation strategy
"""

import logging
from typing import List, Dict, Callable, Any
from ..core.models import Paper, Criterion, TableCell
from .base import ContentGenerator

logger = logging.getLogger(__name__)


class AllChunksContentGenerator(ContentGenerator):
    """
    Implements the All Chunks approach for generating content:
    1. For each paper, generate one comprehensive prompt with all criteria
    2. Process all criteria at once for each paper
    """
    
    def __init__(self, prompt_chatgpt: Callable, **kwargs):
        super().__init__(prompt_chatgpt, **kwargs)
    
    def generate(self, papers: List[Paper], criteria: List[Criterion]) -> List[TableCell]:
        """Generate content with the All Chunks approach"""
        logger.info(f"Generating content with All Chunks for {len(papers)} papers and {len(criteria)} criteria")
        
        # Process each paper separately and collect the results
        paper_comparisons = {}
        for paper in papers:
            logger.debug(f"Processing paper: {paper.id}")
            paper_comparisons[paper.id] = self._process_paper(paper, criteria)
        
        # Convert the results into TableCell objects
        cells = []
        for criterion in criteria:
            for paper in papers:
                value = paper_comparisons.get(paper.id, {}).get(criterion.criterion)
                cell = TableCell(
                    paper_id=paper.id,
                    criterion=criterion.criterion,
                    value=value
                )
                cells.append(cell)
        
        return cells
    
    def _process_paper(self, paper: Paper, criteria: List[Criterion]) -> Dict[str, Any]:
        """Process all criteria for a single paper at once"""
        # Get the full text of the paper
        full_text = self._get_paper_full_text(paper)
        
        # Prepare the criteria text for the prompt
        criteria_text = "\n".join(
            f"Criterion: {crit.criterion}\nDescription: {crit.description}"
            for crit in criteria
        )
        
        prompt = f"""
        You are an expert research assistant.
        
        For the following paper with ID {paper.id}, consider the full text provided below:
        {full_text[:10000]}  # Limit text length for efficiency
        
        Evaluate the following criteria (each is a true/false question):
        {criteria_text}
        
        For each criterion, determine if the paper meets it.
        Provide your answers as a JSON object with the key "results" mapping to an object 
        where each key is the exact criterion name and the value is true, false, or "N/A".
        
        Note: If a criterion is not applicable to this paper, you can mark it as "N/A".

        Your response MUST be valid JSON (with no additional text) and follow the exact format:
        ```json
        {{
            "results": {{
                "Criterion 1": true,
                "Criterion 2": false,
                "Criterion 3": "N/A"
            }}
        }}
        ```
        """
        
        messages = [
            {"role": "system", "content": "You are an expert research assistant."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.prompt_chatgpt(messages, model="gpt-4o")
        
        from ..utils.parsers import parse_json_response
        try:
            parsed = parse_json_response(response)
            # The results should be a mapping of criterion names to boolean/null values
            results = parsed.get("results", {})
            return results
        except Exception as e:
            logger.error(f"Error processing paper {paper.id}: {e}")
            # Create default results (all None) if parsing fails
            return {crit.criterion: None for crit in criteria}
    
    def _get_paper_full_text(self, paper: Paper) -> str:
        """Get the full text of a paper by combining its chunks"""
        full_text = " ".join(f"{chunk.section_title}: {chunk.chunk_text}" for chunk in paper.chunks)
        return full_text