import re
import json
import logging
from .paper_utils import parse_json_response
from .table_logging import log_intermediate_table

logger = logging.getLogger(__name__)

DUMMY_CRITERIA1 = """
[
                    {
                        "criterion": "summary_based_peeling",
                        "description": "The paper proposes a summary-based peeling algorithm for densest subgraph discovery.",
                        "papers": [
                            "manual1"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "neighborhood_summaries",
                        "description": "The paper employs neighborhood summaries to estimate peeling coefficients and subgraph densities.",
                        "papers": [
                            "manual1"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "theta_approximation_guarantee",
                        "description": "The system provides an approximation guarantee for densest subgraph discovery.",
                        "papers": [
                            "manual1",
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "density_estimator",
                        "description": "The system provides estimators for various density metrics during processing.",
                        "papers": [
                            "manual1"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "real_world_application",
                        "description": "The paper applies its systems to real-world datasets.",
                        "papers": [
                            "manual1",
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef",
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "comparison_with_baselines",
                        "description": "The paper compares its system's performance against state-of-the-art or baseline methods.",
                        "papers": [
                            "manual1",
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "execution_time_optimization",
                        "description": "The system demonstrates significant execution time improvements over baseline methods.",
                        "papers": [
                            "manual1",
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "density_metric_support",
                        "description": "The system supports multiple density metrics.",
                        "papers": [
                            "manual1"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "handling_large_graphs",
                        "description": "The system can handle large datasets efficiently.",
                        "papers": [
                            "manual1",
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef",
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "parameter_analysis",
                        "description": "The paper includes parameter sensitivity analysis.",
                        "papers": [
                            "manual1"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "scalability_analysis",
                        "description": "The paper discusses the scalability of the proposed methods.",
                        "papers": [
                            "manual1",
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef",
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "user_defined_apis",
                        "description": "The system provides user-defined APIs for specific operations.",
                        "papers": [
                            "manual1"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "approximation_comparison_experiment",
                        "description": "The approximation factor of the proposed algorithms is compared experimentally.",
                        "papers": [
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "innovation_in_algorithm",
                        "description": "The paper introduces innovative algorithmic improvements or techniques.",
                        "papers": [
                            "manual1",
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef",
                            "9cb4316403b1a30ae637003466336fc1347e6ddc",
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "streaming_algorithm_presented",
                        "description": "The paper presents a streaming algorithm.",
                        "papers": [
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "uses_greedy_algorithm",
                        "description": "The paper uses a greedy algorithm to solve a problem.",
                        "papers": [
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "overlap_handling",
                        "description": "The paper deals with handling overlaps effectively in its data structure or algorithm.",
                        "papers": [
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    }
                ]
                """

