"""
comparison_table_generation/experiments/runner.py

Experiment runner for testing different pipeline configurations
"""

import time
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

from ..core.models import (
    Paper, PipelineConfig, ComparisonTable, 
    CriterionGenerationStrategy, ContentGenerationStrategy, MergingStrategy
)
from ..core.pipeline import PipelineFactory
from .metrics import PipelineMetrics, ExperimentResults

logger = logging.getLogger(__name__)


class ExperimentRunner:
    """Runner for testing different pipeline configurations"""
    
    def __init__(
        self,
        papers: List[Paper],
        repository,
        prompt_chatgpt,
        generate_embedding
    ):
        self.papers = papers
        self.repository = repository
        self.prompt_chatgpt = prompt_chatgpt
        self.generate_embedding = generate_embedding
        self.results = []
    
    def run_experiment(
        self, 
        config: PipelineConfig, 
        experiment_name: str
    ) -> ExperimentResults:
        """
        Run a single experiment with the given configuration
        
        Parameters:
            config: Pipeline configuration
            experiment_name: Name of the experiment
            
        Returns:
            ExperimentResults object with metrics
        """
        logger.info(f"Running experiment: {experiment_name}")
        
        # Create pipeline with config
        pipeline = PipelineFactory.create(
            config=config,
            repository=self.repository,
            prompt_chatgpt=self.prompt_chatgpt,
            generate_embedding=self.generate_embedding
        )
        
        # Run pipeline and measure time
        start_time = time.time()
        comparison_table = pipeline.run(self.papers)
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Calculate metrics
        metrics = PipelineMetrics.calculate(
            table=comparison_table,
            execution_time=execution_time
        )
        
        # Store results
        result = ExperimentResults(
            name=experiment_name,
            config=config.__dict__,
            metrics=metrics,
            execution_time=execution_time
        )
        self.results.append(result)
        
        return result
    
    def run_all_experiments(self) -> List[ExperimentResults]:
        """
        Run all standard experiment configurations
        
        Returns:
            List of ExperimentResults objects
        """
        experiments = [
            # Hybrid RAG
            {
                "name": "Hybrid RAG",
                "config": PipelineConfig(
                    criterion_generation_strategy=CriterionGenerationStrategy.HYBRID,
                    content_generation_strategy=ContentGenerationStrategy.RAG,
                    merging_strategy=MergingStrategy.FULL_TABLE
                )
            },
            # Boolean RAG
            {
                "name": "Boolean RAG",
                "config": PipelineConfig(
                    criterion_generation_strategy=CriterionGenerationStrategy.BOOLEAN_THEN_EXPAND,
                    content_generation_strategy=ContentGenerationStrategy.RAG,
                    merging_strategy=MergingStrategy.FULL_TABLE
                )
            },
            # Hybrid All Chunks
            {
                "name": "Hybrid All Chunks",
                "config": PipelineConfig(
                    criterion_generation_strategy=CriterionGenerationStrategy.HYBRID,
                    content_generation_strategy=ContentGenerationStrategy.ALL_CHUNKS,
                    merging_strategy=MergingStrategy.FULL_TABLE
                )
            },
            # Boolean Pairwise
            {
                "name": "Boolean Pairwise",
                "config": PipelineConfig(
                    criterion_generation_strategy=CriterionGenerationStrategy.BOOLEAN_THEN_EXPAND,
                    content_generation_strategy=ContentGenerationStrategy.RAG,
                    merging_strategy=MergingStrategy.PAIRWISE
                )
            }
        ]
        
        for exp in experiments:
            self.run_experiment(exp["config"], exp["name"])
        
        return self.results
    
    def compare_results(self) -> Dict[str, Any]:
        """
        Compare results from all experiments
        
        Returns:
            Dictionary with comparison results
        """
        if not self.results:
            logger.warning("No experiment results to compare")
            return {}
        
        comparison = {
            "experiments": [result.to_dict() for result in self.results],
            "summary": {
                "best_by_time": min(self.results, key=lambda x: x.execution_time).name,
                "best_by_criteria_count": min(self.results, key=lambda x: x.metrics["num_criteria"]).name,
                "best_by_cell_coverage": max(self.results, key=lambda x: x.metrics["cell_coverage"]).name
            }
        }
        return comparison
    
    def save_results(self, filepath: str) -> None:
        """
        Save experiment results to file
        
        Parameters:
            filepath: Path to save the results
        """
        with open(filepath, 'w') as f:
            json.dump([result.to_dict() for result in self.results], f, indent=4)
        logger.info(f"Results saved to {filepath}")
    
    def load_results(self, filepath: str) -> None:
        """
        Load experiment results from file
        
        Parameters:
            filepath: Path to load the results from
        """
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.results = [ExperimentResults.from_dict(item) for item in data]
        logger.info(f"Loaded {len(self.results)} results from {filepath}")
    
    def visualize_results(self, output_dir: Optional[str] = None) -> None:
        """
        Visualize experiment results with matplotlib
        
        Parameters:
            output_dir: Directory to save the visualizations (optional)
        """
        if not self.results:
            logger.warning("No results to visualize")
            return
        
        # Create output directory if needed
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Convert results to DataFrame for easier visualization
        data = []
        for result in self.results:
            row = {
                "Experiment": result.name,
                "Execution Time (s)": result.execution_time,
                "Criteria Count": result.metrics["num_criteria"],
                "Cell Coverage (%)": result.metrics["cell_coverage"] * 100,
                "Boolean Ratio (%)": result.metrics["boolean_ratio"] * 100,
                "Missing Values (%)": result.metrics["missing_values_percent"]
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Create visualizations
        self._plot_execution_time(df, output_dir)
        self._plot_criteria_metrics(df, output_dir)
        self._plot_comparison_radar(df, output_dir)
    
    def _plot_execution_time(self, df, output_dir):
        """Plot execution time comparison"""
        plt.figure(figsize=(10, 6))
        bars = plt.bar(df["Experiment"], df["Execution Time (s)"], color='skyblue')
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}s',
                    ha='center', va='bottom')
        
        plt.title("Execution Time Comparison")
        plt.xlabel("Experiment")
        plt.ylabel("Time (seconds)")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        
        if output_dir:
            plt.savefig(f"{output_dir}/execution_time.png")
            plt.close()
        else:
            plt.show()
    
    def _plot_criteria_metrics(self, df, output_dir):
        """Plot criteria metrics comparison"""
        plt.figure(figsize=(12, 8))
        
        width = 0.25
        x = range(len(df["Experiment"]))
        
        plt.bar([i - width for i in x], df["Criteria Count"], width, label="Criteria Count", color="skyblue")
        plt.bar(x, df["Cell Coverage (%)"], width, label="Cell Coverage (%)", color="lightgreen")
        plt.bar([i + width for i in x], df["Boolean Ratio (%)"], width, label="Boolean Ratio (%)", color="salmon")
        
        plt.title("Criteria Metrics Comparison")
        plt.xlabel("Experiment")
        plt.ylabel("Value")
        plt.xticks(x, df["Experiment"], rotation=45, ha="right")
        plt.legend()
        plt.tight_layout()
        
        if output_dir:
            plt.savefig(f"{output_dir}/criteria_metrics.png")
            plt.close()
        else:
            plt.show()
    
    def _plot_comparison_radar(self, df, output_dir):
        """Plot radar chart comparison"""
        try:
            # Prepare data for radar chart
            metrics = ["Execution Time (s)", "Criteria Count", "Cell Coverage (%)", 
                      "Boolean Ratio (%)", "Missing Values (%)"]
            
            # Normalize data for radar chart
            df_norm = df.copy()
            for metric in metrics:
                if metric in ["Cell Coverage (%)", "Boolean Ratio (%)"]:
                    # Higher is better
                    df_norm[metric] = df[metric] / df[metric].max()
                else:
                    # Lower is better
                    df_norm[metric] = 1 - (df[metric] / df[metric].max())
            
            # Create radar chart
            plt.figure(figsize=(10, 10))
            ax = plt.subplot(111, polar=True)
            
            angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False).tolist()
            angles += angles[:1]  # Close the loop
            
            for i, exp in enumerate(df["Experiment"]):
                values = df_norm.loc[i, metrics].values.tolist()
                values += values[:1]  # Close the loop
                
                ax.plot(angles, values, linewidth=2, label=exp)
                ax.fill(angles, values, alpha=0.1)
            
            ax.set_thetagrids(np.degrees(angles[:-1]), metrics)
            ax.set_ylim(0, 1)
            plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
            plt.title("Experiment Comparison (Normalized Metrics)")
            
            if output_dir:
                plt.savefig(f"{output_dir}/comparison_radar.png")
                plt.close()
            else:
                plt.show()
        except Exception as e:
            logger.error(f"Error creating radar plot: {e}")