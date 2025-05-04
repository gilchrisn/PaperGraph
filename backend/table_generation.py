from comparison_table_generation.config import logger
from repository.paper_repository import PaperRepository  # Your repository module
from comparison_table_generation.paper_embedding import generate_embedding_for_paper_chunks, retrieve_relevant_chunks
from comparison_table_generation.criterion_generation import generate_detailed_summary
from comparison_table_generation.paper_comparison_table import create_comparison_table
from comparison_table_generation.visualization import display_comparison_table
from backend.comparison_table_generation.grobid_service import extract_all_sections
from services.openai_service import prompt_chatgpt, generate_embedding, get_total_prompt_tokens, get_total_response_tokens
from comparison_table_generation.table_logging import save_intermediate_tables, log_intermediate_table


# DUMMY_TABLE = 
# {
#     "comparison_points": [
#         {
#             "criterion": "Criterion 1",
#             "description": "Description of criterion 1",
#             ""
#         }
#     ]
# }

def main():
    repository = PaperRepository()
    
    # List of paper IDs to process.
    paper_ids = [
        "manual1",
        "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef",
        "9cb4316403b1a30ae637003466336fc1347e6ddc",
        "3ad88b425fd26a6475250bbafd525b12f17f960d",
        # "97932ab77940df76c8b81fca51be061302195779",
        # "cbcf31491afbc03826603dff3827e7ec3de41949",
        # "e4ed248129f6ac1c00e192fd1f02871b913308b5",
        # "eaed7286bba82a3adc56dc17623d82cebe4b34c6",
        # "882d9f8704766d47aa85a30837353876f960dec6"
    ]

    # Pre-compute embeddings for all papers.
    for paper_id in paper_ids:
        generate_embedding_for_paper_chunks(repository, paper_id, extract_all_sections, generate_embedding)
    
    # Create the comparison table using the "hybrid" criterion-generation approach.
    expansion_approach = "boolean_then_expand" # "direct_boolean" or "boolean_then_expand"
    merging_approach = "full_table" # "pairwise" or "full_table"
    content_generation_strategy = "rag" # "rag" or "all_chunks"
    criterion_generation_strategy = expansion_approach + " + " + merging_approach # "hybrid" or (expansion_approach + " + " + merging_approach)
    # criterion_generation_strategy = "hybrid"

    from time import time
    start = time()
    comparison_table = create_comparison_table(
        repository,
        main_paper_id=paper_ids[0],
        baseline_paper_ids=paper_ids[1:],
        criterion_generation_strategy=criterion_generation_strategy,
        get_paper_chunks=lambda pid: repository.get_chunks_by_semantic_id(pid),
        prompt_chatgpt=prompt_chatgpt,
        retrieve_relevant_chunks=lambda query, chunks, top_k=3: retrieve_relevant_chunks(query, chunks, generate_embedding, top_k),
        generate_detailed_summary=lambda full_text: generate_detailed_summary(prompt_chatgpt, full_text),
        content_generation_strategy=content_generation_strategy
    )
    time_taken = time() - start
    print("Time taken:", time_taken)
    print("\n\n")
    
    log_intermediate_table(comparison_table, step="final")
    save_intermediate_tables(details=("Criterion generation strategy: " + criterion_generation_strategy + " | Content generation strategy: " + content_generation_strategy),
                            time_taken=time_taken,
                            total_prompt_tokens=get_total_prompt_tokens(),
                            total_response_tokens=get_total_response_tokens()
                            )
    # Display the comparison table in a Tkinter window.
    display_comparison_table(repository, paper_ids[0], criterion_generation_strategy, content_generation_strategy)

if __name__ == "__main__":
    main()
