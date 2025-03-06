from paper_preprocessing.grobid_paper_extractor import  extract_all_sections
from openai_service.prompt_chatgpt import prompt_chatgpt, generate_embedding
from paper_repository import PaperRepository
import numpy as np
import os
from dotenv import load_dotenv
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine_similarity
import json


DUMMY_CRITERION = {
  "comparison_points": [
    {
      "criterion": "Model Architecture",
      "description": "Understanding the overall design and structure of the models being compared is important to identify fundamental differences and innovations, such as the use of attention mechanisms over traditional recurrent or convolutional layers."
    },
    {
      "criterion": "Experimental Design",
      "description": "The setup of experiments, including datasets, model variants, and hyperparameter tuning, is crucial as it affects the validity and reliability of the results reported. It determines how well the results can be reproduced and generalized."
    },
    {
      "criterion": "Attention Mechanisms",
      "description": "Attention mechanisms, especially the application of multi-head and self-attention, are central to the Transformer model. Comparing these mechanisms between papers can highlight advancements in handling sequence dependencies."
    },
    {
      "criterion": "Efficiency and Parallelization",
      "description": "Efficiency in terms of computation and the ability to parallelize tasks is a key performance metric, especially in large-scale machine learning tasks. This is critical for comparing training times and scalability."
    },
    {
      "criterion": "Performance Metrics",
      "description": "Metrics such as BLEU scores for translation and other relevant task-specific measurements are necessary to objectively compare the effectiveness of the models."
    },
    {
      "criterion": "Training Resources",
      "description": "The computational resources required for training, such as the number and type of GPUs, affect both the practicality and the economic feasibility of replicating and deploying the models."
    },
    {
      "criterion": "Innovation and Novelty",
      "description": "Assessing the novel contributions introduced by the model, such as entirely eschewing recurrence, helps to position the research within the landscape of technological advancements."
    },
    {
      "criterion": "Broader Applicability",
      "description": "The ability of the model to generalize across different tasks and domains, like language translation and parsing, demonstrates its robustness and versatility."
    },
    {
      "criterion": "Regularization Techniques",
      "description": "The application of techniques like dropout and label smoothing plays a crucial role in preventing overfitting and enhancing model performance."
    },
    {
      "criterion": "Availability of Code and Resources",
      "description": "Having publicly available code promotes transparency and reproducibility, allowing other researchers to verify results and build upon the work. It can also accelerate further research in the field."
    }
  ]
}

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API Key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

repository = PaperRepository()

def convert_pgvector(embedding_str: str) -> list[float]:
    """
    Convert a bracketed embedding string from pgvector into a Python list of floats.
    For example: "[0.04895872,0.0069324, ...]" -> [0.04895872, 0.0069324, ...]
    """
    # Remove surrounding brackets if present
    embedding_str = embedding_str.strip()
    if embedding_str.startswith("[") and embedding_str.endswith("]"):
        embedding_str = embedding_str[1:-1]  # remove leading '[' and trailing ']'

    # Split by commas and convert each piece to float
    # This assumes no extra spaces or formatting. If needed, you can do more robust parsing.
    float_strs = embedding_str.split(",")
    return [float(val) for val in float_strs]

def mean_embedding_similarity(embeddings_A: list, embeddings_B: list) -> float:
    """
    Compute cosine similarity between the average embeddings of two papers.
    """
    arr_A = np.array(embeddings_A)
    arr_B = np.array(embeddings_B)
    
    mean_A = np.mean(arr_A, axis=0)
    mean_B = np.mean(arr_B, axis=0)
    
    return sk_cosine_similarity([mean_A], [mean_B])[0][0]

def pairwise_chunk_similarity(embeddings_A: list, embeddings_B: list) -> float:
    """
    For each chunk in Paper A, find the highest similarity with any chunk in Paper B,
    and vice versa, then average these best-match scores.
    """
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
    print(mean_sim, pairwise_sim)

    return alpha * pairwise_sim + (1 - alpha) * mean_sim

