"""
comparison_table_generation/experiments/metrics.py

Metrics for evaluating pipeline performance
"""

import time
from typing import Dict, Any, List
from ..core.models import ComparisonTable


class PipelineMetrics:
    """Calculates metrics for pipeline evaluation"""
    
    @staticmethod
    def calculate(table: ComparisonTable, execution_time: float) -> Dict[str, Any]:
        """
        Calculate various metrics for a comparison table
        
        Parameters:
            table: The comparison table to evaluate
            execution_time: Time taken to generate the table (in seconds)
            
        Returns:
            Dictionary of metrics
        """
        metrics = {
            "num_papers": len(table.papers),
            "num_criteria": len(table.criteria),
            "num_cells": len(table.cells),
            "execution_time": execution_time,
            "criteria_per_paper": len(table.criteria) / len(table.papers) if table.papers else 0,
            "cell_coverage": PipelineMetrics._calculate_cell_coverage(table),
            "boolean_ratio": PipelineMetrics._calculate_boolean_ratio(table),
            "avg_criterion_length": PipelineMetrics._calculate_avg_criterion_length(table),
            "missing_values_percent": PipelineMetrics._calculate_missing_values(table),
            "avg_paper_length": PipelineMetrics._calculate_avg_paper_length(table),
            "avg_description_length": PipelineMetrics._calculate_avg_description_length(table)
        }
        return metrics
    
    @staticmethod
    def _calculate_cell_coverage(table: ComparisonTable) -> float:
        """Calculate percentage of cells with non-null values"""
        expected_cells = len(table.papers) * len(table.criteria)
        if expected_cells == 0:
            return 0.0
        filled_cells = sum(1 for cell in table.cells if cell.value is not None)
        return filled_cells / expected_cells
    
    @staticmethod
    def _calculate_boolean_ratio(table: ComparisonTable) -> float:
        """Calculate ratio of boolean criteria"""
        if not table.criteria:
            return 0.0
        boolean_count = sum(1 for criterion in table.criteria if criterion.is_boolean)
        return boolean_count / len(table.criteria)
    
    @staticmethod
    def _calculate_avg_criterion_length(table: ComparisonTable) -> float:
        """Calculate average length of criterion names"""
        if not table.criteria:
            return 0.0
        total_length = sum(len(criterion.criterion) for criterion in table.criteria)
        return total_length / len(table.criteria)
    
    @staticmethod
    def _calculate_missing_values(table: ComparisonTable) -> float:
        """Calculate percentage of missing values"""
        total_cells = len(table.cells)
        if total_cells == 0:
            return 0.0
        missing_cells = sum(1 for cell in table.cells if cell.value is None or cell.value == "N/A")
        return (missing_cells / total_cells) * 100
    
    @staticmethod
    def _calculate_avg_paper_length(table: ComparisonTable) -> float:
        """Calculate average paper length by chunks"""
        if not table.papers:
            return 0.0
        total_chunks = sum(len(paper.chunks) for paper in table.papers)
        return total_chunks / len(table.papers)
    
    @staticmethod
    def _calculate_avg_description_length(table: ComparisonTable) -> float:
        """Calculate average description length"""
        if not table.criteria:
            return 0.0
        total_length = sum(len(criterion.description) for criterion in table.criteria)
        return total_length / len(table.criteria)


class ExperimentResults:
    """Class for storing and comparing experiment results"""
    
    def __init__(self, name: str, config: Dict[str, Any], metrics: Dict[str, Any], execution_time: float):
        self.name = name
        self.config = config
        self.metrics = metrics
        self.execution_time = execution_time
    
    def __str__(self):
        """String representation of results"""
        return (f"Experiment: {self.name}\n"
                f"Execution time: {self.execution_time:.2f} seconds\n"
                f"Criteria: {self.metrics['num_criteria']}\n"
                f"Cell coverage: {self.metrics['cell_coverage']:.2f}\n"
                f"Boolean ratio: {self.metrics['boolean_ratio']:.2f}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary"""
        return {
            "name": self.name,
            "config": self.config,
            "metrics": self.metrics,
            "execution_time": self.execution_time
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ExperimentResults':
        """Create ExperimentResults from dictionary"""
        return ExperimentResults(
            name=data["name"],
            config=data["config"],
            metrics=data["metrics"],
            execution_time=data["execution_time"]
        )