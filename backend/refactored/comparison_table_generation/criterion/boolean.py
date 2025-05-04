"""
comparison_table_generation/criterion/boolean.py

Implementation of the boolean criterion generation strategy
"""

import logging
from typing import List, Dict, Callable, Any
from ..core.models import Paper, Criterion
from .base import CriterionGenerator

logger = logging.getLogger(__name__)


class BooleanCriterionGenerator(CriterionGenerator):
    """
    Implements the boolean approach for generating criteria:
    1. Generate boolean criteria for each paper independently
    2. Optionally expand non-boolean criteria
    3. Merge similar criteria across papers
    """
    
    def __init__(self, prompt_chatgpt: Callable, expand_iterations: int = 3, **kwargs):
        super().__init__(prompt_chatgpt, **kwargs)
        self.expand_iterations = expand_iterations
    
    def generate(self, papers: List[Paper]) -> List[Criterion]:
        """Generate criteria using the boolean approach"""
        logger.info(f"Generating boolean criteria for {len(papers)} papers")
        
        # Step 1: Generate criteria for each paper
        all_criteria = []
        for paper in papers:
            paper_criteria = self._generate_criteria_for_paper(paper)
            # Tag each criterion with its paper ID
            for criterion in paper_criteria:
                criterion.papers = [paper.id]
                all_criteria.append(criterion)
        
        logger.info(f"Generated {len(all_criteria)} criteria across all papers")
        
        # Step 2: Merge similar criteria
        merged_criteria = self._merge_criteria(all_criteria, papers)
        logger.info(f"Merged to {len(merged_criteria)} criteria")
        
        return merged_criteria
    
    def _generate_criteria_for_paper(self, paper: Paper) -> List[Criterion]:
        """
        Generate boolean criteria for a single paper,
        optionally expanding non-boolean criteria if expand_iterations > 0
        """
        full_text = self._get_paper_full_text(paper)
        
        if self.expand_iterations > 0:
            # Generate expandable criteria
            base_criteria = self._generate_expandable_boolean_criteria(paper.id, full_text)
            
            # Expand non-boolean criteria
            expanded = self._expand_non_boolean_criteria(paper.id, base_criteria, full_text)
            
            # Iteratively expand until no new criteria are added or
            # maximum iterations are reached
            iteration = 1
            while iteration < self.expand_iterations and len(expanded) > len(base_criteria):
                base_criteria = expanded
                expanded = self._expand_non_boolean_criteria(paper.id, base_criteria, full_text)
                iteration += 1
            
            return expanded
        else:
            # Generate direct boolean criteria only
            return self._generate_direct_boolean_criteria(paper.id, full_text)
    
    def _get_paper_full_text(self, paper: Paper) -> str:
        """Get the full text of a paper by combining its chunks"""
        return " ".join(chunk.chunk_text for chunk in paper.chunks)
    
    def _generate_direct_boolean_criteria(self, paper_id: str, full_text: str) -> List[Criterion]:
        """Generate strictly boolean criteria for a paper"""
        prompt = f"""
        You are an expert research assistant. We have a paper with ID: {paper_id}.
        Its content is as follows:
        {full_text[:5000]}  # Limit text length for efficiency
        
        Generate a list of super detailed 'boolean' criteria (i.e., true/false questions) that might be relevant
        for evaluating or comparing this paper. For each criterion, provide:
        - "criterion": a short title
        - "description": a one-sentence description and context
        - "is_boolean": set to true
        
        Your response MUST be valid JSON (with no additional text) and follow the exact format provided below.
        
        Return JSON with "criteria": [...]
        
        Example:
        ```json
        {{
            "criteria": [
                {{"criterion": "criteria1", "description": "description1", "is_boolean": true}},
                {{"criterion": "criteria2", "description": "description2", "is_boolean": true}}
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
        try:
            parsed = parse_json_response(response)
            criteria = []
            
            for item in parsed.get("criteria", []):
                criterion = Criterion(
                    criterion=item.get("criterion", ""),
                    description=item.get("description", ""),
                    papers=[paper_id],
                    is_boolean=item.get("is_boolean", True)
                )
                if self.validate_criterion(criterion):
                    criteria.append(criterion)
            
            return criteria
        except Exception as e:
            logger.error(f"Error parsing boolean criteria for paper {paper_id}: {e}")
            return []
    
    def _generate_expandable_boolean_criteria(self, paper_id: str, full_text: str) -> List[Criterion]:
        """Generate a mix of boolean and expandable criteria"""
        prompt = f"""
        You are an expert research assistant. We have a paper with ID: {paper_id}.
        Its content is as follows:
        {full_text[:5000]}  # Limit text length for efficiency
        
        Generate a list of super detailed 'boolean' criteria (i.e., true/false questions) that might be relevant
        for evaluating or comparing this paper, and true for this paper. If there are any criteria that need 
        further expansion, please provide a more detailed description that can be broken down into sub-criteria.
        
        For each criterion, provide:
        - "criterion": a short criteria
        - "description": a one-sentence description and context
        - "is_boolean": true if it's a true/false question, false if it needs further expansion
        
        Your response MUST be valid JSON (with no additional text) and follow the exact format provided below.
        
        Return JSON with "criteria": [...]
        
        Example:
        ```json
        {{
            "criteria": [
                {{"criterion": "criteria1", "description": "description1", "is_boolean": true}},
                {{"criterion": "criteria2", "description": "description2", "is_boolean": false}}
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
        try:
            parsed = parse_json_response(response)
            criteria = []
            
            for item in parsed.get("criteria", []):
                criterion = Criterion(
                    criterion=item.get("criterion", ""),
                    description=item.get("description", ""),
                    papers=[paper_id],
                    is_boolean=item.get("is_boolean", True)
                )
                if self.validate_criterion(criterion):
                    criteria.append(criterion)
            
            return criteria
        except Exception as e:
            logger.error(f"Error parsing expandable criteria for paper {paper_id}: {e}")
            return []
    
    def _expand_non_boolean_criteria(self, paper_id: str, criteria: List[Criterion], full_text: str) -> List[Criterion]:
        """Expand criteria that are not strictly boolean into multiple boolean criteria"""
        result = []
        
        # Add all boolean criteria directly
        boolean_criteria = [c for c in criteria if c.is_boolean]
        result.extend(boolean_criteria)
        
        # Expand non-boolean criteria
        for criterion in criteria:
            if not criterion.is_boolean:
                expanded = self._expand_criterion(paper_id, criterion, full_text)
                result.extend(expanded)
        
        return result
    
    def _expand_criterion(self, paper_id: str, criterion: Criterion, full_text: str) -> List[Criterion]:
        """Expand a single non-boolean criterion into multiple boolean criteria"""
        prompt = f"""
        We have a criterion that is not strictly boolean:
        Criterion: {criterion.criterion}
        Description: {criterion.description}
        
        Paper ID: {paper_id}
        Full text snippet from the paper:
        {full_text[:3000]}  # Limit text length for efficiency
        
        Please expand or refine this criterion into one or more sub-criteria that can be answered with true/false.
        The sub-criterion name must describe the content, while keeping it short.
        
        Return JSON with "expanded_criteria": a list of criteria objects
        (with "criterion", "description", "is_boolean").
        
        Example:
        ```json
        {{
            "expanded_criteria": [
                {{"criterion": "criteria1", "description": "description1", "is_boolean": true}},
                {{"criterion": "criteria2", "description": "description2", "is_boolean": true}}
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
        try:
            parsed = parse_json_response(response)
            expanded = []
            
            for item in parsed.get("expanded_criteria", []):
                expanded_criterion = Criterion(
                    criterion=item.get("criterion", ""),
                    description=item.get("description", ""),
                    papers=[paper_id],
                    is_boolean=item.get("is_boolean", True)
                )
                if self.validate_criterion(expanded_criterion):
                    expanded.append(expanded_criterion)
            
            return expanded
        except Exception as e:
            logger.error(f"Error expanding criterion for paper {paper_id}: {e}")
            # Return the original criterion as a fallback
            return [criterion]
    
    def _merge_criteria(self, all_criteria: List[Criterion], papers: List[Paper]) -> List[Criterion]:
        """Merge similar criteria across papers"""
        # Get a summary for each paper to provide context
        paper_summaries = {}
        for paper in papers:
            full_text = self._get_paper_full_text(paper)
            paper_summaries[paper.id] = self._generate_brief_summary(full_text)
        
        # Format criteria for the merge prompt
        combined_criteria_str = "\n".join(
            f"- Paper {c.papers[0]}: {c.criterion} => {c.description}"
            for c in all_criteria
        )
        
        combined_summaries_str = "\n".join(
            f"Paper {pid} summary: {text}" for pid, text in paper_summaries.items()
        )
        
        prompt = f"""
        We have criteria from multiple papers, possibly overlapping or similar.
        
        Summaries:
        {combined_summaries_str}
        
        All criteria:
        {combined_criteria_str}
        
        Please merge or group together any criteria that are essentially duplicates or very similar.
        Every criteria must remain a boolean (Yes/No).
        
        Return a JSON with "merged_criteria": an array of unique criteria objects.
        Each object must have:
          - "criterion": short text
          - "description": short description
          - "papers": list of paper_ids that share this criterion
          - "is_boolean": true
        """
        
        messages = [
            {"role": "system", "content": "You are an expert research assistant."},
            {"role": "user", "content": prompt}
        ]
        response = self.prompt_chatgpt(messages, model="gpt-4o")
        
        from ..utils.parsers import parse_json_response
        try:
            parsed = parse_json_response(response)
            merged = []
            
            for item in parsed.get("merged_criteria", []):
                merged_criterion = Criterion(
                    criterion=item.get("criterion", ""),
                    description=item.get("description", ""),
                    papers=item.get("papers", []),
                    is_boolean=item.get("is_boolean", True)
                )
                if self.validate_criterion(merged_criterion):
                    merged.append(merged_criterion)
            
            return merged
        except Exception as e:
            logger.error(f"Error merging criteria: {e}")
            # Fall back to the original criteria
            return all_criteria
    
    def _generate_brief_summary(self, full_text: str) -> str:
        """Generate a brief summary of a paper"""
        prompt = f"""
        You are an expert research assistant. Based on the following text from a research paper,
        generate a brief summary (3-5 sentences) that captures the essence of the paper.
        
        Text:
        {full_text[:3000]}  # Limit text length for efficiency
        """
        
        messages = [
            {"role": "system", "content": "You are an expert research assistant."},
            {"role": "user", "content": prompt}
        ]
        response = self.prompt_chatgpt(messages, model="gpt-4o")
        
        # For a simple summary, we can use the raw text response
        return response