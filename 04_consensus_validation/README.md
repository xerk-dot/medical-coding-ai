# Consensus Validation Tool

This tool validates the accuracy of AI consensus decisions against the official answer key.

## Overview

The consensus validation script compares the latest consensus report from the Medical Board AI Testing System with the official answer key to determine:

- How often the AI consensus matches the correct answer
- Which question types have the highest/lowest consensus accuracy
- Detailed breakdown of incorrect consensus decisions
- Questions where the correct answer led voting but didn't achieve consensus

## Usage

### Basic Validation
```bash
cd is_the_consensus_correct
python3 validate_consensus.py
```

## What It Does

### 1. **Data Loading**
- Loads the official answer key from `00_question_banks/test_1/test_1_answers.json`
- Finds the latest consensus report from `03_consensus_benchmarks/consensus_reports/`
- Loads question types from `00_question_banks/test_1/test_1_questions.json`

### 2. **Validation Process**
- Compares each consensus decision with the correct answer
- Calculates accuracy metrics overall and by question type
- Identifies patterns in incorrect consensus decisions

### 3. **Output**
- **Console Summary**: Comprehensive validation results
- **JSON Report**: Detailed validation report saved locally

## Output Format

### Console Output
```
🎯 CONSENSUS VALIDATION SUMMARY
============================================================
Total Questions: 100
Consensus Achieved: 69/100 (69.0%)
Consensus Correct: 52/69 (75.4% of consensus)
Overall Accuracy: 52/100 (52.0% of all questions)

📋 Accuracy by Question Type:
Type     Total  Consensus  Correct  Accuracy  
--------------------------------------------------
CPT      65     40         30       75.0%
HCPCS    7      4          3        75.0%
ICD      13     11         9        81.8%
other    15     14         10       71.4%

❌ Incorrect Consensus Decisions (17):
  Q3: Consensus=A (57.1%), Correct=D
    Votes: A:4, D:3✓
  Q12: Consensus=A (62.5%), Correct=B
    Votes: A:5, B:3✓
```

### JSON Report
```json
{
  "timestamp": "2025-07-09T18:45:00",
  "summary": {
    "total_questions": 100,
    "consensus_achieved": 69,
    "consensus_correct": 52,
    "consensus_accuracy": 75.4,
    "overall_accuracy": 52.0
  },
  "questions": [
    {
      "question_number": 1,
      "question_type": "CPT",
      "correct_answer": "D",
      "consensus_choice": "D",
      "consensus_achieved": true,
      "consensus_percentage": 85.7,
      "is_consensus_correct": true,
      "total_votes": 7,
      "vote_breakdown": {"D": 6, "A": 1}
    }
  ]
}
```

## Key Metrics

### **Consensus Accuracy**
- Percentage of consensus decisions that match the correct answer
- Only counts questions where consensus was achieved

### **Overall Accuracy** 
- Percentage of all questions where consensus was correct
- Includes questions without consensus (counted as incorrect)

### **By Question Type**
- Breakdown showing which medical coding areas have higher/lower accuracy
- Helps identify strengths and weaknesses in different domains

## Interpreting Results

### **High Consensus Accuracy (>80%)**
- Indicates the AI panel is reliable when it reaches consensus
- Suggests the consensus threshold is working well

### **Low Consensus Accuracy (<60%)**
- May indicate the consensus threshold is too low
- Could suggest systematic biases in the AI panel

### **Incorrect Consensus Patterns**
- Questions where multiple AIs confidently chose the wrong answer
- May indicate common misconceptions or ambiguous questions

### **No Consensus but Correct Leading**
- Questions where the correct answer had the most votes but didn't reach threshold
- May suggest the consensus threshold is too high for these questions

## Files Generated

- **`validation_report_YYYYMMDD_HHMMSS.json`**: Detailed validation results
- Saved in the `is_the_consensus_correct/` directory

## Dependencies

The script uses only Python standard library modules:
- `json` - For loading/saving JSON files
- `os`, `glob` - For file system operations  
- `typing` - For type hints
- `dataclasses` - For data structures
- `collections` - For defaultdict

## Integration

This tool is designed to work with:
- **Medical Board AI Testing System** (generates test results)
- **Consensus Analyzer** (generates consensus reports)
- **Question Banks** (provides questions and answer keys)

## Example Workflow

1. **Run AI Tests**: `python3 medical_test.py --all`
2. **Generate Consensus**: `python3 consensus_analyzer.py 1`
3. **Validate Consensus**: `python3 validate_consensus.py`
4. **Review Results**: Check validation report and console output
5. **Iterate**: Adjust consensus thresholds or AI panel based on results 