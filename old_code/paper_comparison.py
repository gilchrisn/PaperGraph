from backend.comparison_table_generation.grobid_service import  extract_all_sections
from openai_service.prompt_chatgpt import prompt_chatgpt, generate_embedding
from backend.repository.paper_repository import PaperRepository
import numpy as np
import os
from dotenv import load_dotenv
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as sk_cosine_similarity
import json
import re

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
    cleaned_response = re.sub(r"^```json\s*|```$", "", response.strip()).strip()
    cleaned_response = cleaned_response.replace("'", '"')

    print("Cleaned Response:")
    print(cleaned_response)
    print("\n" * 5)

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
    chunks = repository.get_chunks_by_semantic_id(paper_id)
    if chunks:
        return chunks
    
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


    return repository.get_chunks_by_semantic_id(paper_id)

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
        emb = chunk["embedding"]
        if isinstance(emb, str):
            emb = convert_pgvector(emb)
        array_query = np.array(query_embedding)
        array_chunk = np.array(emb)
        score = sk_cosine_similarity(array_query.reshape(1, -1), array_chunk.reshape(1, -1))[0][0]
        scored_chunks.append((score, chunk))
    
    # Sort chunks by descending similarity score
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # Return only the chunk dictionaries for the top_k results
    return [chunk for score, chunk in scored_chunks[:top_k]]


# def generate_comparison_criteria_with_main_paper(main_paper_id: str):
#     """
#     Use the LLM to analyze a main paper's extracted sections and output its own criteria for comparing this paper with a closely related baseline.
#     The goal is to create a comparison table similar to those found in survey papers.
    
#     Parameters:
#         full_text (str): The full text with extracted sections from the main paper.
        
#     Returns:
#         dict: A dictionary parsed from JSON, e.g., {"comparison_points": [ ... ]}.
#     """

#     # Retrieve the chunks for the main paper
#     chunks = get_paper_chunks(main_paper_id)

#     # Combine all chunk texts into a single string
#     full_text = " ".join([chunk["chunk_text"] for chunk in chunks])
    
#     prompt = f"""
#     You are an expert research assistant tasked with creating a detailed survey-style comparison table.
    
#     The goal is to compare a main research paper with a closely related baseline paper by identifying the most important aspects for evaluation.
#     The following text contains the extracted sections (e.g., Methods, Results, Conclusion) of the main paper:
    
#     {full_text}
    
#     Please analyze the provided content and determine, on your own, which criteria are most relevant for comparing the main paper with a baseline paper.
#     Your analysis should consider factors that are typically critical in academic comparisons, such as experimental design, statistical methods, performance metrics, novelty, and overall impact.
    
#     For each criterion you identify, provide a short description explaining why that aspect is important for a survey-style comparison.
    
#     Provide your output in valid JSON format with a single key "comparison_points" that maps to a list of objects.
#     Each object should include:
#       - "criterion": the name of the comparison aspect.
#       - "description": a short explanation of its significance.
    
#     The output should follow this format:
#     ```json
#     {{
#       "comparison_points": [
#         {{
#           "criterion": "Criterion Name",
#           "description": "Explanation of its significance."
#         }}
#       ]
#     }}
#     ```
#     """
    
#     messages = [
#         {"role": "system", "content": "You are an expert research assistant."},
#         {"role": "user", "content": prompt}
#     ]
    
#     response = prompt_chatgpt(messages, model="gpt-4o")
#     response_dict = parse_json_response(response)
    
#     return response_dict

