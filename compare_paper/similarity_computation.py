# similarity_computation.py
from sklearn.metrics.pairwise import cosine_similarity

def compute_similarity(embeddings_1, embeddings_2):
    """
    Compute similarity scores for corresponding metrics between two papers.

    :param embeddings_1: Dictionary of embeddings for Paper 1
    :param embeddings_2: Dictionary of embeddings for Paper 2
    :return: Dictionary of similarity scores for each metric
    """
    similarities = {}
    for metric in embeddings_1.keys():
        if embeddings_1[metric] is not None and embeddings_2[metric] is not None:
            similarity = cosine_similarity(embeddings_1[metric], embeddings_2[metric])[0][0]
            similarities[metric] = similarity
        else:
            similarities[metric] = 0.0  # Assign 0 similarity if one or both metrics are missing
    return similarities

def compute_overall_similarity(similarity_scores, weights=None):
    """
    Compute an overall similarity score using weighted average.

    :param similarity_scores: Dictionary of similarity scores for each metric
    :param weights: Optional dictionary of weights for each metric
    :return: Overall similarity score
    """
    if not weights:
        weights = {metric: 1.0 for metric in similarity_scores.keys()}  # Equal weight for all metrics
    total_weight = sum(weights.values())
    weighted_similarity = sum(similarity_scores[metric] * weights.get(metric, 1.0) for metric in similarity_scores.keys())
    return weighted_similarity / total_weight