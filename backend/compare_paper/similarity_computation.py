# similarity_computation.py
from sklearn.metrics.pairwise import cosine_similarity
from compare_paper.paper_embedding import generate_embedding
from grobid.grobid_paper_extractor import extract_metadata, extract_all_metadata
from openai_service.prompt_chatgpt import prompt_chatgpt
import json

# def get_similarity(paper_1_path, paper_2_path):
#     paper_1_abstract = extract_metadata(paper_1_path, "processHeaderDocument")["abstract"]
#     paper_2_abstract = extract_metadata(paper_2_path, "processHeaderDocument")["abstract"]

#     embeddings_paper_1 = generate_embedding(paper_1_abstract)
#     embeddings_paper_2 = generate_embedding(paper_2_abstract)

#     return cosine_similarity(embeddings_paper_1, embeddings_paper_2)[0][0], "citation", "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua"


def get_similarity(paper_1_path, paper_2_path):
    paper_1_details = extract_all_metadata(paper_1_path)
    paper_2_details = extract_all_metadata(paper_2_path)

    prompt = """
    ### Task Prompt

    You are an AI assistant. Your task is to determine whether **Paper B** could serve as a relevant or "missed" baseline/reference for **Paper A**. Analyze them based on the following **criteria** and **weights**, and return the results in the specified JSON format.

    ---

    ### Criteria and Weights
    1. **Problem Alignment (Weight = 3)**  
    - Are the problems or goals described effectively the same or closely related?

    2. **Methodological Overlap (Weight = 3)**  
    - Do the papers use similar frameworks, algorithms, or theoretical approaches?

    3. **Dataset / Experimental Setup Overlap (Weight = 2)**  
    - Are the datasets, sample populations, or experimental setups comparable?  
    - If theoretical, do they address the same scenario/assumptions?

    4. **Performance Metrics & Results Comparability (Weight = 2)**  
    - Do both papers report results using comparable metrics (e.g., accuracy, F1-score, runtime)?

    5. **Novelty & Claims (Weight = 2)**  
    - Are the stated contributions or novelty claims of Paper B relevant to Paper A?  
    - Could Paper B’s novelty challenge, complement, or provide context for Paper A’s claims?

    6. **References & Citation Network (Weight = 1)**  
    - Do they cite many of the same key sources, or does Paper B cite important works that Paper A has missed?

    7. **Temporal Context (Weight = 1)**  
    - Was Paper B published earlier or around the same time, making it feasible for Paper A to have cited it?

    ---

    ### Instructions

    For each criterion:
    1. Summarize how **Paper A** addresses it.
    2. Summarize how **Paper B** addresses it.
    3. Assign a **Relevance Score** from 0 to 3:
    - **0** = Not relevant or no overlap.
    - **1** = Slight overlap or weak relevance.
    - **2** = Moderate overlap or relevance.
    - **3** = Strong overlap or direct relevance.
    4. Provide a brief explanation for the score.

    ---

    ### Final Output Format

    Return the analysis as a JSON object structured like this:

    {
    "criteria": {
        "problem_alignment": {
        "source_paper": "[Summary of Paper A for Problem Alignment]",
        "cited_paper": "[Summary of Paper B for Problem Alignment]",
        "relevance_score": [0-3],
        "explanation": "[Explanation for the score]"
        },
        "methodological_overlap": {
        "source_paper": "[Summary of Paper A for Methodology]",
        "cited_paper": "[Summary of Paper B for Methodology]",
        "relevance_score": [0-3],
        "explanation": "[Explanation for the score]"
        },
        "dataset_experimental_overlap": {
        "source_paper": "[Summary of Paper A for Dataset/Experiment Setup]",
        "cited_paper": "[Summary of Paper B for Dataset/Experiment Setup]",
        "relevance_score": [0-3],
        "explanation": "[Explanation for the score]"
        },
        "performance_metrics_comparability": {
        "source_paper": "[Summary of Paper A for Performance Metrics]",
        "cited_paper": "[Summary of Paper B for Performance Metrics]",
        "relevance_score": [0-3],
        "explanation": "[Explanation for the score]"
        },
        "novelty_claims": {
        "source_paper": "[Summary of Paper A for Novelty Claims]",
        "cited_paper": "[Summary of Paper B for Novelty Claims]",
        "relevance_score": [0-3],
        "explanation": "[Explanation for the score]"
        },
        "references_citation_network": {
        "source_paper": "[Summary of Paper A for References]",
        "cited_paper": "[Summary of Paper B for References]",
        "relevance_score": [0-3],
        "explanation": "[Explanation for the score]"
        },
        "temporal_context": {
        "source_paper": "[Summary of Paper A for Temporal Context]",
        "cited_paper": "[Summary of Paper B for Temporal Context]",
        "relevance_score": [0-3],
        "explanation": "[Explanation for the score]"
        }
    },
    "relationship_type": "[baseline/citation]",
    "conclusion": "[Summarize whether Paper B is likely a missed baseline or citation for Paper A]"
    }

    ---

    ### Papers to Analyze

    **Paper A**:  
    {paper_1_details}

    **Paper B Summary**:  
    {paper_2_details}
    """

    messages = [
        {"role": "system", "content": "You are an AI assistant."},
        {"role": "user", "content": prompt}
    ]

    prompt_response = prompt_chatgpt(messages, model="gpt-4")
    response = prompt_response["choices"][0]["message"]

    # Save the response to a txt file
    with open("resources\\response.txt", "w") as f:
        f.write(response)

    return parse_openai_response(response)

def parse_openai_response(response):
    # parse the specific response format from get_similarity into a dict
    data = json.loads(response)

    # Calculate the similarity score based on the relevance scores and weights
    weights_dict = {
        "problem_alignment": 3,
        "methodological_overlap": 3,
        "dataset_experimental_overlap": 2,
        "performance_metrics_comparability": 2,
        "novelty_claims": 2,
        "references_citation_network": 1,
        "temporal_context": 1
    }

    total_score = 0
    total_weight = 0
    for criterion, value in data["criteria"].items():
        total_score += value["relevance_score"] * weights_dict[criterion]
        total_weight += weights_dict[criterion]

    similarity_score = total_score / total_weight

    # Append similarity score to the JSON response
    data["similarity_score"] = similarity_score

    return data

if __name__ == '__main__':
    paper_1_path = "resources\\all_papers\\-Stepping_A_Parallel_Single_Source_Shortest_Path_Algorithm.pdf"
    paper_2_path = "resources\\all_papers\\3-HOP_A_High-Compression_Indexing_Scheme_for_Reachability_Query.pdf"

    similarity_data = get_similarity(paper_1_path, paper_2_path)

    print(similarity_data)