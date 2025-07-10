#!/usr/bin/env python3
"""
Question Type Classifier

This script analyzes questions in the test_1_questions.json file and classifies them
into categories based on the presence of key terms:
1. CPT - Questions asking about CPT codes
2. ICD - Questions asking about ICD codes  
3. HCPCS - Questions asking about HCPCS codes
4. other - Questions that don't mention these coding systems

The script uses regex patterns to identify these terms and appends the question_type
field to each question in the JSON file.
"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, List


def classify_question_type(question_text: str) -> str:
    """
    Classify a question based on the presence of CPT, ICD, or HCPCS terms.
    
    Args:
        question_text: The question text to analyze
        
    Returns:
        str: One of 'CPT', 'ICD', 'HCPCS', or 'other'
    """
    # Convert to lowercase for case-insensitive matching
    text_lower = question_text.lower()
    
    # Define regex patterns for each coding system
    cpt_patterns = [
        r'\bcpt\b',                    # "CPT"
        r'\bcpt\s+code\b',            # "CPT code"
        r'\bwhich\s+cpt\b',           # "which CPT"
        r'\bcpt\s+coding\b'           # "CPT coding"
    ]
    
    icd_patterns = [
        r'\bicd\b',                    # "ICD"
        r'\bicd\s*-?\s*10\b',         # "ICD-10" or "ICD 10"
        r'\bicd\s*-?\s*10\s*-?\s*cm\b', # "ICD-10-CM"
        r'\bwhich\s+icd\b',           # "which ICD"
        r'\bicd\s+code\b'             # "ICD code"
    ]
    
    hcpcs_patterns = [
        r'\bhcpcs\b',                 # "HCPCS"
        r'\bhcpcs\s+level\s+ii\b',    # "HCPCS Level II"
        r'\bwhich\s+hcpcs\b',         # "which HCPCS"
        r'\bhcpcs\s+code\b'           # "HCPCS code"
    ]
    
    # Check for CPT patterns
    for pattern in cpt_patterns:
        if re.search(pattern, text_lower):
            return "CPT"
    
    # Check for ICD patterns
    for pattern in icd_patterns:
        if re.search(pattern, text_lower):
            return "ICD"
    
    # Check for HCPCS patterns
    for pattern in hcpcs_patterns:
        if re.search(pattern, text_lower):
            return "HCPCS"
    
    # If none of the above patterns match, classify as 'other'
    return "other"


def load_questions_json(file_path: str) -> List[Dict]:
    """
    Load questions from JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of question dictionaries
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        print(f"✅ Loaded {len(questions)} questions from {file_path}")
        return questions
    except FileNotFoundError:
        print(f"❌ Error: File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in file: {e}")
        return []
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return []


def save_questions_json(questions: List[Dict], file_path: str) -> bool:
    """
    Save questions back to JSON file.
    
    Args:
        questions: List of question dictionaries
        file_path: Path to save the JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved {len(questions)} questions to {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False


def classify_all_questions(questions: List[Dict]) -> List[Dict]:
    """
    Classify all questions and add question_type field.
    
    Args:
        questions: List of question dictionaries
        
    Returns:
        List of question dictionaries with question_type added
    """
    print("🔍 Classifying questions by type...")
    
    # Statistics tracking
    type_counts = {"CPT": 0, "ICD": 0, "HCPCS": 0, "other": 0}
    
    for question in questions:
        question_text = question.get("question", "")
        question_type = classify_question_type(question_text)
        
        # Add the question_type field
        question["question_type"] = question_type
        
        # Update statistics
        type_counts[question_type] += 1
    
    # Print classification statistics
    print("\n📊 Classification Results:")
    print(f"   CPT questions:   {type_counts['CPT']:3d}")
    print(f"   ICD questions:   {type_counts['ICD']:3d}")
    print(f"   HCPCS questions: {type_counts['HCPCS']:3d}")
    print(f"   Other questions: {type_counts['other']:3d}")
    print(f"   Total:           {sum(type_counts.values()):3d}")
    
    return questions


def show_examples(questions: List[Dict], max_examples: int = 3):
    """
    Show examples of each question type for verification.
    
    Args:
        questions: List of classified questions
        max_examples: Maximum number of examples to show per type
    """
    print("\n📝 Examples by Question Type:")
    
    examples_by_type = {"CPT": [], "ICD": [], "HCPCS": [], "other": []}
    
    # Collect examples
    for question in questions:
        question_type = question.get("question_type", "other")
        if len(examples_by_type[question_type]) < max_examples:
            examples_by_type[question_type].append(question)
    
    # Display examples
    for question_type in ["CPT", "ICD", "HCPCS", "other"]:
        print(f"\n{question_type} Questions:")
        if examples_by_type[question_type]:
            for i, question in enumerate(examples_by_type[question_type], 1):
                question_num = question.get("question_number", "?")
                question_text = question.get("question", "")[:100] + "..."
                print(f"  {i}. Q{question_num}: {question_text}")
        else:
            print("  (No examples found)")


def main():
    """Main function to run the question type classifier."""
    parser = argparse.ArgumentParser(
        description="Classify questions by type (CPT, ICD, HCPCS, other) and update JSON file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Classify questions in the default file
  %(prog)s
  
  # Specify a different JSON file
  %(prog)s --input custom_questions.json
  
  # Show more examples of each type
  %(prog)s --examples 5
  
  # Show examples but don't save changes
  %(prog)s --dry-run
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        default="../../00_question_banks/test_1/test_1_questions.json",
        help="Path to input JSON file (default: ../../00_question_banks/test_1/test_1_questions.json)"
    )
    
    parser.add_argument(
        "--examples", "-e",
        type=int,
        default=3,
        help="Number of examples to show per question type (default: 3)"
    )
    
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show classification results but don't save changes"
    )
    
    args = parser.parse_args()
    
    # Resolve file path
    input_path = Path(args.input)
    if not input_path.is_absolute():
        # Make relative to script location
        script_dir = Path(__file__).parent
        input_path = script_dir / args.input
    
    input_path = input_path.resolve()
    
    print(f"🎯 Question Type Classifier")
    print(f"📁 Input file: {input_path}")
    
    # Check if file exists
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        return 1
    
    # Load questions
    questions = load_questions_json(str(input_path))
    if not questions:
        return 1
    
    # Classify questions
    classified_questions = classify_all_questions(questions)
    
    # Show examples
    if args.examples > 0:
        show_examples(classified_questions, args.examples)
    
    # Save results (unless dry-run)
    if not args.dry_run:
        if save_questions_json(classified_questions, str(input_path)):
            print(f"\n✅ Successfully updated {input_path}")
        else:
            return 1
    else:
        print(f"\n🔍 Dry run complete - no changes saved")
    
    print("✅ Classification complete!")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main()) 