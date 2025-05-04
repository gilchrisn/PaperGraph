"""
comparison_table_generation/embedding/retriever.py

Functions for retrieving relevant paper chunks using embeddings
"""

import numpy as np
from typing import List, Dict, Any, Callable
import logging
from ..core.models import PaperChunk

logger = logging.getLogger(__name__)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute the cosine similarity between two vectors.
    """
    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def retrieve_relevant_chunks(
    query_text: str, 
    chunks: List[PaperChunk], 
    generate_embedding: Callable,
    top_k: int = 3
) -> List[PaperChunk]:
    """
    Retrieve the top_k most relevant chunks based on cosine similarity 
    between the query embedding and each chunk's embedding.
    """
    if not chunks:
        logger.warning("No chunks provided for retrieval")
        return []
    
    # Generate embedding for the query
    query_embedding = generate_embedding(query_text)
    
    # Score each chunk based on similarity to the query
    scored_chunks = []
    for chunk in chunks:
        # Skip chunks without embeddings
        if not chunk.embedding:
            continue
        
        # Calculate similarity score
        score = cosine_similarity(query_embedding, chunk.embedding)
        scored_chunks.append((score, chunk))
    
    # Sort by score in descending order
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # Return the top_k chunks
    return [chunk for score, chunk in scored_chunks[:top_k]]


def mean_embedding_similarity(embeddings_A: List[List[float]], embeddings_B: List[List[float]]) -> float:
    """
    Compute similarity between two sets of embeddings using mean pooling.
    """
    if not embeddings_A or not embeddings_B:
        return 0.0
    
    arr_A = np.array(embeddings_A)
    arr_B = np.array(embeddings_B)
    mean_A = np.mean(arr_A, axis=0)
    mean_B = np.mean(arr_B, axis=0)
    return cosine_similarity(mean_A, mean_B)


def pairwise_chunk_similarity(embeddings_A: List[List[float]], embeddings_B: List[List[float]]) -> float:
    """
    Compute similarity between two sets of embeddings using pairwise comparisons.
    """
    if not embeddings_A or not embeddings_B:
        return 0.0
    
    arr_A = np.array(embeddings_A)
    arr_B = np.array(embeddings_B)
    
    # Calculate similarity matrix
    sim_matrix = np.zeros((len(arr_A), len(arr_B)))
    for i, emb_A in enumerate(arr_A):
        for j, emb_B in enumerate(arr_B):
            sim_matrix[i, j] = cosine_similarity(emb_A, emb_B)
    
    # Get maximum similarity for each element in A and B
    max_sim_A = np.max(sim_matrix, axis=1)
    max_sim_B = np.max(sim_matrix, axis=0)
    
    # Return the average of the two directions
    return (np.mean(max_sim_A) + np.mean(max_sim_B)) / 2.0


def compare_paper_embeddings(embeddings_A: List[List[float]], embeddings_B: List[List[float]], alpha: float = 0.6) -> float:
    """
    Combine the mean embedding similarity and pairwise chunk similarity into a single score.
    
    Parameters:
        embeddings_A: List of embeddings for paper A
        embeddings_B: List of embeddings for paper B
        alpha: Weight for pairwise similarity (1-alpha is weight for mean similarity)
    
    Returns:
        Combined similarity score between 0 and 1
    """
    if not embeddings_A or not embeddings_B:
        return 0.0
    
    mean_sim = mean_embedding_similarity(embeddings_A, embeddings_B)
    pairwise_sim = pairwise_chunk_similarity(embeddings_A, embeddings_B)
    
    return alpha * pairwise_sim + (1 - alpha) * mean_sim