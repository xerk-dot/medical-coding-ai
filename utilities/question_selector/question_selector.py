#!/usr/bin/env python3
"""
Question Selector Tool

This tool creates a new test question/answer bank by selecting questions from available test banks.
The selected questions and answers are stored in 00_question_banks as final_questions.json and final_answers.json.
"""

import json
import os
import random
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import argparse
from datetime import datetime


class QuestionSelector:
    def __init__(self, base_path: str = "../../00_question_banks"):
        self.base_path = Path(base_path)
        self.available_tests = self._discover_tests()
        
    def _discover_tests(self) -> Dict[str, Dict[str, Path]]:
        """Discover available test banks in the 00_question_banks directory."""
        tests = {}
        
        if not self.base_path.exists():
            raise FileNotFoundError(f"Question banks directory not found: {self.base_path}")
        
        # Look for test directories
        for test_dir in self.base_path.iterdir():
            if test_dir.is_dir() and test_dir.name.startswith("test_"):
                test_name = test_dir.name
                questions_file = test_dir / f"{test_name}_questions.json"
                answers_file = test_dir / f"{test_name}_answers.json"
                
                if questions_file.exists():
                    tests[test_name] = {
                        "questions": questions_file,
                        "answers": answers_file if answers_file.exists() else None
                    }
        
        return tests
    
    def load_test_data(self, test_name: str) -> Tuple[List[Dict], List[Dict]]:
        """Load questions and answers for a specific test."""
        if test_name not in self.available_tests:
            raise ValueError(f"Test '{test_name}' not found. Available tests: {list(self.available_tests.keys())}")
        
        test_info = self.available_tests[test_name]
        
        # Load questions
        with open(test_info["questions"], 'r') as f:
            questions = json.load(f)
        
        # Load answers if available
        answers = []
        if test_info["answers"]:
            with open(test_info["answers"], 'r') as f:
                answers = json.load(f)
        
        return questions, answers
    
    def create_question_bank(self, 
                           test_selections: Dict[str, List[int]], 
                           output_name: str = "final",
                           shuffle: bool = True,
                           metadata: Optional[Dict] = None) -> Tuple[str, str]:
        """
        Create a new question bank by selecting specific questions from test banks.
        
        Args:
            test_selections: Dict mapping test names to lists of question numbers to include
                           e.g., {"test_1": [1, 5, 10, 15], "test_2": [2, 4, 6, 8]}
            output_name: Base name for output files (default: "final")
            shuffle: Whether to shuffle the selected questions
            metadata: Optional metadata to include in the output
            
        Returns:
            Tuple of (questions_file_path, answers_file_path)
        """
        selected_questions = []
        selected_answers = []
        
        # Process each test selection
        for test_name, question_numbers in test_selections.items():
            questions, answers = self.load_test_data(test_name)
            
            # Convert question numbers to indices (1-based to 0-based)
            for q_num in question_numbers:
                if 1 <= q_num <= len(questions):
                    # Find the question with the matching question_number
                    question = next((q for q in questions if q.get("question_number") == q_num), None)
                    if question:
                        # Add source information
                        question["source_test"] = test_name
                        question["original_question_number"] = q_num
                        selected_questions.append(question)
                        
                        # Find corresponding answer if available
                        if answers:
                            answer = next((a for a in answers if a.get("question_number") == q_num), None)
                            if answer:
                                answer["source_test"] = test_name
                                answer["original_question_number"] = q_num
                                selected_answers.append(answer)
                else:
                    print(f"Warning: Question {q_num} not found in {test_name} (max: {len(questions)})")
        
        # Shuffle if requested
        if shuffle:
            # Create a mapping to maintain question-answer correspondence
            indices = list(range(len(selected_questions)))
            random.shuffle(indices)
            
            selected_questions = [selected_questions[i] for i in indices]
            if selected_answers:
                selected_answers = [selected_answers[i] for i in indices]
        
        # Renumber questions in the new bank
        for i, question in enumerate(selected_questions, 1):
            question["question_number"] = i
        
        for i, answer in enumerate(selected_answers, 1):
            answer["question_number"] = i
        
        # Create output structure with metadata
        output_questions = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "total_questions": len(selected_questions),
                "source_tests": list(test_selections.keys()),
                "shuffled": shuffle,
                **(metadata or {})
            },
            "questions": selected_questions
        }
        
        output_answers = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "total_answers": len(selected_answers),
                "source_tests": list(test_selections.keys()),
                "shuffled": shuffle,
                **(metadata or {})
            },
            "answers": selected_answers
        }
        
        # Write output files
        questions_file = self.base_path / f"{output_name}_questions.json"
        answers_file = self.base_path / f"{output_name}_answers.json"
        
        with open(questions_file, 'w') as f:
            json.dump(output_questions["questions"], f, indent=2)
        
        if selected_answers:
            with open(answers_file, 'w') as f:
                json.dump(output_answers["answers"], f, indent=2)
        
        return str(questions_file), str(answers_file) if selected_answers else None
    
    def create_random_bank(self, 
                         num_questions_per_test: Dict[str, int],
                         output_name: str = "final",
                         metadata: Optional[Dict] = None) -> Tuple[str, str]:
        """
        Create a question bank by randomly selecting questions from each test.
        
        Args:
            num_questions_per_test: Dict mapping test names to number of questions to select
                                  e.g., {"test_1": 50, "test_2": 50}
            output_name: Base name for output files
            metadata: Optional metadata to include
            
        Returns:
            Tuple of (questions_file_path, answers_file_path)
        """
        test_selections = {}
        
        for test_name, num_questions in num_questions_per_test.items():
            questions, _ = self.load_test_data(test_name)
            available_numbers = [q["question_number"] for q in questions]
            
            # Randomly select question numbers
            selected_numbers = random.sample(available_numbers, 
                                           min(num_questions, len(available_numbers)))
            test_selections[test_name] = selected_numbers
        
        return self.create_question_bank(test_selections, output_name, True, metadata)
    
    def list_available_tests(self):
        """Print information about available test banks."""
        print("Available test banks:")
        print("-" * 50)
        
        for test_name, test_info in self.available_tests.items():
            questions, answers = self.load_test_data(test_name)
            print(f"\n{test_name}:")
            print(f"  Questions: {len(questions)}")
            print(f"  Answers: {'Yes' if answers else 'No'}")
            
            # Show question types if available
            question_types = set(q.get("question_type", "Unknown") for q in questions)
            print(f"  Question types: {', '.join(question_types)}")


