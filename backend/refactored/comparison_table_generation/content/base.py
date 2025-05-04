"""
comparison_table_generation/content/base.py

Abstract base class for content generation
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Callable, Any
from ..core.models import Paper, Criterion, TableCell


class ContentGenerator(ABC):
    """Abstract base class for content generation strategies"""
    
    def __init__(self, prompt_chatgpt: Callable, **kwargs):
        self.prompt_chatgpt = prompt_chatgpt
        self.kwargs = kwargs
    
    @abstractmethod
    def generate(self, papers: List[Paper], criteria: List[Criterion]) -> List[TableCell]:
        """Generate table cells for each paper-criterion combination"""
        pass