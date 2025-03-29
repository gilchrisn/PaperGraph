import json
import logging
from .paper_utils import convert_pgvector
from .criterion_generation import generate_comparison_criteria_with_hybrid_approach, create_comparison_criteria_two_passes
from .paper_utils import parse_json_response

logger = logging.getLogger(__name__)


DUMMY_CRITERIA1 = """
[
                    {
                        "criterion": "summary_based_peeling",
                        "description": "The paper introduces a summary-based peeling algorithm for densest subgraph discovery.",
                        "papers": [
                            "manual1"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "avoids_materialization",
                        "description": "The system avoids the need for materializing relational graphs.",
                        "papers": [
                            "manual1"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "supports_multiple_density_metrics",
                        "description": "The system supports various density metrics including edge-density and triangle-density.",
                        "papers": [
                            "manual1"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "approximation_guarantees",
                        "description": "The paper provides approximation guarantees for the densest subgraph discovery problem.",
                        "papers": [
                            "manual1",
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef",
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "real_world_applications",
                        "description": "The paper demonstrates the application of the system in real-world scenarios.",
                        "papers": [
                            "manual1",
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef",
                            "9cb4316403b1a30ae637003466336fc1347e6ddc",
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "scalability_analysis",
                        "description": "The paper includes an analysis of the scalability of the proposed system on large datasets.",
                        "papers": [
                            "manual1",
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "memory_efficiency",
                        "description": "The system is designed to be memory efficient compared to materialization-based methods.",
                        "papers": [
                            "manual1",
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "time_complexity_analysis",
                        "description": "The paper provides a detailed analysis of the time complexity of the proposed algorithms.",
                        "papers": [
                            "manual1",
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "comparison_with_baselines",
                        "description": "The paper compares the proposed system with baseline methods in terms of efficiency and effectiveness.",
                        "papers": [
                            "manual1",
                            "9cb4316403b1a30ae637003466336fc1347e6ddc",
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "parameter_sensitivity_analysis",
                        "description": "The paper includes a sensitivity analysis of the parameters used in the system.",
                        "papers": [
                            "manual1"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "unbiased_estimators",
                        "description": "The paper claims that the estimators used in the system are unbiased for the density metrics considered.",
                        "papers": [
                            "manual1"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "detailed_experimental_results",
                        "description": "The paper provides detailed experimental results to support the claims made about the system.",
                        "papers": [
                            "manual1",
                            "9cb4316403b1a30ae637003466336fc1347e6ddc",
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "meta_path_support",
                        "description": "The system supports the use of meta-paths for extracting relational graphs from heterogeneous data sources.",
                        "papers": [
                            "manual1"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "user_defined_apis",
                        "description": "The system provides user-defined APIs for customizing the peeling coefficient and subgraph density estimation.",
                        "papers": [
                            "manual1"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "theoretical_results",
                        "description": "The paper includes theoretical results that support the effectiveness of the proposed system.",
                        "papers": [
                            "manual1",
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "handles_large_graphs",
                        "description": "The system is capable of handling large graphs efficiently, as demonstrated in the experiments.",
                        "papers": [
                            "manual1",
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef",
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "detailed_description_of_algorithms",
                        "description": "The paper provides a detailed description of the algorithms used in the system.",
                        "papers": [
                            "manual1",
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "future_work_discussion",
                        "description": "The paper discusses potential future work and improvements for the system.",
                        "papers": [
                            "manual1",
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "streaming_algorithm_presented",
                        "description": "The paper presents a streaming algorithm for finding approximately densest subgraphs.",
                        "papers": [
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "mapreduce_implementation",
                        "description": "The paper includes a MapReduce implementation of the algorithm.",
                        "papers": [
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "space_efficiency_discussed",
                        "description": "The paper discusses space efficiency and includes a sketching heuristic to reduce memory usage.",
                        "papers": [
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "directed_and_undirected_graphs",
                        "description": "The paper addresses both directed and undirected graphs in the context of the densest subgraph problem.",
                        "papers": [
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "lower_bound_provided",
                        "description": "The paper provides a lower bound on the space required by any streaming algorithm to obtain a constant-factor approximation.",
                        "papers": [
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "algorithm_modification_for_large_subgraphs",
                        "description": "The paper includes a modification of the algorithm to find densest subgraphs above a prescribed size.",
                        "papers": [
                            "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "proposes_new_algorithm",
                        "description": "The paper proposes a new algorithm, Greedy++, for the densest subgraph problem.",
                        "papers": [
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "improves_existing_algorithm",
                        "description": "The paper claims that Greedy++ improves upon Charikar's greedy algorithm in terms of accuracy and efficiency.",
                        "papers": [
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "uses_real_world_datasets",
                        "description": "The experiments in the paper are conducted on real-world datasets.",
                        "papers": [
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "provides_runtime_analysis",
                        "description": "The paper provides a detailed runtime analysis of the Greedy++ algorithm.",
                        "papers": [
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "discusses_open_questions",
                        "description": "The paper discusses open questions and conjectures related to the densest subgraph problem.",
                        "papers": [
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "pseudocode_provided",
                        "description": "The paper includes pseudocode for the Greedy++ algorithm.",
                        "papers": [
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "implementation_details_provided",
                        "description": "The paper provides implementation details for the Greedy++ algorithm.",
                        "papers": [
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "algorithm_intuition_explained",
                        "description": "The paper explains the intuition behind the Greedy++ algorithm.",
                        "papers": [
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "hardware_specifications",
                        "description": "The paper specifies the hardware used for experiments, including CPU, memory, and other relevant details.",
                        "papers": [
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "datasets_used",
                        "description": "The paper lists the datasets used in the experiments, including their sources and characteristics.",
                        "papers": [
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "experimental_procedure",
                        "description": "The paper describes the experimental procedure, including the steps taken to conduct the experiments.",
                        "papers": [
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "performance_metrics",
                        "description": "The paper specifies the performance metrics used to evaluate the algorithms.",
                        "papers": [
                            "9cb4316403b1a30ae637003466336fc1347e6ddc"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "uses_overlap_tree",
                        "description": "The paper introduces and utilizes the Overlap Tree data structure for managing metapath query overlaps.",
                        "papers": [
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "introduces_new_cache_policy",
                        "description": "The paper proposes a new cache replacement policy that considers interdependence among cached items.",
                        "papers": [
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "uses_sparse_matrix_multiplication",
                        "description": "The paper employs sparse matrix multiplication techniques tailored for metapath query evaluation.",
                        "papers": [
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "proposes_dynamic_data_structure",
                        "description": "The paper proposes a dynamic data structure, the Overlap Tree, for managing query overlaps.",
                        "papers": [
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "addresses_multi_query_optimization",
                        "description": "The paper addresses multi-query optimization in the context of metapath query workloads.",
                        "papers": [
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "introduces_atrapos_method",
                        "description": "The paper introduces Atrapos, a method for efficient evaluation of metapath query workloads.",
                        "papers": [
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "uses_zipfian_distribution",
                        "description": "The paper evaluates cache replacement policies using a Zipfian distribution for query workload generation.",
                        "papers": [
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "provides_open_source_code",
                        "description": "The paper provides open-source code for the Atrapos method.",
                        "papers": [
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "discusses_cache_size_variation",
                        "description": "The paper discusses the impact of varying cache sizes on the performance of metapath query evaluation.",
                        "papers": [
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "uses_dynamic_programming",
                        "description": "The paper uses dynamic programming to determine the optimal order of matrix multiplications.",
                        "papers": [
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "considers_constrained_metapaths",
                        "description": "The paper considers constrained metapaths in its evaluation and methodology.",
                        "papers": [
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    },
                    {
                        "criterion": "provides_comprehensive_evaluation",
                        "description": "The paper provides a comprehensive evaluation of Atrapos against various baselines and scenarios.",
                        "papers": [
                            "3ad88b425fd26a6475250bbafd525b12f17f960d"
                        ],
                        "is_boolean": true
                    }
                ]
                """

