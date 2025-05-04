"""
comparison_table_generation/core/pipeline.py

Main pipeline orchestrator for the table generation process
"""

from typing import List, Dict, Type, Callable
import logging
from .models import (
    Paper, Criterion, TableCell, ComparisonTable, PipelineConfig,
    CriterionGenerationStrategy, ContentGenerationStrategy, MergingStrategy
)
from ..criterion.base import CriterionGenerator
from ..criterion.hybrid import HybridCriterionGenerator
from ..criterion.boolean import BooleanCriterionGenerator
from ..criterion.reduction import CriterionReducer
from ..content.base import ContentGenerator
from ..content.rag import RAGContentGenerator
from ..content.all_chunks import AllChunksContentGenerator

logger = logging.getLogger(__name__)


class TableGenerationPipeline:
    """Main pipeline for generating comparison tables"""
    
    def __init__(
        self,
        config: PipelineConfig,
        repository,
        prompt_chatgpt: Callable,
        generate_embedding: Callable
    ):
        self.config = config
        self.repository = repository
        self.prompt_chatgpt = prompt_chatgpt
        self.generate_embedding = generate_embedding
        
        # Initialize components based on config
        self.criterion_generator = self._init_criterion_generator()
        self.content_generator = self._init_content_generator()
        self.criterion_reducer = CriterionReducer(
            prompt_chatgpt=prompt_chatgpt,
            strategy=config.merging_strategy
        )
        
    def _init_criterion_generator(self) -> CriterionGenerator:
        """Initialize criterion generator based on strategy"""
        if self.config.criterion_generation_strategy == CriterionGenerationStrategy.HYBRID:
            return HybridCriterionGenerator(
                prompt_chatgpt=self.prompt_chatgpt,
                generate_embedding=self.generate_embedding
            )
        elif self.config.criterion_generation_strategy == CriterionGenerationStrategy.BOOLEAN_THEN_EXPAND:
            return BooleanCriterionGenerator(
                prompt_chatgpt=self.prompt_chatgpt,
                expand_iterations=self.config.expand_iterations
            )
        else:
            return BooleanCriterionGenerator(
                prompt_chatgpt=self.prompt_chatgpt,
                expand_iterations=0  # Direct boolean only
            )
    
    def _init_content_generator(self) -> ContentGenerator:
        """Initialize content generator based on strategy"""
        if self.config.content_generation_strategy == ContentGenerationStrategy.RAG:
            return RAGContentGenerator(
                prompt_chatgpt=self.prompt_chatgpt,
                generate_embedding=self.generate_embedding,
                top_k=self.config.retrieve_top_k
            )
        else:
            return AllChunksContentGenerator(
                prompt_chatgpt=self.prompt_chatgpt
            )
    
    def run(self, papers: List[Paper]) -> ComparisonTable:
        """Run the complete pipeline"""
        logger.info(f"Starting pipeline with {len(papers)} papers")
        
        # Step 1: Generate criteria
        logger.info("Generating criteria...")
        criteria = self.criterion_generator.generate(papers)
        logger.info(f"Generated {len(criteria)} criteria")
        
        # Step 2: Reduce/merge similar criteria
        logger.info("Reducing similar criteria...")
        reduced_criteria = self.criterion_reducer.reduce(criteria, papers)
        logger.info(f"Reduced to {len(reduced_criteria)} criteria")
        
        # Step 3: Generate content for each cell
        logger.info("Generating table content...")
        cells = self.content_generator.generate(papers, reduced_criteria)
        
        # Step 4: Create and return the comparison table
        table = ComparisonTable(
            papers=papers,
            criteria=reduced_criteria,
            cells=cells
        )
        
        logger.info("Pipeline complete")
        return table


class PipelineFactory:
    """Factory for creating pipeline instances"""
    
    @staticmethod
    def create(
        config: PipelineConfig,
        repository,
        prompt_chatgpt: Callable,
        generate_embedding: Callable
    ) -> TableGenerationPipeline:
        """Create a new pipeline instance"""
        return TableGenerationPipeline(
            config=config,
            repository=repository,
            prompt_chatgpt=prompt_chatgpt,
            generate_embedding=generate_embedding
        )
    
    @staticmethod
    def create_with_defaults(
        repository,
        prompt_chatgpt: Callable,
        generate_embedding: Callable
    ) -> TableGenerationPipeline:
        """Create a pipeline with default configuration"""
        return TableGenerationPipeline(
            config=PipelineConfig.default(),
            repository=repository,
            prompt_chatgpt=prompt_chatgpt,
            generate_embedding=generate_embedding
        )