def generate_detailed_summary(full_text: str) -> list:
    """
    Use the LLM to generate detailed bullet points summarizing the key aspects of a paper.
    The bullet points should capture:
      - The methodology and key techniques used.
      - The experimental design, including datasets and evaluation metrics.
      - The main results and their significance.
      - Innovative contributions and novel aspects.
      - Limitations and unique insights.
    
    Parameters:
      full_text (str): The detailed text of the paper.
    
    Returns:
      list: A list of bullet points (strings) capturing the detailed discussion of the paper.
    """

    prompt = f"""
    You are an expert research assistant. Based on the following detailed text from a research paper, generate an exhaustive list of bullet points that capture every aspect of the paper in a super detailed and specific manner. Include every key detail discussed in the paper—whether it is about the methodology, experimental design, results, innovations, limitations, or any other critical points that contribute to understanding the work.

    Text:
    {full_text}

    Return your answer as a JSON object with a single key "bullet_points" that maps to a list of bullet points.
    Ensure that any double quotes within the bullet points are escaped using a backslash (\").

    For example:
    ```json
    {{
        "bullet_points": [
            "Detailed description of the methodology used, including all techniques and their rationales.",
            "Thorough breakdown of the experimental design, including datasets, evaluation metrics, and training configurations.",
            "Comprehensive summary of the main results and their significance, with numeric details if available.",
            "Extensive discussion of innovative contributions and novel ideas introduced in the paper.",
            "Critical analysis of limitations and any unique insights that impact the interpretation of the results."
        ]
    }}
    ```
    """

    messages = [
            {"role": "system", "content": "You are an expert research assistant."},
            {"role": "user", "content": prompt}
        ]

    response = prompt_chatgpt(messages, model="gpt-4o")

    try:

        response_dict = parse_json_response(response)

        return response_dict.get("bullet_points", [])
    except Exception as e:
        print("Error parsing detailed summary:", e)
        return []

def generate_comparison_criteria_with_aggregated_summary(paper_ids: list, mode: str = "detailed"):
    """
    Generate comparison criteria by aggregating the summaries of multiple papers and identifying common themes.
    
    Parameters:
        paper_ids (list): A list of paper IDs.
        mode (str): "detailed" for super detailed bullet points, or "general" for a more high-level summary.
    
    Returns:
        dict: A dictionary, e.g.:
        {
            "comparison_points": [
                {
                    "criterion": "Evaluation Metrics",
                    "description": "Captures performance measures used."
                },
                ...
            ]
        }
    """
    # Retrieve the full text for each paper by combining its extracted sections.
    full_texts = {}
    for paper_id in paper_ids:
        chunks = get_paper_chunks(paper_id)
        full_text = " ".join([chunk["chunk_text"] for chunk in chunks])
        full_texts[paper_id] = full_text

    # Generate summaries for each paper.
    summaries = {}
    for paper_id, full_text in full_texts.items():
        summaries[paper_id] = generate_detailed_summary(full_text)


    # Combine all summaries into a single aggregated text.
    combined_summary = "\n\n".join([f"{pid}: {summaries[pid]}" for pid in summaries])
    
    # Build the prompt for generating unified comparison criteria.
    if mode == "detailed":
        prompt = f"""
        You are an expert research assistant tasked with generating a set of evaluation criteria based on the aggregated, detailed summaries of several research papers.
        Based on the following aggregated detailed summaries, generate a list of criteria that capture all the nuances, strengths, weaknesses, and key points discussed in these papers.
        Aggregated Detailed Summaries:
        {combined_summary}
        Return your answer in valid JSON format with a key "comparison_points" mapping to a list of objects.
        Each object must have:
        - "criterion": the name of the evaluation criterion.
        - "description": a short explanation of its significance.
        Example:
        ```json
        {{
        "comparison_points": [
            {{
            "criterion": "Evaluation Metrics",
            "description": "Captures performance measures such as BLEU, ROUGE, etc."
            }},
            {{
            "criterion": "Experimental Design",
            "description": "Highlights methodology and datasets."
            }}
        ]
        }}
        ```

        Ensure that any double quotes within the bullet points are escaped using a backslash (\").
        """ 
    else: 
        # general mode 
        prompt = f""" You are an expert research assistant tasked with generating a set of evaluation criteria based on the aggregated summaries of several research papers. 
        Based on the following aggregated summaries, generate a list of high-level criteria that capture the common themes, strengths, and weaknesses across these papers. 
        Aggregated Summaries: 
        {combined_summary} 
        Return your answer in valid JSON format with a key "comparison_points" mapping to a list of objects. Each object must have:
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

        Ensure that any double quotes within the bullet points are escaped using a backslash (\").
        """

    messages = [
        {"role": "system", "content": "You are an expert research assistant."},
        {"role": "user", "content": prompt}
    ]

    response = prompt_chatgpt(messages, model="gpt-4o")
    try:
        response_dict = parse_json_response(response)
        return response_dict
    except Exception as e:
        print("Error parsing response:", e)
        return {}