def compare_two_papers(main_paper_id: str, baseline_paper_id: str, alpha: float = 0.5) -> float:
    """
    1. Retrieve chunk rows for each paper (main and baseline).
    2. For each chunk row, parse the bracketed embedding string from pgvector into a list of floats.
    3. Collect embeddings in a list for each paper.
    4. Compute combined similarity using mean and pairwise measures.
    """
    # Retrieve chunk rows from your repository. Each row has "embedding" as a bracketed string.
    main_chunks = repository.get_chunks_by_semantic_id(main_paper_id)       # e.g. [{'embedding': '[0.0489,0.0069,...]', ...}, ...]
    baseline_chunks = repository.get_chunks_by_semantic_id(baseline_paper_id)

    # Convert bracketed strings into lists of floats
    embeddings_A = []
    for chunk in main_chunks:
        if "embedding" in chunk and chunk["embedding"]:
            embedding_list = convert_pgvector(chunk["embedding"])  # parse the bracketed string
            embeddings_A.append(embedding_list)

    embeddings_B = []
    for chunk in baseline_chunks:
        if "embedding" in chunk and chunk["embedding"]:
            embedding_list = convert_pgvector(chunk["embedding"])
            embeddings_B.append(embedding_list)

    # If either paper has no valid embeddings, return 0 or handle accordingly
    if not embeddings_A or not embeddings_B:
        print("One or both papers have no valid embeddings.")
        return 0.0

    # Compute the combined similarity
    similarity_score = compare_paper_embeddings(embeddings_A, embeddings_B, alpha=alpha)
    return similarity_score

