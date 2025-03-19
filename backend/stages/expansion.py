from typing import List, Dict
from services.openai_service import prompt_chatgpt
from utils.parsing import parse_json_response

class ExpansionStage:
    def __init__(self, repository):
        self.repository = repository

    def run(self, paper_ids: List[str]) -> List[Dict]:
        """Run the expansion stage to generate criteria for each paper."""
        expanded_criteria = []
        for paper_id in paper_ids:
            criteria = self._generate_criteria_for_paper(paper_id)
            expanded_criteria.append({"paper_id": paper_id, "criteria": criteria})
        return expanded_criteria

    def _generate_criteria_for_paper(self, paper_id: str) -> List[Dict]:
        """Generate criteria for a single paper."""
        full_text = self._get_full_text(paper_id)
        prompt = self._build_prompt(full_text)
        response = prompt_chatgpt(prompt)
        return parse_json_response(response)

    def _get_full_text(self, paper_id: str) -> str:
        """Retrieve the full text of a paper."""
        chunks = self.repository.get_chunks_by_semantic_id(paper_id)
        return " ".join([chunk["chunk_text"] for chunk in chunks])

    def _build_prompt(self, full_text: str) -> str:
        """Build the prompt for generating criteria."""
        return f"""
        Generate a set of boolean criteria for the following paper:
        {full_text}
        """