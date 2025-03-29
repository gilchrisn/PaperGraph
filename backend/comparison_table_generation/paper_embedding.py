import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine_similarity
from .paper_utils import convert_pgvector

def mean_embedding_similarity(embeddings_A: list, embeddings_B: list) -> float:
    arr_A = np.array(embeddings_A)
    arr_B = np.array(embeddings_B)
    mean_A = np.mean(arr_A, axis=0)
    mean_B = np.mean(arr_B, axis=0)
    return sk_cosine_similarity([mean_A], [mean_B])[0][0]

def pairwise_chunk_similarity(embeddings_A: list, embeddings_B: list) -> float:
    arr_A = np.array(embeddings_A)
    arr_B = np.array(embeddings_B)
    sim_matrix = sk_cosine_similarity(arr_A, arr_B)
    max_sim_A = np.max(sim_matrix, axis=1)
    max_sim_B = np.max(sim_matrix, axis=0)
    return (np.mean(max_sim_A) + np.mean(max_sim_B)) / 2.0

def compare_paper_embeddings(embeddings_A: list, embeddings_B: list, alpha: float = 0.6) -> float:
    """
    Combine the mean embedding similarity and pairwise chunk similarity into a single score.
    """
    mean_sim = mean_embedding_similarity(embeddings_A, embeddings_B)
    pairwise_sim = pairwise_chunk_similarity(embeddings_A, embeddings_B)
    return alpha * pairwise_sim + (1 - alpha) * mean_sim

def compare_two_papers(repository, main_paper_id: str, baseline_paper_id: str, alpha: float = 0.5) -> float:
    """
    Retrieve chunk embeddings for two papers from the repository and compute a combined similarity score.
    """
    main_chunks = repository.get_chunks_by_semantic_id(main_paper_id)
    baseline_chunks = repository.get_chunks_by_semantic_id(baseline_paper_id)

    embeddings_A = [convert_pgvector(chunk["embedding"]) for chunk in main_chunks if chunk.get("embedding")]
    embeddings_B = [convert_pgvector(chunk["embedding"]) for chunk in baseline_chunks if chunk.get("embedding")]

    if not embeddings_A or not embeddings_B:
        print("One or both papers have no valid embeddings.")
        return 0.0

    return compare_paper_embeddings(embeddings_A, embeddings_B, alpha=alpha)

def generate_embedding_for_paper_chunks(repository, paper_id: str, extract_all_sections, generate_embedding):
    """
    Generate embeddings for each section (chunk) of a paper and store them in the database.
    """
    chunks = repository.get_chunks_by_semantic_id(paper_id)
    if chunks:
        return chunks

    paper = repository.get_paper_by_semantic_id(paper_id)
    pdf_path = paper["local_filepath"]
    sections = extract_all_sections(pdf_path)

    for section, text in sections.items():
        embedding = generate_embedding(text)
        chunk = {
            "semantic_id": paper_id,
            "section_title": section,
            "chunk_text": text,
            "embedding": embedding
        }
        repository.create_chunk(chunk)

    return repository.get_chunks_by_semantic_id(paper_id)

def get_paper_chunks(repository, paper_id: str) -> list[dict]:
    """
    Retrieve the chunks of a paper from the database.
    """
    return repository.get_chunks_by_semantic_id(paper_id)

def retrieve_relevant_chunks(query_text: str, chunks: list[dict], generate_embedding, top_k=3) -> list[dict]:
    """
    Retrieve the top_k most relevant chunks based on cosine similarity between the query embedding and each chunk's embedding.
    """
    query_embedding = generate_embedding(query_text)
    scored_chunks = []
    for chunk in chunks:
        emb = chunk["embedding"]
        if isinstance(emb, str):
            emb = convert_pgvector(emb)
        score = sk_cosine_similarity(
            np.array(query_embedding).reshape(1, -1),
            np.array(emb).reshape(1, -1)
        )[0][0]
        scored_chunks.append((score, chunk))
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    return [chunk for score, chunk in scored_chunks[:top_k]]
