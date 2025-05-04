"""
comparison_table_generation/core/models.py

Core data models for the table generation pipeline
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum, auto


class CriterionGenerationStrategy(Enum):
    """Strategies for generating criteria"""
    HYBRID = auto()
    BOOLEAN_THEN_EXPAND = auto()
    DIRECT_BOOLEAN = auto()
    TWO_PASS = auto()


class ContentGenerationStrategy(Enum):
    """Strategies for generating table content"""
    RAG = auto()  # Retrieval-Augmented Generation
    ALL_CHUNKS = auto()  # Full chunk processing


class MergingStrategy(Enum):
    """Strategies for merging similar criteria"""
    FULL_TABLE = auto()
    PAIRWISE = auto()


@dataclass
class Paper:
    """Represents a research paper"""
    id: str
    title: str
    content: str
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunks: List['PaperChunk'] = field(default_factory=list)


@dataclass
class PaperChunk:
    """Represents a chunk/section of a paper"""
    paper_id: str
    section_title: str
    chunk_text: str
    embedding: Optional[List[float]] = None


@dataclass
class Criterion:
    """Represents an evaluation criterion"""
    criterion: str
    description: str
    papers: List[str] = field(default_factory=list)
    is_boolean: bool = True


@dataclass
class TableCell:
    """Represents a cell in the comparison table"""
    paper_id: str
    criterion: str
    value: Any  # Can be bool, str, or None


@dataclass
class ComparisonTable:
    """Represents the complete comparison table"""
    papers: List[Paper]
    criteria: List[Criterion]
    cells: List[TableCell]
    
    def get_cell(self, paper_id: str, criterion: str) -> Optional[TableCell]:
        """Get a specific cell from the table"""
        for cell in self.cells:
            if cell.paper_id == paper_id and cell.criterion == criterion:
                return cell
        return None


@dataclass
class PipelineConfig:
    """Configuration for the table generation pipeline"""
    criterion_generation_strategy: CriterionGenerationStrategy
    content_generation_strategy: ContentGenerationStrategy
    merging_strategy: MergingStrategy
    expand_iterations: int = 3
    retrieve_top_k: int = 3
    max_boolean_criteria: int = 50
    similarity_threshold: float = 0.85
    
    @classmethod
    def default(cls) -> 'PipelineConfig':
        """Create default configuration"""
        return cls(
            criterion_generation_strategy=CriterionGenerationStrategy.HYBRID,
            content_generation_strategy=ContentGenerationStrategy.RAG,
            merging_strategy=MergingStrategy.FULL_TABLE
        )