def refine_criterion(criterion: dict, paper_ids: list) -> dict:
    """
    Refine a given evaluation criterion by retrieving additional details from all papers
    (using RAG) and prompting the LLM to update the criterion and its description.
    
    Parameters:
      criterion (dict): An object with keys "criterion" and "description" from the initial generation.
      paper_ids (list): A list of all paper IDs being compared.
    
    Returns:
      dict: A refined criterion with keys "criterion" and "description".
    """
    # For each paper, retrieve its chunks and get the top relevant excerpts.
    combined_excerpts = ""
    for pid in paper_ids:
        chunks = get_paper_chunks(pid)
        query_text = f"{criterion['criterion']} - {criterion['description']}"
        relevant_chunks = retrieve_relevant_chunks(query_text, chunks, top_k=3)
        excerpt_text = "\n".join([f"{c['section_title']}: {c['chunk_text']}" for c in relevant_chunks])
        combined_excerpts += f"Paper {pid}:\n{excerpt_text}\n\n"
    
    # Build a prompt that includes the current criterion and the additional detailed excerpts.
    prompt = f"""
    You are an expert research assistant tasked with refining an evaluation criterion for comparing research papers.
    Existing Criterion: {criterion['criterion']}
    Existing Description: {criterion['description']}

    Additional Detailed Excerpts from all papers:
    {combined_excerpts}

    Please provide a refined version of this criterion that more accurately captures the common themes and nuances discussed across these papers.
    Return your answer in valid JSON format with the following keys:
    - "criterion": the refined criterion (a short label),
    - "description": a refined, concise description.

    Example:
    ```json
    {{
        "comparison_points": [
            {{
                "criterion": "Detailed Criterion 1", 
                "description": "Description of the refined criterion."
            }},
            {{
                "criterion": "Detailed Criterion 2",
                "description": "Description of the refined criterion."
            }}
        ]

    }}
    ```

    Ensure that any double quotes within the bullet points are escaped using a backslash (\").
    """

    messages = [
        {"role": "system", "content": "You are an expert research assistant."},
        {"role": "user", "content": prompt}
    ]
    
    response = prompt_chatgpt(messages, model="gpt-4o")
    try:
        refined = parse_json_response(response)
    except Exception as e:
        print("Error refining criterion:", e)
        # Fallback: return the original criterion if parsing fails.
        refined = {"criterion": criterion["criterion"], "description": criterion["description"]}
    return refined

def generate_comparison_criteria_with_hybrid_approach(paper_ids: list) -> dict:
    """
    Generate evaluation criteria using an aggregated summary method, then refine each criterion using RAG.
    
    This method first aggregates detailed summaries for each paper, then generates initial criteria.
    Next, for each criterion, it retrieves relevant excerpts from all papers and asks the LLM to refine that criterion.
    
    Returns:
      dict: A dictionary with key "comparison_points" mapping to a list of refined criterion objects.
            Each object has:
              - "criterion": the refined criterion (a short label),
              - "description": the refined, concise description.
    """
    # First, generate initial criteria using the aggregated summary approach.
    # initial_output = generate_comparison_criteria_with_aggregated_summary(paper_ids, mode="general")
    initial_output = DUMMY_CRITERION

    # Expect initial_output to be a dict with key "comparison_points"
    initial_criteria = initial_output.get("comparison_points", [])
    
    refined_criteria = {"comparison_points": []}
    
    # For each initially generated criterion, refine it using additional context from all papers.
    for crit in initial_criteria:
        refined_list = refine_criterion(crit, paper_ids)
        print("Refined Criteria:", refined_list)
        for refined in refined_list["comparison_points"]:
            refined_criteria["comparison_points"].append(refined)
            
    print("Refined Criteria:", refined_criteria)
    return refined_criteria