def generate_comparison_criteria_with_aggregated_summary(paper_ids: list, get_paper_chunks, generate_detailed_summary, prompt_chatgpt, mode: str = "detailed") -> dict:
    """
    Generate initial evaluation criteria by aggregating detailed summaries from each paper.
    """
    full_texts = {}
    for paper_id in paper_ids:
        chunks = get_paper_chunks(paper_id)
        full_texts[paper_id] = " ".join(chunk["chunk_text"] for chunk in chunks)

    summaries = {}
    for paper_id, full_text in full_texts.items():
        summaries[paper_id] = generate_detailed_summary(full_text)

    combined_summary = "\n\n".join(f"{pid}: {summaries[pid]}" for pid in summaries)

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
    Please do not use any LaTeX formatting (e.g., avoid sequences like \\( or \\)); if mathematical notation is needed, please use plain text.
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
        
        Please do not use any LaTeX formatting (e.g., avoid sequences like \\( or \\)); if mathematical notation is needed, please use plain text.
        """
    
    messages = [
        {"role": "system", "content": "You are an expert research assistant."},
        {"role": "user", "content": prompt}
    ]
    response = prompt_chatgpt(messages, model="gpt-4o")
    try:
        response_dict = parse_json_response(response)
        # logger.debug("Aggregated criteria: %s", response_dict)
        return response_dict, summaries
    except Exception as e:
        logger.error("Error parsing aggregated criteria: %s", e)
        return {}, summaries

def refine_criterion(criterion: dict, paper_ids: list, get_paper_chunks, retrieve_relevant_chunks, prompt_chatgpt) -> dict:
    """
    Refine a given evaluation criterion by gathering additional details (via RAG) from each paper.
    """
    combined_excerpts = ""
    for pid in paper_ids:
        chunks = get_paper_chunks(pid)
        query_text = f"{criterion['criterion']} - {criterion['description']}"
        relevant_chunks = retrieve_relevant_chunks(query_text, chunks, top_k=3)
        excerpt_text = "\n".join(f"{c['section_title']}: {c['chunk_text']}" for c in relevant_chunks)
        combined_excerpts += f"Paper {pid}:\n{excerpt_text}\n\n"
    
    prompt = f"""
    You are an expert research assistant tasked with refining an evaluation criterion for comparing research papers.
    The existing criterion and description are provided below.
    
    Existing Criterion: {criterion['criterion']}
    Existing Description: {criterion['description']}
    
    Additional Detailed Excerpts from all papers:
    {combined_excerpts}
    
    Please provide a refined version of this criterion such that it is formulated as a true/false statement.
    Additionally, provide a refined and concise explanation (description) of why this true/false criterion is important and how it captures the common themes or nuances across these papers.
    
    Return your answer in valid JSON format with the following keys:
    - "criterion": the refined true/false short 1-3 word statement that describes the criterion,
    - "description": a refined, concise explanation of the criterion.
    
    Your response MUST be valid JSON (with no additional text) and follow the exact format provided below. 
    Please do not use any LaTeX formatting (e.g., avoid sequences like \\( or \\)); if mathematical notation is needed, please use plain text.

    Example:
    ```json
    {{
        "comparison_points": [
            {{
                "criterion": "criteria1",
                "description": "description1"
            }},
            {{
                "criterion": "criteria2",
                "description": "description2"
            }}
        ]
    }}
    ```
    
    Ensure that any double quotes within the text are escaped using a backslash (\").
    """

    messages = [
        {"role": "system", "content": "You are an expert research assistant."},
        {"role": "user", "content": prompt}
    ]
    response = prompt_chatgpt(messages, model="gpt-4o")
    try:
        refined = parse_json_response(response)
        return refined["comparison_points"]
    except Exception as e:
        logger.error("Error refining criterion: %s", e)
        return {"criterion": criterion["criterion"], "description": criterion["description"]}

def generate_comparison_criteria_with_hybrid_approach(paper_ids: list, get_paper_chunks, generate_detailed_summary, prompt_chatgpt, retrieve_relevant_chunks) -> list:
    """
    Generate evaluation criteria using a two-stage (hybrid) approach.
    Currently, this uses a dummy criterion that is later refined.
    """
    initial_output, summaries = generate_comparison_criteria_with_aggregated_summary(paper_ids, get_paper_chunks, generate_detailed_summary, prompt_chatgpt, mode="general")  
    initial_criteria = initial_output.get("comparison_points", [])

    # Log initial criteria to a file
    log_intermediate_table(initial_output["comparison_points"], step="initial")

    refined_criteria = {"comparison_points": []}
    for crit in initial_criteria:
        refined = refine_criterion(crit, paper_ids, get_paper_chunks, retrieve_relevant_chunks, prompt_chatgpt)
        # Assuming the refined output is directly a dictionary; if it contains a list, adjust accordingly.
        refined_criteria["comparison_points"].extend(refined)
    

    # logger.debug("Refined criteria after hybrid approach: %s", refined_criteria)
    # Log intermediate criteria to a file
    log_intermediate_table(refined_criteria["comparison_points"], step="refined")

    # Filter out any controversial or non-insightful criteria
    refined_criteria = refine_criteria_second_pass(
        refined_criteria["comparison_points"],
        paper_ids,
        summaries,
        prompt_chatgpt
    )

    log_intermediate_table(refined_criteria
                           , step="refined_criteria")
    
    refined_criteria_second_pass = refine_criteria_second_pass(
        refined_criteria["comparison_points"],
        paper_ids,
        summaries,
        prompt_chatgpt
    )

    log_intermediate_table(refine_criteria_second_pass, step="refined_criteria")

    return refined_criteria_second_pass

# ------------------------------------------------------------
# EXPANSION STAGE
# ------------------------------------------------------------

def generate_boolean_criteria_for_paper(
    paper_id: str,
    full_text: str,
    prompt_chatgpt,
) -> list[dict]:
    """
    Approach <1>: Ask LLM to directly generate a set of boolean criteria for a single paper.
    Returns a list of dicts: [{"criterion": "...", "description": "...", "is_boolean": true}, ...]
    """
    # Prompt: ask for boolean criteria
    prompt = f"""
    You are an expert research assistant. We have a paper with ID: {paper_id}.
    Its content is as follows:
    {full_text}

    Generate a list of super detailed 'boolean' criteria (i.e., true/false questions) that might be relevant
    for evaluating or comparing this paper. For each criterion, provide:
    - "criterion": a short title
    - "description": a one-sentence description and context
    - "is_boolean": set to true

    Your response MUST be valid JSON (with no additional text) and follow the exact format provided below. 
    Please do not use any LaTeX formatting (e.g., avoid sequences like \\( or \\)); if mathematical notation is needed, please use plain text.

    Return JSON with "criteria": [...]

    Example:
    ```json
    {{
        "criteria": [
            {{"criterion": "criteria1", "description": "description1", "is_boolean": true}},
            {{"criterion": "criteria2", "description": "description2", "is_boolean": true}}
        ]
    }}
    """
    messages = [
        {"role": "system", "content": "You are an expert research assistant."},
        {"role": "user", "content": prompt}
    ]
    response = prompt_chatgpt(messages, model="gpt-4o")

    try: 
        parsed = parse_json_response(response)
        return parsed.get("criteria", [])
    except Exception as e:
        logger.warning("Error parsing boolean criteria for paper %s: %s", paper_id, e)
        return []

def generate_expandable_boolean_criteria_for_paper(
    paper_id: str,
    full_text: str,
    prompt_chatgpt
) -> list[dict]:
    """
    Approach <1b>: Generate a set of boolean criteria that can be expanded further.
    This is a variant of the direct boolean approach, but with more room for expansion.
    """
    # Prompt: ask for boolean criteria
    prompt = f"""
    You are an expert research assistant. We have a paper with ID: {paper_id}.
    Its content is as follows:
    {full_text}

    Generate a list of super detailed 'boolean' criteria (i.e., true/false questions) that might be relevant
    for evaluating or comparing this paper, and true for this paper. If there are any criteria that need further expansion, please provide
    a more detailed description that can be broken down into sub-criteria.

    For each criterion, provide:
    - "criterion": a short criteria
    - "description": a one-sentence description and context
    - "is_boolean": true if it's a true/false question, false if it needs further expansion

    Your response MUST be valid JSON (with no additional text) and follow the exact format provided below. 
    Please do not use any LaTeX formatting (e.g., avoid sequences like \\( or \\)); if mathematical notation is needed, please use plain text.

    Return JSON with "criteria": [...]

    Example:
    ```json
    {{
        "criteria": [
            {{"criterion": "criteria1", "description": "description1", "is_boolean": true}},
            {{"criterion": "criteria2", "description": "description2", "is_boolean": false}}
        ]
    }}
        
    """
    messages = [
        {"role": "system", "content": "You are an expert research assistant."},
        {"role": "user", "content": prompt}
    ]
    response = prompt_chatgpt(messages, model="gpt-4o")

    try:
        
        parsed = parse_json_response(response)
        logger.debug("Parsed boolean criteria for paper %s: %s", paper_id, parsed)
        return parsed.get("criteria", [])
    except Exception as e:
        logger.warning("Error parsing boolean criteria for paper %s: %s", paper_id, e)
        return []
    
def expand_non_boolean_criteria(
    paper_id: str,
    existing_criteria: list[dict],
    full_text: str,
    prompt_chatgpt
) -> list[dict]:
    """
    Approach <2>: Iteratively expand criteria that are not strictly boolean or need more elaboration.
    For demonstration, we simply ask the LLM to refine them further if "is_boolean" is false.
    """
    refined_criteria = []
    for crit in existing_criteria:
        if crit.get("is_boolean"):
            # Already boolean, no expansion needed
            refined_criteria.append(crit)
            continue

        # If it's not boolean, ask LLM to refine or expand
        prompt = f"""
        We have a criterion that is not strictly boolean:
        {crit}

        Paper ID: {paper_id}
        Full text of the paper:
        {full_text}

        Please expand or refine this criterion into one or more sub-criteria that can be answered with true/false.
        The sub-criterion name must describe the content, while keeping it short. 
        Return JSON with "expanded_criteria": a list of criteria objects
        (with "criterion", "description", "is_boolean").

        Your response MUST be valid JSON (with no additional text) and follow the exact format provided below. Ensure that any double quotes within the bullet points are escaped using a backslash (\").

        Example:
        ```json
        {{
            "expanded_criteria": [
                {{"criterion": "criteria1", "description": "description1", "is_boolean": true}},
                {{"criterion": "criteria2", "description": "description2", "is_boolean": true}}
            ]
        }}
        """
        messages = [
            {"role": "system", "content": "You are an expert research assistant."},
            {"role": "user", "content": prompt}
        ]
        response = prompt_chatgpt(messages, model="gpt-4o")
        try:
            parsed = parse_json_response(response)
            expanded_list = parsed.get("expanded_criteria", [])
            logger.debug("Expanded criteria for paper %s: %s", paper_id, expanded_list)
            refined_criteria.extend(expanded_list)
        except Exception as e:
            logger.warning("Error expanding non-boolean criterion for paper %s: %s", paper_id, e)
            # Fallback: keep the original criterion if expansion fails
            refined_criteria.append(crit)

    return refined_criteria

def expand_criteria_for_paper(
    paper_id: str,
    full_text: str,
    prompt_chatgpt,
    approach: str = "boolean_then_expand"
) -> list[dict]:
    """
    Master function for the Expansion Stage, which calls different approaches:
      - "boolean_then_expand": first generate boolean criteria, then expand any leftover non-boolean ones
      - "direct_boolean": directly generate a set of boolean criteria only
      - (you can add more approaches if needed)

    Returns a list of dicts, e.g.:
      [
        {"criterion": "...", "description": "...", "is_boolean": true},
        ...
      ]
    """
    if approach == "direct_boolean":
        # Approach <1> only
        return generate_boolean_criteria_for_paper(paper_id, full_text, prompt_chatgpt)
    elif approach == "boolean_then_expand":
        # First generate a base set of criteria
        base_criteria =  generate_expandable_boolean_criteria_for_paper(paper_id, full_text, prompt_chatgpt)
        logger.debug("Base criteria for paper %s: %s", paper_id, base_criteria)
        # While expanding, keep refining non-boolean criteria
        expanded = expand_non_boolean_criteria(paper_id, base_criteria, full_text, prompt_chatgpt)

        while len(expanded) > len(base_criteria):
            # If expansion adds new criteria, refine them further
            base_criteria = expanded
            expanded = expand_non_boolean_criteria(paper_id, base_criteria, full_text, prompt_chatgpt)

            # Log new criteria
            logger.debug("Expanded criteria for paper %s: %s", paper_id, expanded)
     
        return expanded
    else:
        logger.warning("Unknown expansion approach: %s", approach)
        return []
    
# MERGING STAGE

def merge_criteria_llm_full_table(
    all_criteria: list[dict],
    all_summaries: dict[str, str],
    prompt_chatgpt
) -> list[dict]:
    """
    Approach <1> from your spec:
    - "throw the full table into LLM, ask it to merge similar criteria"
    all_criteria: a list of criteria dicts from multiple papers
    all_summaries: {paper_id: "summary text", ...} to provide context
    """

    combined_criteria_str = "\n".join(
        f"- Paper {c['paper_id']}: {c['criterion']} => {c['description']}"
        for c in all_criteria
    )

    combined_summaries_str = "\n".join(
        f"Paper {pid} summary: {text}" for pid, text in all_summaries.items()
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
    response = prompt_chatgpt(messages, model="gpt-4o")

    try:
        parsed = parse_json_response(response)
        return parsed.get("merged_criteria", [])
    except Exception as e:
        logger.warning("Error merging criteria with full-table approach: %s", e)
        return all_criteria  # fallback, no merging

def merge_criteria_pairwise(all_criteria: list[dict], prompt_chatgpt) -> list[dict]:
    """
    Approach <2>: "merge same criterion based on criterion label and paper content pairwise"
    Naively check pairwise similarity and merge criteria if they are similar.
    """
    merged = []
    skip_indices = set()
    n = len(all_criteria)
    
    for i in range(n):
        if i in skip_indices:
            continue
        c1 = all_criteria[i]
        # Ensure "papers" exists
        if "papers" not in c1:
            c1["papers"] = [c1.get("paper_id")]
        else:
            if c1.get("paper_id") not in c1["papers"]:
                c1["papers"].append(c1.get("paper_id"))
        
        for j in range(i + 1, n):
            if j in skip_indices:
                continue
            c2 = all_criteria[j]
            prompt = f"""
            You are an expert research assistant.

            Instructions:
            - Compare the two criteria below.
            - If they are essentially the same, merge them into one.
            - If they are different, leave them as is.

            Criteria 1:
            Paper: {c1['paper_id']}
            Criterion: {c1['criterion']}
            Description: {c1['description']}

            Criteria 2:
            Paper: {c2['paper_id']}
            Criterion: {c2['criterion']}
            Description: {c2['description']}

            Are these criteria similar enough to be merged? (true/false)

            Example Output (do not include this in your answer):
            ```json
            {{
                "merge": true
            }}
            ```
            """
            messages = [
                {"role": "system", "content": "You are an expert research assistant."},
                {"role": "user", "content": prompt}
            ]
            response = prompt_chatgpt(messages, model="gpt-4o")
            try:
                parsed = parse_json_response(response)
                if parsed.get("merge", False):
                    # Merge c2 into c1 by adding c2's paper_id to the "papers" list
                    if "papers" not in c1:
                        c1["papers"] = [c1.get("paper_id")]
                    c1["papers"].append(c2.get("paper_id"))
                    skip_indices.add(j)
                    print(f"Merged {c2['criterion']} into {c1['criterion']}")
            except Exception as e:
                logger.warning("Error merging criteria pairwise: %s", e)
        
        merged.append(c1)
    
    return merged

def refine_criteria_second_pass(
    merged_criteria: list[dict],
    paper_ids: list[str],
    all_summaries: dict[str, str],
    prompt_chatgpt
) -> list[dict]:
    """
    Final refinement pass:
    Review the merged criteria to remove any that might be controversial or not insightful.
    Use the summaries from the papers as context to ensure that the remaining criteria are
    both insightful and strictly boolean. Each remaining criterion is accompanied by a brief
    explanation of its significance and a list of associated paper_ids.
    
    Returns:
        A list of refined criteria objects, each containing:
        - "criterion": the final boolean criterion,
        - "description": a brief explanation,
        - "papers": a list of paper IDs that contributed to this criterion.
    """
    # Build context strings from summaries and criteria
    combined_summaries = "\n".join(
        f"Paper {pid} Summary: {summary}" for pid, summary in all_summaries.items()
    )
    
    combined_criteria = "\n".join(
        f"Criterion: {crit.get('criterion')} | Description: {crit.get('description')} | Papers: {crit.get('papers', [crit.get('paper_id')])}"
        for crit in merged_criteria
    )
    
    prompt = f"""
    You are an expert research assistant. We have a set of merged evaluation criteria gathered from multiple research papers.
    As a final quality control step, please review these criteria using the context from the paper summaries below.
    
    Context Summaries:
    {combined_summaries}
    
    Merged Criteria:
    {combined_criteria}
    
    Instructions:
    - Remove any criteria that may be considered controversial or that do not provide insightful evaluation.
    - Only FILTER, do not add new criteria or modify existing ones.
    - Maintain the association with the paper IDs that originally contributed to the criterion.
    
    Return your answer as valid JSON with a key "refined_criteria" mapping to a list of objects.
    Each object must have:
      - "criterion": <unmodified criterion>,
      - "description": <unmodified description>,
      - "papers": a list of paper IDs that support this criterion.
      
    Your response MUST be valid JSON (with no additional text) and follow the exact format provided below.
    Please do not use any LaTeX formatting (e.g., avoid sequences like \\( or \\)); if mathematical notation is needed, please use plain text.
    
    Example (do not include this in your answer):
    ```json
    {{
        "refined_criteria": [
            {{"criterion": "Evaluation Metrics", "description": "Measures performance and consistency across experiments.", "papers": ["paper1", "paper2"]}},
            {{"criterion": "Experimental Design", "description": "Ensures robust methodology and reproducibility.", "papers": ["paper1"]}}
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
        parsed = parse_json_response(response)
        return parsed.get("refined_criteria", [])
    except Exception as e:
        logger.error("Error refining criteria second pass: %s", e)
        # Fallback: return the original merged criteria if refinement fails
        return merged_criteria


# TWO-STAGE ORCHESTRATION

def create_comparison_criteria_two_passes(
    repository,
    paper_ids: list[str],
    prompt_chatgpt,
    expansion_approach: str = "boolean_then_expand",
    merging_approach: str = "full_table"
) -> list[dict]:
    """
    Master method that:
      1) Expands criteria for each paper (Expansion Stage).
      2) Merges them (Merging Stage).
      3) Returns a final table of merged criteria.
      4) (Optional) Creates the final "comparison table" across all papers using these merged criteria.

    Returns the final merged criteria or a final table structure.
    """

    if expansion_approach not in ["boolean_then_expand", "direct_boolean"]:
        raise ValueError("Invalid expansion approach")
    if merging_approach not in ["full_table", "pairwise"]:
        raise ValueError("Invalid merging approach")
    
    # 1. Expansion Stage: gather criteria from each paper
    all_criteria = []
    all_summaries = {}

    for idx, pid in enumerate(paper_ids):
        # Retrieve or build the full text
        chunks = repository.get_chunks_by_semantic_id(pid)
        full_text = "\n".join(chunk["chunk_text"] for chunk in chunks)

        # Expand criteria
        paper_criteria = expand_criteria_for_paper(
            paper_id=pid,
            full_text=full_text,
            prompt_chatgpt=prompt_chatgpt,
            approach=expansion_approach
        )

        # Tag each criterion with the paper_id for later merging
        for c in paper_criteria:
            c["paper_id"] = pid

        all_criteria.extend(paper_criteria)

        # ====== DEBUG LOGGING =====
        # Copy a snapshot of the criteria for logging
        # Instead of just copying the current paper's criteria:
        all_criteria_snapshot = [c.copy() for c in all_criteria if c["paper_id"] in paper_ids[:(idx+1)]]
        for c in all_criteria_snapshot:
            # Build the comparisons dictionary so that it is True only for the criterion's own paper_id.
            c["comparisons"] = {
                ppr_id: True if ppr_id == c["paper_id"] else ""
                for ppr_id in paper_ids[:(idx+1)]
            }


        # Log the intermediate criteria for this paper
        log_intermediate_table(all_criteria_snapshot, step=f"expanded_{pid}")
        # ==========================


        # If you need summaries for merging
        summary = generate_detailed_summary(prompt_chatgpt, full_text)
        all_summaries[pid] = summary

    # log_intermediate_table(all_criteria, step=f"expanded")

    logger.info("All Criteria: %s", all_criteria)

    # 2. Merging Stage: pick one of the approaches to merge them
    if merging_approach == "full_table":
        merged_criteria = merge_criteria_llm_full_table(all_criteria, all_summaries, prompt_chatgpt)
    elif merging_approach == "pairwise":
        merged_criteria = merge_criteria_pairwise(all_criteria, prompt_chatgpt)
    else:
        merged_criteria = all_criteria

    log_intermediate_table(merged_criteria, step=f"merged")
    logger.info("Merged Criteria: %s", merged_criteria)

    # 3. Refinement Stage: review and refine the merged criteria
    second_pass_criteria = refine_criteria_second_pass(
        merged_criteria,
        paper_ids,
        all_summaries,
        prompt_chatgpt
    ) 

    log_intermediate_table(second_pass_criteria, step=f"refined")
    logger.info("Refined Criteria: %s", second_pass_criteria)
    
    return second_pass_criteria

# ============================================================
# HELPER FUNCTIONS
# ============================================================


def generate_detailed_summary(prompt_chatgpt, full_text: str) -> list:
    """
    Use the LLM to generate a detailed summary (as bullet points) of a paper.
    """
    prompt = f"""
    You are an expert research assistant. Based on the following detailed text from a research paper, generate an exhaustive list of bullet points that capture every aspect of the paper.
    
    Text:
    {full_text}
    
    Return your answer as a JSON object with a key "bullet_points" mapping to a list of bullet points.
    Please do not use any LaTeX formatting (e.g., avoid sequences like \\( or \\)); if mathematical notation is needed, please use plain text.
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
        logger.error("Error parsing detailed summary: %s", e)
        return []
