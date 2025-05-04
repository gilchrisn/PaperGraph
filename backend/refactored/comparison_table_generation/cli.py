"""
comparison_table_generation/cli.py

Command-line interface for running the table generation pipeline
"""

import argparse
import logging
import os
import sys
from typing import List
import json

from .core.models import (
    PipelineConfig, CriterionGenerationStrategy, ContentGenerationStrategy, MergingStrategy
)
from .core.pipeline import PipelineFactory
from .utils.converters import convert_repo_paper_to_model
from .visualization.table_viewer import display_comparison_table
from .experiments.runner import ExperimentRunner


def setup_logging(verbose: bool = False):
    """Set up logging for CLI"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("comparison_pipeline_cli.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description="Table Generation Pipeline CLI")
    
    # Main paper and comparison papers
    parser.add_argument("--main-paper", "-m", required=True, help="Main paper ID")
    parser.add_argument("--papers", "-p", nargs="+", help="Additional paper IDs to compare")
    
    # Pipeline configuration
    parser.add_argument(
        "--criterion-strategy", "-c",
        choices=["hybrid", "boolean_then_expand", "direct_boolean"],
        default="hybrid",
        help="Criterion generation strategy"
    )
    parser.add_argument(
        "--content-strategy", "-g",
        choices=["rag", "all_chunks"],
        default="rag",
        help="Content generation strategy"
    )
    parser.add_argument(
        "--merging-strategy", "-s",
        choices=["full_table", "pairwise"],
        default="full_table",
        help="Merging strategy"
    )
    
    # Additional options
    parser.add_argument(
        "--experiment", "-e",
        action="store_true",
        help="Run experiments with different configurations"
    )
    parser.add_argument(
        "--visualize", "-v",
        action="store_true",
        help="Visualize the results"
    )
    parser.add_argument(
        "--output", "-o",
        default="results",
        help="Output directory for artifacts"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def map_criterion_strategy(strategy_str: str) -> CriterionGenerationStrategy:
    """Map string representation to criterion generation strategy enum"""
    if strategy_str == "hybrid":
        return CriterionGenerationStrategy.HYBRID
    elif strategy_str == "boolean_then_expand":
        return CriterionGenerationStrategy.BOOLEAN_THEN_EXPAND
    elif strategy_str == "direct_boolean":
        return CriterionGenerationStrategy.DIRECT_BOOLEAN
    else:
        raise ValueError(f"Unknown criterion generation strategy: {strategy_str}")


def map_content_strategy(strategy_str: str) -> ContentGenerationStrategy:
    """Map string representation to content generation strategy enum"""
    if strategy_str == "rag":
        return ContentGenerationStrategy.RAG
    elif strategy_str == "all_chunks":
        return ContentGenerationStrategy.ALL_CHUNKS
    else:
        raise ValueError(f"Unknown content generation strategy: {strategy_str}")


def map_merging_strategy(strategy_str: str) -> MergingStrategy:
    """Map string representation to merging strategy enum"""
    if strategy_str == "full_table":
        return MergingStrategy.FULL_TABLE
    elif strategy_str == "pairwise":
        return MergingStrategy.PAIRWISE
    else:
        raise ValueError(f"Unknown merging strategy: {strategy_str}")


def main():
    """Main function for the CLI"""
    args = parse_args()
    logger = setup_logging(args.verbose)
    
    # Import dependencies
    from repository.paper_repository import PaperRepository
    from services.openai_service import prompt_chatgpt, generate_embedding
    
    # Create repository
    repository = PaperRepository()
    
    # Get paper IDs
    main_paper_id = args.main_paper
    additional_paper_ids = args.papers or []
    all_paper_ids = [main_paper_id] + additional_paper_ids
    
    # Load papers
    papers = []
    for paper_id in all_paper_ids:
        paper_data = repository.get_paper_by_semantic_id(paper_id)
        if not paper_data:
            logger.error(f"Paper not found: {paper_id}")
            sys.exit(1)
            
        chunks = repository.get_chunks_by_semantic_id(paper_id)
        paper = convert_repo_paper_to_model(paper_data, chunks)
        papers.append(paper)
    
    # Create output directory if needed
    os.makedirs(args.output, exist_ok=True)
    
    if args.experiment:
        # Run experiments
        logger.info("Running experiments...")
        runner = ExperimentRunner(
            papers=papers,
            repository=repository,
            prompt_chatgpt=prompt_chatgpt,
            generate_embedding=generate_embedding
        )
        
        results = runner.run_all_experiments()
        runner.save_results(f"{args.output}/experiment_results.json")
        
        if args.visualize:
            runner.visualize_results(args.output)
        
        # Print summary
        summary = runner.compare_results()["summary"]
        print("\nExperiment Results Summary:")
        print(f"Best by time: {summary['best_by_time']}")
        print(f"Best by criteria count: {summary['best_by_criteria_count']}")
        print(f"Best by cell coverage: {summary['best_by_cell_coverage']}")
        
    else:
        # Run single pipeline configuration
        logger.info("Running pipeline with specified configuration...")
        
        # Create pipeline configuration
        config = PipelineConfig(
            criterion_generation_strategy=map_criterion_strategy(args.criterion_strategy),
            content_generation_strategy=map_content_strategy(args.content_strategy),
            merging_strategy=map_merging_strategy(args.merging_strategy)
        )
        
        # Create and run pipeline
        pipeline = PipelineFactory.create(
            config=config,
            repository=repository,
            prompt_chatgpt=prompt_chatgpt,
            generate_embedding=generate_embedding
        )
        
        comparison_table = pipeline.run(papers)
        
        # Save results
        with open(f"{args.output}/comparison_table.json", "w") as f:
            # Convert to serializable format
            table_dict = {
                "papers": [p.id for p in comparison_table.papers],
                "criteria": [
                    {
                        "criterion": c.criterion,
                        "description": c.description,
                        "papers": c.papers,
                        "is_boolean": c.is_boolean
                    }
                    for c in comparison_table.criteria
                ],
                "cells": [
                    {
                        "paper_id": cell.paper_id,
                        "criterion": cell.criterion,
                        "value": cell.value
                    }
                    for cell in comparison_table.cells
                ]
            }
            json.dump(table_dict, f, indent=2)
        
        # Display the table
        if args.visualize:
            display_comparison_table(comparison_table, repository)
        
        # Print summary
        print("\nComparison Table Generated:")
        print(f"Papers: {len(comparison_table.papers)}")
        print(f"Criteria: {len(comparison_table.criteria)}")
        print(f"Cells: {len(comparison_table.cells)}")
        print(f"Results saved to {args.output}/comparison_table.json")


if __name__ == "__main__":
    main()