def create_comparison_table(main_paper_id: str, baseline_paper_ids: list, mode: str = "hybrid"):
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
    # Return early if the comparison table already exists
    if repository.get_paper_comparison_by_semantic_id(main_paper_id):
        return repository.get_paper_comparison_by_semantic_id(main_paper_id)
    
    # Build a list of all paper IDs: main paper + baseline papers.
    all_paper_ids = [main_paper_id] + baseline_paper_ids

    # 2. Generate comparison criteria from the main paper.
    if mode == "hybrid":
        criteria_list = generate_comparison_criteria_with_hybrid_approach(all_paper_ids)["comparison_points"]
    elif mode == "aggregated":
        criteria_list = generate_comparison_criteria_with_aggregated_summary(all_paper_ids, mode="detailed")["comparison_points"]

    print("Criteria List:", criteria_list)
    
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
        - Provide your answer in the most concise manner possible: each paper’s response should be around 1-3 words. Only go beyond if really necessary.
        - Your response MUST be valid JSON (with no additional text) and follow the exact format provided below. Ensure that any double quotes within the bullet points are escaped using a backslash (\").

        Example Output (do not include this in your answer):
        ```json
        {{
            "criterion": "criterion_name",
            "comparisons": {{
                "<paper_1 id>": "Sentence comparing paper 1.",
                "<paper_2 id>": "Sentence comparing paper 2.",
                "<paper_3 id>": "Sentence comparing paper 3."
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

        # 7. Save the result for this criterion.
        comparison_table.append({
            "criterion": criterion_name,
            "description": criterion_description,
            "comparisons": comparison_entries  # Structured as {paper_id: "comparison text"}
        })

    # 8. Save the complete comparison table in JSON format into the database.
    repository.create_paper_comparison({
        "semantic_id": main_paper_id,  # Using the main paper as the root.
        "comparison_data": comparison_table
    })
    return comparison_table

# =================
# VISUALIZATION
# =================
import tkinter as tk
from tkinter import ttk
import json
import webbrowser

# Simple Tooltip class with bounds checking and updating.
class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None

    def showtip(self, text, x, y):
        "Display text in tooltip window at x,y, adjusting if needed."
        if self.tipwindow:
            # If the tooltip is already displayed, update its text and reposition.
            label = self.tipwindow.children.get("label")
            if label:
                label.config(text=text)
            self.tipwindow.wm_geometry(f"+{x}+{y}")
            return
        if not text:
            return
        # Get screen dimensions.
        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        max_width = 400
        label = tk.Label(tw, name="label", text=text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("Helvetica", 10), wraplength=max_width)
        label.pack(ipadx=5, ipady=3)
        tw.update_idletasks()
        tw_width = tw.winfo_reqwidth()
        tw_height = tw.winfo_reqheight()
        if x + tw_width > screen_width:
            x = screen_width - tw_width - 10
        if y + tw_height > screen_height:
            y = screen_height - tw_height - 10
        tw.wm_geometry(f"+{x}+{y}")

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

def display_comparison_table(main_paper_id: str):
    """
    Retrieve the comparison table for a main paper from the database,
    parse it, and display it in a window in a tabular format.
    
    The comparison table JSON is expected to be a list of dicts with keys:
      - criterion
      - description
      - comparisons: a dict mapping paper IDs to their comparison text.
    
    Additionally:
      - Hovering over a header shows the paper title and its relevance score.
      - Hovering over a cell shows the full cell text along with the relevance score.
      - Clicking a header opens the paper's PDF.
    """
    # Retrieve the JSON comparison table.
    comparison_table = repository.get_paper_comparison_by_semantic_id(main_paper_id)["comparison_data"]
    
    # Extract all paper IDs from the comparisons.
    paper_ids = set()
    for entry in comparison_table:
        comps = entry.get("comparisons", {})
        paper_ids.update(comps.keys())
    paper_ids = sorted(list(paper_ids))
    
    # Build mapping: paper_id -> title, and paper_id -> PDF URL.
    paper_titles = {}
    paper_pdf_urls = {}
    paper_years = {}
    paper_venues = {}
    for pid in paper_ids:
        paper = repository.get_paper_by_semantic_id(pid)
        if paper:
            paper_titles[pid] = paper.get("title", pid)
            paper_pdf_urls[pid] = paper.get("open_access_pdf", None)
            paper_years[pid] = paper.get("year", "N/A")
            paper_venues[pid] = paper.get("venue", "N/A")
        else:
            paper_titles[pid] = pid
            paper_pdf_urls[pid] = None
            paper_years[pid] = "N/A"
            paper_venues[pid] = "N/A"


    # Build mapping: paper_id -> relevance score
    paper_relevance = {}
    for pid in paper_ids:
        relation = repository.get_relation_by_source_and_target(main_paper_id, pid)
        print(main_paper_id, pid)
        if relation and relation.get("relevance_score") is not None:
            paper_relevance[pid] = relation["relevance_score"]
        else:
            paper_relevance[pid] = "N/A"

    # Create the Tkinter window, full-screen.
    root = tk.Tk()
    root.title(f"Comparison Table for Paper {main_paper_id}")
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}")
    
    # Configure style for better appearance.
    style = ttk.Style(root)
    style.configure("Treeview", rowheight=50, font=("Helvetica", 10))
    style.configure("Treeview.Heading", font=("Helvetica", 12, "bold"))
    
    # Create a Frame to hold the Treeview and scrollbars.
    frame = tk.Frame(root)
    frame.pack(expand=True, fill="both")
    
    # Create vertical and horizontal scrollbars.
    vscroll = tk.Scrollbar(frame, orient="vertical")
    hscroll = tk.Scrollbar(frame, orient="horizontal")
    
    # Create a Treeview widget with scrollbars.
    tree = ttk.Treeview(frame, yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
    vscroll.config(command=tree.yview)
    hscroll.config(command=tree.xview)
    vscroll.pack(side="right", fill="y")
    hscroll.pack(side="bottom", fill="x")
    tree.pack(expand=True, fill="both")
    
    # Define columns: first column is for "Criterion", then one for each paper id.
    columns = ["Criterion"] + paper_ids
    tree["columns"] = columns[1:]  # "#0" is used for the Criterion column.
    tree.heading("#0", text="Criterion")
    tree.column("#0", anchor="w", width=250, minwidth=250)
    
    for col in columns[1:]:
        tree.heading(col, text=col)
        tree.column(col, anchor="w", width=300, minwidth=300)
    
    # Optional: Add alternating row colors for readability.
    tree.tag_configure('oddrow', background='lightblue')
    tree.tag_configure('evenrow', background='white')
    
    # Insert rows into the Treeview.
    for idx, entry in enumerate(comparison_table):
        criterion = entry.get("criterion", "")
        comparisons = entry.get("comparisons", {})
        row_values = []
        for pid in paper_ids:
            cell_text = comparisons.get(pid, "No relevant details found.")
            row_values.append(cell_text)
        tag = 'oddrow' if idx % 2 == 0 else 'evenrow'
        tree.insert("", "end", text=criterion, values=row_values, tags=(tag,))
    
    # Create a global tooltip instance.
    tooltip = ToolTip(tree)
    
    # Bind mouse motion to update tooltip.
    def on_motion(event):
        region = tree.identify("region", event.x, event.y)
        if region == "heading":
            col = tree.identify_column(event.x)
            try:
                index = int(col.replace("#", "")) - 1  # Adjust: "#0" is criterion.
                if 0 <= index < len(paper_ids):
                    pid = paper_ids[index]
                    title = paper_titles.get(pid, pid)
                    year = paper_years.get(pid, "N/A")
                    venue = paper_venues.get(pid, "N/A")
                    relevance = paper_relevance.get(pid, "N/A")
                    display_text = f"{title}\nYear: {year}\nVenue: {venue}\nRelevance: {relevance}"
                    tooltip.showtip(display_text, event.x_root + 20, event.y_root + 10)
                else:
                    tooltip.hidetip()
            except Exception:
                tooltip.hidetip()
        elif region == "cell":
            row_id = tree.identify_row(event.y)
            col = tree.identify_column(event.x)
            if row_id and col:
                item = tree.item(row_id)
                if col == "#0":
                    cell_text = item.get("text", "")
                else:
                    col_index = int(col.replace("#", "")) - 1
                    values = item.get("values", [])
                    cell_text = values[col_index] if col_index < len(values) else ""
                    # Add relevance score for that column.
                    pid = paper_ids[col_index]
                    relevance = paper_relevance.get(pid, "N/A")
                    cell_text = f"{cell_text}\nRelevance: {relevance}"
                tooltip.showtip(cell_text, event.x_root + 20, event.y_root + 10)
            else:
                tooltip.hidetip()
        else:
            tooltip.hidetip()
    
    tree.bind("<Motion>", on_motion)
    tree.bind("<Leave>", lambda event: tooltip.hidetip())
    
    # Bind header click: when clicking on a header, open the PDF.
    def on_header_click(event):
        region = tree.identify("region", event.x, event.y)
        if region == "heading":
            col = tree.identify_column(event.x)
            try:
                index = int(col.replace("#", "")) - 1
                if 0 <= index < len(paper_ids):
                    pid = paper_ids[index]
                    pdf_url = paper_pdf_urls.get(pid)
                    if pdf_url:
                        webbrowser.open_new(pdf_url)
            except Exception as e:
                print("Error in header click:", e)
    
    tree.bind("<Button-1>", on_header_click)
    
    root.mainloop()

if __name__ == "__main__":
    paper_ids = [
        "204e3073870fae3d05bcbc2f6a8e263d9b72e776",
        "43428880d75b3a14257c3ee9bda054e61eb869c0",
        "4550a4c714920ef57d19878e31c9ebae37b049b2",
        "13d9323a8716131911bfda048a40e2cde1a76a46",
        "735d547fc75e0772d2a78c46a1cc5fad7da1474c",
        "c6850869aa5e78a107c378d2e8bfa39633158c0c",
        "b60abe57bc195616063be10638c6437358c81d1e",
        "93499a7c7f699b6630a86fad964536f9423bb6d0",
        "47570e7f63e296f224a0e7f9a0d08b0de3cbaf40"
    ]

    # paper_ids = [
    #     "manual1",
    #     "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef",
    #     "9cb4316403b1a30ae637003466336fc1347e6ddc",
    #     "3ad88b425fd26a6475250bbafd525b12f17f960d",
    #     "97932ab77940df76c8b81fca51be061302195779",
    #     "cbcf31491afbc03826603dff3827e7ec3de41949",
    #     "e4ed248129f6ac1c00e192fd1f02871b913308b5",
    #     "eaed7286bba82a3adc56dc17623d82cebe4b34c6",
    #     "882d9f8704766d47aa85a30837353876f960dec6"
    # ]

    # paper_ids = [
    #     "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef",
    #     "9cb4316403b1a30ae637003466336fc1347e6ddc",
    #     "3ad88b425fd26a6475250bbafd525b12f17f960d",
    #     "97932ab77940df76c8b81fca51be061302195779",
    #     "cbcf31491afbc03826603dff3827e7ec3de41949",
    #     "e4ed248129f6ac1c00e192fd1f02871b913308b5",
    #     "eaed7286bba82a3adc56dc17623d82cebe4b34c6",
    #     "manual1",
    #     "882d9f8704766d47aa85a30837353876f960dec6"
    # ]


    # paper_ids = [
    #     '1b6e810ce0afd0dd093f789d2b2742d047e316d5',
    #     '5f19ae1135a9500940978104ec15a5b8751bc7d2',
    #     '0f733817e82026f7c29909a51cb4df7d2685f0e7',
    # ]

    # Generate the comparison table
    # for paper_id in paper_ids:
    #     generate_embedding_for_paper_chunks(paper_id)

    # create_comparison_table(paper_ids[0], paper_ids[1:], mode="aggregated")
    create_comparison_table(paper_ids[0], paper_ids[1:], mode="hybrid")
    display_comparison_table(paper_ids[0])

    pass    
