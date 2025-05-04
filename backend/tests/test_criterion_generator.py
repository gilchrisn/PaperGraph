"""
comparison_table_generation/tests/test_criterion_generator.py

Tests for the criterion generation components
"""

import unittest
from unittest.mock import MagicMock, patch
import json

from ..core.models import Paper, PaperChunk, Criterion
from ..criterion.hybrid import HybridCriterionGenerator
from ..criterion.boolean import BooleanCriterionGenerator


class TestHybridCriterionGenerator(unittest.TestCase):
    """Test the hybrid criterion generation strategy"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the prompt_chatgpt function
        self.mock_prompt_chatgpt = MagicMock()
        self.mock_prompt_chatgpt.return_value = json.dumps({
            "comparison_points": [
                {"criterion": "test_criterion", "description": "test description"}
            ]
        })
        
        # Mock the generate_embedding function
        self.mock_generate_embedding = MagicMock()
        self.mock_generate_embedding.return_value = [0.1, 0.2, 0.3]
        
        # Create a generator instance
        self.generator = HybridCriterionGenerator(
            prompt_chatgpt=self.mock_prompt_chatgpt,
            generate_embedding=self.mock_generate_embedding
        )
        
        # Create test papers
        self.test_papers = [
            Paper(
                id="paper1",
                title="Test Paper 1",
                content="This is a test paper content.",
                chunks=[
                    PaperChunk(
                        paper_id="paper1",
                        section_title="Introduction",
                        chunk_text="This is the introduction.",
                        embedding=[0.1, 0.2, 0.3]
                    ),
                    PaperChunk(
                        paper_id="paper1",
                        section_title="Methods",
                        chunk_text="These are the methods.",
                        embedding=[0.4, 0.5, 0.6]
                    )
                ]
            ),
            Paper(
                id="paper2",
                title="Test Paper 2",
                content="This is another test paper content.",
                chunks=[
                    PaperChunk(
                        paper_id="paper2",
                        section_title="Introduction",
                        chunk_text="This is the second introduction.",
                        embedding=[0.7, 0.8, 0.9]
                    )
                ]
            )
        ]
    
    def test_generate(self):
        """Test the generate method"""
        # Mock additional methods
        with patch.object(self.generator, '_generate_paper_summaries') as mock_summaries, \
             patch.object(self.generator, '_generate_initial_criteria') as mock_initial, \
             patch.object(self.generator, '_refine_criteria') as mock_refine, \
             patch.object(self.generator, '_refine_second_pass') as mock_second_pass:
            
            # Set return values
            mock_summaries.return_value = {"paper1": ["summary1"], "paper2": ["summary2"]}
            mock_initial.return_value = [
                Criterion(criterion="c1", description="d1", papers=[], is_boolean=False)
            ]
            mock_refine.return_value = [
                Criterion(criterion="c1", description="d1 refined", papers=["paper1"], is_boolean=True)
            ]
            mock_second_pass.return_value = [
                Criterion(criterion="c1", description="d1 refined", papers=["paper1"], is_boolean=True)
            ]
            
            # Call the method
            result = self.generator.generate(self.test_papers)
            
            # Assertions
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].criterion, "c1")
            self.assertEqual(result[0].description, "d1 refined")
            self.assertEqual(result[0].papers, ["paper1"])
            self.assertTrue(result[0].is_boolean)
            
            # Verify method calls
            mock_summaries.assert_called_once_with(self.test_papers)
            mock_initial.assert_called_once()
            mock_refine.assert_called_once()
            mock_second_pass.assert_called_once()
    
    def test_validate_criterion(self):
        """Test criterion validation"""
        # Valid criterion
        valid = Criterion(
            criterion="test",
            description="description",
            papers=[],
            is_boolean=True
        )
        self.assertTrue(self.generator.validate_criterion(valid))
        
        # Invalid - empty criterion
        invalid1 = Criterion(
            criterion="",
            description="description",
            papers=[],
            is_boolean=True
        )
        self.assertFalse(self.generator.validate_criterion(invalid1))
        
        # Invalid - empty description
        invalid2 = Criterion(
            criterion="test",
            description="",
            papers=[],
            is_boolean=True
        )
        self.assertFalse(self.generator.validate_criterion(invalid2))
        
        # Invalid - criterion too long
        invalid3 = Criterion(
            criterion="x" * 51,  # Longer than 50 chars
            description="description",
            papers=[],
            is_boolean=True
        )
        self.assertFalse(self.generator.validate_criterion(invalid3))


class TestBooleanCriterionGenerator(unittest.TestCase):
    """Test the boolean criterion generation strategy"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the prompt_chatgpt function
        self.mock_prompt_chatgpt = MagicMock()
        self.mock_prompt_chatgpt.return_value = json.dumps({
            "criteria": [
                {"criterion": "test_criterion", "description": "test description", "is_boolean": True}
            ]
        })
        
        # Create a generator instance
        self.generator = BooleanCriterionGenerator(
            prompt_chatgpt=self.mock_prompt_chatgpt,
            expand_iterations=2
        )
        
        # Create test papers
        self.test_papers = [
            Paper(
                id="paper1",
                title="Test Paper 1",
                content="This is a test paper content.",
                chunks=[
                    PaperChunk(
                        paper_id="paper1",
                        section_title="Introduction",
                        chunk_text="This is the introduction.",
                        embedding=[0.1, 0.2, 0.3]
                    )
                ]
            )
        ]
    
    def test_generate(self):
        """Test the generate method"""
        # Mock additional methods
        with patch.object(self.generator, '_generate_criteria_for_paper') as mock_criteria, \
             patch.object(self.generator, '_merge_criteria') as mock_merge:
            
            # Set return values
            mock_criteria.return_value = [
                Criterion(criterion="c1", description="d1", papers=["paper1"], is_boolean=True)
            ]
            mock_merge.return_value = [
                Criterion(criterion="c1", description="d1", papers=["paper1"], is_boolean=True)
            ]
            
            # Call the method
            result = self.generator.generate(self.test_papers)
            
            # Assertions
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0].criterion, "c1")
            self.assertEqual(result[0].description, "d1")
            self.assertEqual(result[0].papers, ["paper1"])
            self.assertTrue(result[0].is_boolean)
            
            # Verify method calls
            mock_criteria.assert_called_once_with(self.test_papers[0])
            mock_merge.assert_called_once()