def main():
    parser = argparse.ArgumentParser(description="Create custom question banks from available tests")
    parser.add_argument("--list", action="store_true", help="List available test banks")
    parser.add_argument("--random", action="store_true", help="Randomly select questions")
    parser.add_argument("--output", default="final", help="Output file base name (default: final)")
    parser.add_argument("--test1-count", type=int, default=50, help="Number of questions from test_1")
    parser.add_argument("--test2-count", type=int, default=50, help="Number of questions from test_2")
    parser.add_argument("--no-shuffle", action="store_true", help="Don't shuffle the final questions")
    
    args = parser.parse_args()
    
    # Initialize selector
    selector = QuestionSelector()
    
    if args.list:
        selector.list_available_tests()
        return
    
    if args.random:
        # Create random selection
        questions_file, answers_file = selector.create_random_bank(
            {
                "test_1": args.test1_count,
                "test_2": args.test2_count
            },
            output_name=args.output,
            metadata={
                "selection_method": "random",
                "test1_count": args.test1_count,
                "test2_count": args.test2_count
            }
        )
    else:
        # Example: Create a specific selection
        # You can modify this to accept specific question numbers via command line
        questions_file, answers_file = selector.create_question_bank(
            {
                "test_1": list(range(1, args.test1_count + 1)),
                "test_2": list(range(1, args.test2_count + 1))
            },
            output_name=args.output,
            shuffle=not args.no_shuffle,
            metadata={
                "selection_method": "sequential",
                "test1_count": args.test1_count,
                "test2_count": args.test2_count
            }
        )
    
    print(f"\nQuestion bank created successfully!")
    print(f"Questions file: {questions_file}")
    if answers_file:
        print(f"Answers file: {answers_file}")


if __name__ == "__main__":
    main()