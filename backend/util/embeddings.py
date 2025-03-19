import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine_similarity

def convert_pgvector(embedding_str: str) -> list[float]:
    """Convert a bracketed embedding string from pgvector into a Python list of floats."""
    embedding_str = embedding_str.strip()
    if embedding_str.startswith("[") and embedding_str.endswith("]"):
        embedding_str = embedding_str[1:-1]
    float_strs = embedding_str.split(",")
    return [float(val) for val in float_strs]

def mean_embedding_similarity(embeddings_A: list, embeddings_B: list) -> float:
    """Compute cosine similarity between the average embeddings of two papers."""
    arr_A = np.array(embeddings_A)
    arr_B = np.array(embeddings_B)
    mean_A = np.mean(arr_A, axis=0)
    mean_B = np.mean(arr_B, axis=0)
    return sk_cosine_similarity([mean_A], [mean_B])[0][0]

def pairwise_chunk_similarity(embeddings_A: list, embeddings_B: list) -> float:
    """For each chunk in Paper A, find the highest similarity with any chunk in Paper B, and vice versa."""
    arr_A = np.array(embeddings_A)
    arr_B = np.array(embeddings_B)
    sim_matrix = sk_cosine_similarity(arr_A, arr_B)
    max_sim_A = np.max(sim_matrix, axis=1)
    max_sim_B = np.max(sim_matrix, axis=0)
    return (np.mean(max_sim_A) + np.mean(max_sim_B)) / 2.0