def parse_json_response(response):
    cleaned_response = response.strip().strip('```json')

    import json
    # Parse response into a dictionary
    response_dict = json.loads(cleaned_response)
    return response_dict


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Compute the cosine similarity between two vectors.
    """
    a = np.array(vec1)
    b = np.array(vec2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def generate_embedding_for_paper_chunks(paper_id: str):
    """
    Generate the embeddings for all the chunks of a paper and store them in the database.
    
    Parameters:
        paper_id (str): The semantic ID of the paper for which to generate embeddings.
    """

    # Dont generate embeddings if they already exist
    if repository.get_chunks_by_semantic_id(paper_id):
        return
    
    # Get the filepath
    pdf_path = repository.get_paper_by_semantic_id(paper_id)["local_filepath"]
    sections = extract_all_sections(pdf_path)
    
    for section in sections.keys():
        embedding = generate_embedding(sections[section])
        
        chunk = {
            "semantic_id": paper_id,
            "section_title": section,
            "chunk_text": sections[section],
            "embedding": embedding
        }
        
        repository.create_chunk(chunk)

    

def get_paper_chunks(paper_id: str) -> list[dict]:
    """
    Retrieve the chunks of a paper from the database.
    
    Parameters:
        paper_id (str): The semantic ID of the paper.
        
    Returns:
        list of dict: A list where each dict represents a chunk with keys:
            - "section_title": str,
            - "chunk_text": str,
            - "embedding": list[float] (the embedding vector for this chunk)
    """
    return repository.get_chunks_by_semantic_id(paper_id)

def retrieve_relevant_chunks(query_text: str, chunks: list[dict], top_k=3) -> list[dict]:
    """
    Retrieve the top_k most relevant chunks based on cosine similarity between the query embedding and each chunk's embedding.
    
    Parameters:
        query_text (str): The text query used to search for relevant chunks.
        chunks (list of dict): A list where each dict represents a chunk with keys:
            - "section_title": str,
            - "chunk_text": str,
            - "embedding": list[float] (the embedding vector for this chunk)
        top_k (int): The number of top relevant chunks to return.
        
    Returns:
        list of dict: The top_k chunk dictionaries sorted by highest cosine similarity.
    """
    # Generate the embedding for the query text
    query_embedding = generate_embedding(query_text)

    # Compute similarity score for each chunk and store the result with the chunk
    scored_chunks = []
    for chunk in chunks:
        array_query = np.array(query_embedding)
        array_chunk = np.array(chunk["embedding"])
        score = sk_cosine_similarity(array_query.reshape(1, -1), array_chunk.reshape(1, -1))[0][0]
        scored_chunks.append((score, chunk))
    
    # Sort chunks by descending similarity score
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # Return only the chunk dictionaries for the top_k results
    return [chunk for score, chunk in scored_chunks[:top_k]]


def generate_comparison_criteria(full_text):
    """
    Use the LLM to analyze a main paper's extracted sections and output its own criteria for comparing this paper with a closely related baseline.
    The goal is to create a comparison table similar to those found in survey papers.
    
    Parameters:
        full_text (str): The full text with extracted sections from the main paper.
        
    Returns:
        dict: A dictionary parsed from JSON, e.g., {"comparison_points": [ ... ]}.
    """
    
    prompt = f"""
    You are an expert research assistant tasked with creating a detailed survey-style comparison table.
    
    The goal is to compare a main research paper with a closely related baseline paper by identifying the most important aspects for evaluation.
    The following text contains the extracted sections (e.g., Methods, Results, Conclusion) of the main paper:
    
    {full_text}
    
    Please analyze the provided content and determine, on your own, which criteria are most relevant for comparing the main paper with a baseline paper.
    Your analysis should consider factors that are typically critical in academic comparisons, such as experimental design, statistical methods, performance metrics, novelty, and overall impact.
    
    For each criterion you identify, provide a short description explaining why that aspect is important for a survey-style comparison.
    
    Provide your output in valid JSON format with a single key "comparison_points" that maps to a list of objects.
    Each object should include:
      - "criterion": the name of the comparison aspect.
      - "description": a short explanation of its significance.
    
    The output should follow this format:
    ```json
    {{
      "comparison_points": [
        {{
          "criterion": "Criterion Name",
          "description": "Explanation of its significance."
        }}
      ]
    }}
    ```
    """
    
    messages = [
        {"role": "system", "content": "You are an expert research assistant."},
        {"role": "user", "content": prompt}
    ]
    
    response = prompt_chatgpt(messages, model="gpt-4o")
    response_dict = parse_json_response(response)
    
    return response_dict

def create_comparison_table(main_paper_id: str, baseline_paper_ids: list):
    """
    Generate a survey-style comparison table for a set of papers by comparing them across
    each criterion derived from the main paper.
    
    Workflow:
      1. Retrieve the main paper's chunks and combine them into a single text.
      2. Generate comparison criteria from the main paper (via LLM).
      3. Pre-fetch chunks for all papers (main + baseline) to avoid repeated DB calls.
      4. For each criterion, retrieve relevant excerpts from every paper using a RAG approach.
      5. Use LangChain's LLMChain to produce a structured, multi-paper comparison per criterion.
      6. Assemble the results into a unified JSON object.
      7. Save the comparison table into the database.
    
    Assumes that chunk embeddings are already stored in the database for each paper.
    
    Returns:
      list: Each entry is a dict with keys "criterion", "description", and "comparisons".
            "comparisons" is a dict mapping each paper_id to its comparison text.
    """
    # Build a list of all paper IDs: main paper + baseline papers.
    all_paper_ids = [main_paper_id] + baseline_paper_ids

    # 1. Retrieve main paper chunks and build full text.
    main_chunks = repository.get_chunks_by_semantic_id(main_paper_id)
    main_full_text = "\n".join([
        f"{chunk['section_title']}: {chunk['chunk_text']}"
        for chunk in main_chunks
    ])

    # 2. Generate comparison criteria from the main paper.
    criteria_dict = generate_comparison_criteria(main_full_text)
    # criteria_dict = DUMMY_CRITERION # For testing purposes
    criteria_list = criteria_dict.get("comparison_points", [])



    # 3. Pre-fetch chunks for all papers to avoid repeated DB calls.
    papers_chunks = {pid: repository.get_chunks_by_semantic_id(pid) for pid in all_paper_ids}
    # Convert the embedding strings to lists of floats
    for pid, chunks in papers_chunks.items():
        for chunk in chunks:
            if "embedding" in chunk and chunk["embedding"]:
                chunk["embedding"] = convert_pgvector(chunk["embedding"])

    comparison_table = []

    # 4. For each criterion, retrieve relevant excerpts from every paper.
    for criterion_obj in criteria_list:
        criterion_name = criterion_obj.get("criterion")
        criterion_description = criterion_obj.get("description")

        papers_excerpts = {}
        for pid in all_paper_ids:
            chunks = papers_chunks.get(pid, [])
            if not chunks:
                papers_excerpts[pid] = "No relevant details found."
                continue

            # Build a query string combining criterion name and description.
            query_text = f"{criterion_name} - {criterion_description}"
            
            # Retrieve relevant chunks using RAG.
            relevant_chunks = retrieve_relevant_chunks(query_text, chunks, top_k=3)
            excerpt_text = "\n".join([f"{c['section_title']}: {c['chunk_text']}" for c in relevant_chunks])
            papers_excerpts[pid] = excerpt_text if excerpt_text else "No relevant details found."

        # Consolidate excerpts into a single string.
        consolidated_excerpts = "\n\n".join([f"Paper {pid}: {text}" for pid, text in papers_excerpts.items()])
        
        # 5. Build a prompt to compare all papers for this criterion with structured JSON output.
        prompt = f"""
        You are an expert research assistant tasked with comparing multiple research papers based on a specific evaluation criterion.

        Instructions:
        - Compare each paper based on the given criterion.
        - Highlight key similarities, differences, and unique contributions.
        - Your response MUST be valid JSON (with no additional text) and follow the exact format provided below.
        
        Example Output (do not include this in your answer):
        ```json
        {{
            "criterion": "criterion_name",
            "comparisons": {{
                "paper_1": "Comparison details for Paper 1.",
                "paper_2": "Comparison details for Paper 2.",
                "paper_3": "Comparison details for Paper 3."
            }}
        }}
        ```

        Now, please provide your response in valid JSON format.

        Comparison Criterion:
        Criterion: {criterion_name}
        Description: {criterion_description}

        Relevant Excerpts:
        {consolidated_excerpts}
        """

        messages = [
            {"role": "system", "content": "You are an expert research assistant."},
            {"role": "user", "content": prompt}
        ]


        response = prompt_chatgpt(messages, model="gpt-4o")
        response_dict = parse_json_response(response)

        comparison_entries = response_dict.get("comparisons", {})
        print(comparison_entries)
        # 7. Save the result for this criterion.
        comparison_table.append({
            "criterion": criterion_name,
            "description": criterion_description,
            "comparisons": comparison_entries  # Structured as {paper_id: "comparison text"}
        })

    # 8. Save the complete comparison table in JSON format into the database.
    print(comparison_table)
    comparison_table_json = json.dumps(comparison_table)
    repository.create_paper_comparison({
        "semantic_id": main_paper_id,  # Using the main paper as the root.
        "comparison": comparison_table_json
    })
    return comparison_table

if __name__ == "__main__":
    paper_ids = ['204e3073870fae3d05bcbc2f6a8e263d9b72e776', 
                 'fa72afa9b2cbc8f0d7b05d52548906610ffbb9c5', 
                 'c8efcc854d97dfc2a42b83316a2109f9d166e43f',
                 '95a251513853c6032bdecebd4b74e15795662986',
                 '02417d57dec9215a0b66a63e9a70571c168de54b',
                 '07559ad8ccaf1110232a4be78f825691e8416d8c']

    # Generate the chunks for each paper
    generate_embedding_for_paper_chunks(paper_ids[5])

    # Compare 2 papers
    main_paper_id = paper_ids[0]
    baseline_paper_id = paper_ids[5]

    # Print the name of the papers
    main_paper_title = repository.get_paper_by_semantic_id(main_paper_id)["title"]
    baseline_paper_title = repository.get_paper_by_semantic_id(baseline_paper_id)["title"]
 

    similarity_score = compare_two_papers(main_paper_id, baseline_paper_id)
    print(f"Comparing papers: {main_paper_title} and {baseline_paper_title}")
    
    print(f"Similarity score between Paper A and Paper B: {similarity_score}")

    #
    # Generate the comparison table
    # comparison_table = create_comparison_table(paper_ids[0], paper_ids[1:])
    # print(comparison_table)