def generate_comparison_content(
    criteria_list,
    all_paper_ids,
    papers_chunks,
    retrieve_relevant_chunks,
    prompt_chatgpt,
    parse_json_response,
    logger,
    content_generation_strategy
) -> list:
    """
    Generate comparison table content based on the content generation strategy.
    """
    if content_generation_strategy == "all_chunks":
        # Instead of processing each criterion individually, we generate one prompt per paper.
        paper_comparisons = {}
        # Prepare a list of criteria text for the prompt.
        criteria_text = "\n".join(
            f"Criterion: {crit.get('criterion')}\nDescription: {crit.get('description')}"
            for crit in criteria_list
        )

        for pid in all_paper_ids:
            chunks = papers_chunks.get(pid, [])
            if not chunks:
                # If there are no chunks, mark all criteria as None for this paper.
                paper_comparisons[pid] = {crit.get("criterion"): None for crit in criteria_list}
                continue

            # Concatenate all chunks into one long text.
            full_text = " ".join(f"{c['section_title']}: {c['chunk_text']}" for c in chunks)
            # Build one prompt that asks for evaluation of all criteria for this paper.

            column_prompt = f"""
            You are an expert research assistant.
            
            For the following paper with ID {pid}, consider the full text provided below:
            {full_text}
            
            Evaluate the following criteria (each is a true/false question):
            {criteria_text}
            
            For each criterion, determine if the paper meets it.
            Provide your answers as a JSON object with the key "results" mapping to an object where each key is the exact criterion name and the value is true, false, or "N/A".
            
            Note: If a criterion is not applicable to this paper, you can mark it as "N/A".

            Your response MUST be valid JSON (with no additional text) and follow the exact format:
            ```json
            {{
                "results": {{
                    "Criterion 1": true,
                    "Criterion 2": false,
                    "Criterion 3": "N/A"
                }}
            }}
            ```
            """
            messages = [
                {"role": "system", "content": "You are an expert research assistant."},
                {"role": "user", "content": column_prompt}
            ]
            response = prompt_chatgpt(messages, model="gpt-4o")
            try:
                parsed = parse_json_response(response)
                # Expecting the JSON to have a "results" key mapping criterion names to boolean/null.
                paper_comparisons[pid] = parsed.get("results", {})
            except Exception as e:
                logger.error("Error parsing column response for paper %s: %s", pid, e)
                paper_comparisons[pid] = {crit.get("criterion"): None for crit in criteria_list}
        
        # Now, build the table by merging per-paper (column) results into per-criterion rows.
        comparison_table = []
        for crit in criteria_list:
            criterion_name = crit.get("criterion")
            criterion_description = crit.get("description")
            comparisons = {}
            for pid in all_paper_ids:
                # For each criterion, retrieve the value for this paper.
                comparisons[pid] = paper_comparisons.get(pid, {}).get(criterion_name, None)
            comparison_table.append({
                "criterion": criterion_name,
                "description": criterion_description,
                "comparisons": comparisons
            })
    else:
        # Default RAG approach (existing logic): one prompt per criterion.
        comparison_table = []
        for criterion_obj in criteria_list:
            criterion_name = criterion_obj.get("criterion")
            criterion_description = criterion_obj.get("description")
            papers_excerpts = {}
            for pid in all_paper_ids:
                chunks = papers_chunks.get(pid, [])
                if not chunks:
                    papers_excerpts[pid] = "No relevant details found."
                    continue

                query_text = f"{criterion_name} - {criterion_description}"
                relevant_chunks = retrieve_relevant_chunks(query_text, chunks, top_k=3)
                excerpt_text = "\n".join(f"{c['section_title']}: {c['chunk_text']}" for c in relevant_chunks)
                papers_excerpts[pid] = excerpt_text if excerpt_text else "No relevant details found."
            
            consolidated_excerpts = "\n\n".join(f"Paper {pid}: {text}" for pid, text in papers_excerpts.items())
            
            prompt = f"""
            You are an expert research assistant tasked with comparing multiple research papers based on a specific evaluation criterion.
            
            Instructions:
            - Compare each paper based on the given criterion.
            - Each cell should only be true, false or "N/A".
            - Your response MUST be valid JSON (with no additional text) and follow the exact format provided below. Ensure that any double quotes within the text are escaped using a backslash (\").
            
            Note: If the criterion is not applicable to a paper, you can mark it as "N/A".
            
            Example Output (do not include this in your answer):
            ```json
            {{
                "criterion": "criterion_name",
                "description": "criterion_description",
                "comparisons": {{
                    "<paper_1 id>": true,
                    "<paper_2 id>": false,  
                    "<paper_3 id>": "N/A"
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
            try:
                response_dict = parse_json_response(response)
                comparisons = response_dict.get("comparisons", {})
            except Exception as e:
                logger.error("Error parsing comparison response: %s", e)
                comparisons = {}
            
            comparison_table.append({
                "criterion": criterion_name,
                "description": criterion_description,
                "comparisons": comparisons
            })
    return comparison_table

def create_comparison_table(
    repository, 
    main_paper_id: str, 
    baseline_paper_ids: list, 
    criterion_generation_strategy: str = "hybrid",
    get_paper_chunks=None, 
    prompt_chatgpt=None, 
    retrieve_relevant_chunks=None,
    generate_detailed_summary=None,
    content_generation_strategy: str = "rag"   # New parameter: "rag" (default) or "all_chunks"
) -> list:
    """
    Create a comparison table for the main paper (and baseline papers) based on generated criteria.
    Logs the intermediate comparison table to a file.

    Parameters:
        content_generation_strategy: If set to "rag", use top_k relevant excerpts; if "all_chunks",
                        retrieve all chunks and concatenate them for each paper.
    """
    existing = repository.get_paper_comparison_by_semantic_id(
        main_paper_id,
        criterion_generation_strategy=criterion_generation_strategy,
        content_generation_strategy=content_generation_strategy
    )
    if existing:
        return existing["comparison_data"]

    all_paper_ids = [main_paper_id] + baseline_paper_ids

    if criterion_generation_strategy == "hybrid":
        criteria_list = generate_comparison_criteria_with_hybrid_approach(
            all_paper_ids,
            lambda pid: repository.get_chunks_by_semantic_id(pid),
            generate_detailed_summary,
            prompt_chatgpt,
            lambda query, chunks, top_k=3: retrieve_relevant_chunks(query, chunks, top_k=top_k)
        )
    elif criterion_generation_strategy.startswith("boolean_then_expand") or criterion_generation_strategy.startswith("direct_boolean"):
        expansion_approach = criterion_generation_strategy.split("+")[0].strip()
        merging_approach = criterion_generation_strategy.split("+")[1].strip()

        # criteria_list = create_comparison_criteria_two_passes(
        #     repository,
        #     paper_ids=all_paper_ids,
        #     prompt_chatgpt=prompt_chatgpt,
        #     expansion_approach=expansion_approach,
        #     merging_approach=merging_approach
        # )

        criteria_list = json.loads(DUMMY_CRITERIA1)

        # from comparison_table_generation.criterion_generation import refine_criteria_second_pass
        # from services.openai_service import prompt_chatgpt
        # criteria_list = refine_criteria_second_pass(
        #     criteria_list,
        #     all_paper_ids,
        #     all_summaries={},
        #     prompt_chatgpt=prompt_chatgpt,
        # ) 
    else:
        criteria_list = []

    # Pre-fetch all chunks for every paper.
    papers_chunks = {pid: repository.get_chunks_by_semantic_id(pid) for pid in all_paper_ids}
    for pid, chunks in papers_chunks.items():
        for chunk in chunks:
            if chunk.get("embedding"):
                chunk["embedding"] = convert_pgvector(chunk["embedding"])

    comparison_table = generate_comparison_content(
        criteria_list,
        all_paper_ids,
        papers_chunks,
        retrieve_relevant_chunks,
        prompt_chatgpt,
        parse_json_response,
        logger,
        content_generation_strategy
    )

    # Log intermediate comparison table.
    repository.create_paper_comparison({
        "semantic_id": main_paper_id,
        "comparison_data": comparison_table,
        "criterion_generation_strategy": criterion_generation_strategy,
        "content_generation_strategy": content_generation_strategy
    })

    return comparison_table
