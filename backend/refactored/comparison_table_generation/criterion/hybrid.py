"""
comparison_table_generation/criterion/hybrid.py

Implementation of the hybrid criterion generation strategy
"""

import logging
from typing import List, Dict, Callable, Any
from ..core.models import Paper, Criterion
from .base import CriterionGenerator

logger = logging.getLogger(__name__)


class HybridCriterionGenerator(CriterionGenerator):
    """
    Implements the hybrid approach for generating criteria:
    1. Generate initial criteria from aggregated summaries
    2. Refine criteria using retrieval-augmented generation
    3. Filter and merge similar criteria
    """
    
    def __init__(self, prompt_chatgpt: Callable, generate_embedding: Callable, **kwargs):
        super().__init__(prompt_chatgpt, **kwargs)
        self.generate_embedding = generate_embedding
    
    def generate(self, papers: List[Paper]) -> List[Criterion]:
        """Generate criteria using the hybrid approach"""
        logger.info(f"Generating criteria with hybrid approach for {len(papers)} papers")
        
        # Step 1: Generate paper summaries
        paper_summaries = self._generate_paper_summaries(papers)
        
        # Step 2: Generate initial criteria
        initial_criteria = self._generate_initial_criteria(papers, paper_summaries)
        logger.info(f"Generated {len(initial_criteria)} initial criteria")
        
        # Step 3: Refine each criterion
        refined_criteria = self._refine_criteria(initial_criteria, papers)
        logger.info(f"Refined to {len(refined_criteria)} criteria")
        
        # Step 4: Second-pass refinement
        final_criteria = self._refine_second_pass(refined_criteria, papers, paper_summaries)
        logger.info(f"Final refinement: {len(final_criteria)} criteria")
        
        return final_criteria
    
    def _generate_paper_summaries(self, papers: List[Paper]) -> Dict[str, str]:
        """Generate detailed summaries for each paper"""
        summaries = {}
        for paper in papers:
            full_text = self._get_paper_full_text(paper)
            summary = self._generate_detailed_summary(full_text)
            summaries[paper.id] = summary
        return summaries
    
    def _get_paper_full_text(self, paper: Paper) -> str:
        """Get the full text of a paper by combining its chunks"""
        return " ".join(chunk.chunk_text for chunk in paper.chunks)
    
    def _generate_detailed_summary(self, full_text: str) -> str:
        """Generate a detailed summary for a paper"""
        prompt = f"""
        You are an expert research assistant. Based on the following detailed text from a research paper, 
        generate an exhaustive list of bullet points that capture every aspect of the paper.
        
        Text:
        {full_text[:5000]}  # Limit text length for efficiency
        
        Return your answer as a JSON object with a key "bullet_points" mapping to a list of bullet points.
        Please do not use any LaTeX formatting (e.g., avoid sequences like \\( or \\)); 
        if mathematical notation is needed, please use plain text.
        """
        messages = [
            {"role": "system", "content": "You are an expert research assistant."},
            {"role": "user", "content": prompt}
        ]
        response = self.prompt_chatgpt(messages, model="gpt-4o")
        
        # Parse response based on your existing utility function
        # This would typically be in utils.parsers
        from ..utils.parsers import parse_json_response
        response_dict = parse_json_response(response)
        return response_dict.get("bullet_points", [])
    
    def _generate_initial_criteria(self, papers: List[Paper], summaries: Dict[str, str]) -> List[Criterion]:
        """Generate initial criteria from paper summaries"""
        # Similar to your existing generate_comparison_criteria_with_aggregated_summary
        combined_summary = "\n\n".join(f"{pid}: {summaries[pid]}" for pid in summaries)
        
        prompt = f"""
        You are an expert research assistant tasked with generating a set of evaluation criteria 
        based on the aggregated summaries of several research papers.
        
        Based on the following aggregated summaries, generate a list of high-level criteria that 
        capture the common themes, strengths, and weaknesses across these papers.
        
        Aggregated Summaries:
        {combined_summary}
        
        Return your answer in valid JSON format with a key "comparison_points" mapping to a list of objects.
        Each object must have:
        - "criterion": the name of the evaluation criterion.
        - "description": a brief explanation of its significance.
        
        Example:
        ```json
        {{
            "comparison_points": [
                {{
                    "criterion": "Evaluation Metrics",
                    "description": "Measures performance."
                }},
                {{
                    "criterion": "Experimental Design",
                    "description": "Describes setup and datasets."
                }}
            ]
        }}
        ```
        """
        
        messages = [
            {"role": "system", "content": "You are an expert research assistant."},
            {"role": "user", "content": prompt}
        ]
        response = self.prompt_chatgpt(messages, model="gpt-4o")
        
        from ..utils.parsers import parse_json_response
        response_dict = parse_json_response(response)
        
        # Convert to Criterion objects
        initial_criteria = []
        for point in response_dict.get("comparison_points", []):
            criterion = Criterion(
                criterion=point.get("criterion", ""),
                description=point.get("description", ""),
                papers=[],
                is_boolean=False
            )
            if self.validate_criterion(criterion):
                initial_criteria.append(criterion)
        
        return initial_criteria
    
    def _refine_criteria(self, criteria: List[Criterion], papers: List[Paper]) -> List[Criterion]:
        """Refine criteria using retrieval-augmented generation"""
        # Similar to your existing refine_criterion function
        refined_criteria = []
        
        for criterion in criteria:
            # Get relevant excerpts for this criterion from all papers
            combined_excerpts = self._get_relevant_excerpts(criterion, papers)
            
            prompt = f"""
            You are an expert research assistant tasked with refining an evaluation criterion 
            for comparing research papers.
            
            The existing criterion and description are provided below.
            
            Existing Criterion: {criterion.criterion}
            Existing Description: {criterion.description}
            
            Additional Detailed Excerpts from all papers:
            {combined_excerpts}
            
            Please provide a refined version of this criterion such that it is formulated as a true/false statement.
            Additionally, provide a refined and concise explanation (description) of why this true/false criterion 
            is important and how it captures the common themes or nuances across these papers.
            
            Return your answer in valid JSON format with the following keys:
            - "criterion": the refined true/false short 1-3 word statement that describes the criterion,
            - "description": a refined, concise explanation of the criterion.
            
            Your response MUST be valid JSON (with no additional text) and follow the exact format provided.
            """
            
            messages = [
                {"role": "system", "content": "You are an expert research assistant."},
                {"role": "user", "content": prompt}
            ]
            response = self.prompt_chatgpt(messages, model="gpt-4o")
            
            from ..utils.parsers import parse_json_response
            try:
                refined = parse_json_response(response)
                
                # Check if the response has the expected format
                for refined_point in refined.get("comparison_points", []):
                    refined_criterion = Criterion(
                        criterion=refined_point.get("criterion", criterion.criterion),
                        description=refined_point.get("description", criterion.description),
                        papers=[p.id for p in papers],
                        is_boolean=True
                    )
                    if self.validate_criterion(refined_criterion):
                        refined_criteria.append(refined_criterion)
            except Exception as e:
                logger.error(f"Error refining criterion: {e}")
                # Fall back to the original criterion
                refined_criteria.append(criterion)
        
        return refined_criteria
    
    def _get_relevant_excerpts(self, criterion: Criterion, papers: List[Paper]) -> str:
        """Get relevant excerpts from papers for a specific criterion"""
        # Similar to your existing retrieve_relevant_chunks function
        combined_excerpts = ""
        for paper in papers:
            query_text = f"{criterion.criterion} - {criterion.description}"
            
            # Use embeddings to find relevant chunks
            from ..embedding.retriever import retrieve_relevant_chunks
            relevant_chunks = retrieve_relevant_chunks(
                query_text=query_text,
                chunks=paper.chunks,
                generate_embedding=self.generate_embedding,
                top_k=3
            )
            
            excerpt_text = "\n".join(f"{c.section_title}: {c.chunk_text}" for c in relevant_chunks)
            combined_excerpts += f"Paper {paper.id}:\n{excerpt_text}\n\n"
        
        return combined_excerpts
    
    def _refine_second_pass(self, criteria: List[Criterion], papers: List[Paper], summaries: Dict[str, str]) -> List[Criterion]:
        """Final refinement pass to filter out controversial or non-insightful criteria"""
        # Similar to your existing refine_criteria_second_pass function
        combined_summaries = "\n".join(
            f"Paper {pid} Summary: {summary}" for pid, summary in summaries.items()
        )
        
        combined_criteria = "\n".join(
            f"Criterion: {crit.criterion} | Description: {crit.description} | Papers: {crit.papers}"
            for crit in criteria
        )
        
        prompt = f"""
        You are an expert research assistant. We have a set of merged evaluation criteria gathered 
        from multiple research papers.
        
        As a final quality control step, please review these criteria using the context 
        from the paper summaries below.
        
        Context Summaries:
        {combined_summaries}
        
        Merged Criteria:
        {combined_criteria}
        
        Instructions:
        - Remove any criteria that may be considered controversial or that do not provide insightful evaluation.
        - Only FILTER, do not add new criteria or modify existing ones.
        - Maintain the association with the paper IDs that originally contributed to the criterion.
        
        Return your answer as valid JSON with a key "refined_criteria" mapping to a list of objects.
        Each object must have:
          - "criterion": <unmodified criterion>,
          - "description": <unmodified description>,
          - "papers": a list of paper IDs that support this criterion.
          
        Your response MUST be valid JSON (with no additional text) and follow the exact format provided.
        """
        
        messages = [
            {"role": "system", "content": "You are an expert research assistant."},
            {"role": "user", "content": prompt}
        ]
        
        response = self.prompt_chatgpt(messages, model="gpt-4o")
        
        from ..utils.parsers import parse_json_response
        try:
            parsed = parse_json_response(response)
            refined_criteria = []
            
            for item in parsed.get("refined_criteria", []):
                criterion = Criterion(
                    criterion=item.get("criterion", ""),
                    description=item.get("description", ""),
                    papers=item.get("papers", []),
                    is_boolean=True
                )
                if self.validate_criterion(criterion):
                    refined_criteria.append(criterion)
            
            return refined_criteria
        except Exception as e:
            logger.error(f"Error in second-pass refinement: {e}")
            # Fall back to the original criteria
            return criteria