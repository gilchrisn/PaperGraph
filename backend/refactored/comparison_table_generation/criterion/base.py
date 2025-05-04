"""
comparison_table_generation/criterion/base.py

Abstract base classes for criterion generation
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Callable, Any
from ..core.models import Paper, Criterion


class CriterionGenerator(ABC):
    """Abstract base class for criterion generation strategies"""
    
    def __init__(self, prompt_chatgpt: Callable, **kwargs):
        self.prompt_chatgpt = prompt_chatgpt
        self.kwargs = kwargs
    
    @abstractmethod
    def generate(self, papers: List[Paper]) -> List[Criterion]:
        """Generate criteria for the given papers"""
        pass
    
    def refine_criterion(self, criterion: Criterion, papers: List[Paper]) -> Criterion:
        """Refine a single criterion based on paper content"""
        # Common refinement logic can go here
        return criterion
    
    def validate_criterion(self, criterion: Criterion) -> bool:
        """Validate that a criterion meets quality standards"""
        if not criterion.criterion or not criterion.description:
            return False
        if len(criterion.criterion) < 3 or len(criterion.criterion) > 50:
            return False
        return True