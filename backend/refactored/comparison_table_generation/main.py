"""
comparison_table_generation/main.py

Main runner for the table generation pipeline
"""

import logging
import os
import sys
from typing import List
from .core.models import (
    Paper, PipelineConfig, CriterionGenerationStrategy, 
    ContentGenerationStrategy, MergingStrategy
)
from .core.pipeline import PipelineFactory
from .utils.converters import convert_repo_paper_to_model


def setup_logging():
    """Set up logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("comparison_pipeline.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def main():
    """Main entry point for table generation"""
    logger = setup_logging()
    
    # Add the parent directory to sys.path so we can import the repository
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    
    # Import the repository and services
    from repository.paper_repository import PaperRepository
    from services.openai_service import prompt_chatgpt, generate_embedding
    
    # Create repository instance
    repository = PaperRepository()
    
    # Specify paper IDs
    paper_ids = [
        "manual1",
        "fb232886e08a0a85b4dcd7e9712d0ec17dbe8aef",
        "9cb4316403b1a30ae637003466336fc1347e6ddc",
        "3ad88b425fd26a6475250bbafd525b12f17f960d"
    ]
    
    # Load paper data from repository and convert to model format
    papers = []
    for paper_id in paper_ids:
        paper_data = repository.get_paper_by_semantic_id(paper_id)
        if not paper_data:
            logger.error(f"Paper not found: {paper_id}")
            continue
            
        chunks = repository.get_chunks_by_semantic_id(paper_id)
        paper = convert_repo_paper_to_model(paper_data, chunks)
        papers.append(paper)
    
    # Create pipeline configuration
    config = PipelineConfig(
        criterion_generation_strategy=CriterionGenerationStrategy.HYBRID,
        content_generation_strategy=ContentGenerationStrategy.RAG,
        merging_strategy=MergingStrategy.FULL_TABLE,
        retrieve_top_k=3
    )
    
    # Create and run pipeline
    logger.info("Creating pipeline with configuration")
    pipeline = PipelineFactory.create(
        config=config,
        repository=repository,
        prompt_chatgpt=prompt_chatgpt,
        generate_embedding=generate_embedding
    )
    
    logger.info("Running pipeline")
    comparison_table = pipeline.run(papers)
    
    # Display the comparison table
    logger.info(f"Generated table with {len(comparison_table.criteria)} criteria")
    
    # Use the visualization module to display the table
    from .visualization.table_viewer import display_comparison_table
    display_comparison_table(comparison_table)
    
    return comparison_table


if __name__ == "__main__":
    main()