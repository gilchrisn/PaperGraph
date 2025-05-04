"""
comparison_table_generation/utils/converters.py

Utility functions for converting between data formats
"""

import numpy as np
from typing import List, Dict, Any
from ..core.models import Paper, PaperChunk, Criterion, TableCell, ComparisonTable


def convert_pgvector(embedding_str: str) -> List[float]:
    """
    Convert a bracketed embedding string from pgvector into a Python list of floats.
    For example: "[0.04895872,0.0069324,...]" -> [0.04895872, 0.0069324, ...]
    """
    embedding_str = embedding_str.strip()
    if embedding_str.startswith("[") and embedding_str.endswith("]"):
        embedding_str = embedding_str[1:-1]  # remove the surrounding brackets
    float_strs = embedding_str.split(",")
    return [float(val) for val in float_strs]


def convert_repo_paper_to_model(repo_paper: Dict[str, Any], chunks: List[Dict[str, Any]]) -> Paper:
    """
    Convert a paper record from the repository format to the model format.
    
    Parameters:
        repo_paper: Paper record from the repository
        chunks: List of chunk records from the repository
        
    Returns:
        Paper object in the model format
    """
    model_chunks = []
    for chunk in chunks:
        embedding = chunk.get("embedding")
        if isinstance(embedding, str):
            embedding = convert_pgvector(embedding)
        
        model_chunks.append(
            PaperChunk(
                paper_id=chunk.get("semantic_id"),
                section_title=chunk.get("section_title", ""),
                chunk_text=chunk.get("chunk_text", ""),
                embedding=embedding
            )
        )
    
    return Paper(
        id=repo_paper.get("semantic_id"),
        title=repo_paper.get("title", ""),
        content="",  # Will be populated from chunks if needed
        embedding=None,  # Paper-level embedding is typically not used
        metadata=repo_paper,
        chunks=model_chunks
    )


def convert_repo_comparison_to_model(
    repo_comparison: Dict[str, Any],
    papers: List[Paper]
) -> ComparisonTable:
    """
    Convert a comparison table from the repository format to the model format.
    
    Parameters:
        repo_comparison: Comparison record from the repository
        papers: List of Paper objects
        
    Returns:
        ComparisonTable object in the model format
    """
    comparison_data = repo_comparison.get("comparison_data", [])
    
    criteria = []
    cells = []
    
    for entry in comparison_data:
        criterion = Criterion(
            criterion=entry.get("criterion", ""),
            description=entry.get("description", ""),
            papers=[p.id for p in papers],
            is_boolean=True
        )
        criteria.append(criterion)
        
        comparisons = entry.get("comparisons", {})
        for paper in papers:
            value = comparisons.get(paper.id)
            cell = TableCell(
                paper_id=paper.id,
                criterion=criterion.criterion,
                value=value
            )
            cells.append(cell)
    
    return ComparisonTable(
        papers=papers,
        criteria=criteria,
        cells=cells
    )