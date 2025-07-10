# Enhanced Consensus Validation Tool

This tool validates the accuracy of AI consensus decisions against the official answer key and provides detailed individual model performance statistics.

## Overview

The enhanced consensus validation script compares the latest consensus report from the Medical Board AI Testing System with the official answer key to determine:

- How often the AI consensus matches the correct answer
- Individual AI model performance rankings
- Which models perform best on different question types
- Detailed breakdown of incorrect consensus decisions
- Questions where the correct answer led voting but didn't achieve consensus

## Usage

### Basic Validation with Model Performance
```bash
cd consensus_validation
python3 validate_consensus.py
```

## What It Does

### 1. **Data Loading**
- Loads the official answer key from `question_banks/test_1/test_1_answers.json`
- Loads individual test results from all AI models in `test_attempts/`
- Finds the latest consensus report from `consensus_benchmarks/consensus_reports/`
- Loads question types from `question_banks/test_1/test_1_questions.json`

### 2. **Individual Model Analysis**
- Calculates accuracy for each AI model against the answer key
- Ranks models by overall performance
- Analyzes performance by question type (CPT, ICD, HCPCS, other)
- Identifies top and bottom performers

### 3. **Consensus Validation**
- Compares each consensus decision with the correct answer
- Calculates accuracy metrics overall and by question type
- Identifies patterns in incorrect consensus decisions

### 4. **Output**
- **Console Summary**: Individual model performance + consensus validation results
- **JSON Report**: Detailed validation report with model performance data

## Current Results (With Corrected Answer Key)

### **🤖 Individual Model Performance**
```
Model Name                          Total  Correct  Accuracy  
----------------------------------------------------------------------
Dr. o1                              57     54       94.7      %
Dr. GPT 4.1                         100    73       73.0      %
Dr. Grok 3 Beta                     36     26       72.2      %
Dr. GPT 4o                          100    72       72.0      %
Dr. Claude Sonnet the 4th           100    71       71.0      %
Dr. Gemini Flash the 2.5th          100    65       65.0      %
Dr. DeepSeek V3                     100    64       64.0      %
Dr. Mistral Medium                  100    63       63.0      %
Dr. Gemini Pro the 2.5th            96     45       46.9      %
Dr. o3                              0      0        0.0       %
Dr. Grok 3 Preview                  0      0        0.0       %
```

### **🎯 Consensus Validation Summary**
```
Total Questions: 100
Consensus Achieved: 54/100 (54.0%)
Consensus Correct: 48/54 (88.9% of consensus)
Overall Accuracy: 48/100 (48.0% of all questions)
```

## Key Insights

### **🏆 Top Performers**
1. **Dr. o1** (94.7%) - Highest accuracy but only answered 57 questions
2. **Dr. GPT 4.1** (73.0%) - Strong performance across all 100 questions
3. **Dr. Grok 3 Beta** (72.2%) - Good accuracy but limited responses (36 questions)

### **📊 Performance Patterns**
- **High Accuracy, Low Volume**: o1 has excellent accuracy but low response rate
- **Balanced Performance**: GPT-4.1, GPT-4o, Claude Sonnet show consistent 70%+ accuracy
- **Mid-Tier Models**: Gemini Flash, DeepSeek V3, Mistral Medium around 63-65%
- **Struggling Models**: Gemini Pro (46.9%), o3 and Grok 3 Preview (0% due to technical issues)

### **🎯 Consensus Quality**
- **High Consensus Accuracy**: 88.9% of consensus decisions are correct
- **Consensus Threshold**: Current 70% threshold appears well-calibrated
- **Missed Opportunities**: 24 questions where correct answer led but didn't reach consensus

## Output Format

### Console Output
```
🤖 INDIVIDUAL MODEL PERFORMANCE
======================================================================
Model Name                          Total  Correct  Accuracy  
----------------------------------------------------------------------
Dr. o1                              57     54       94.7      %
Dr. GPT 4.1                         100    73       73.0      %
[... more models ...]

🏆 Best Performer: Dr. o1 (94.7%)
🔻 Worst Performer: Dr. Grok 3 Preview (0.0%)

📊 Top 3 Models - Accuracy by Question Type:
Model                     CPT      ICD      HCPCS    Other   
------------------------------------------------------------
Dr. o1                    0.0%     0.0%     0.0%     94.7%   
Dr. GPT 4.1               0.0%     0.0%     0.0%     73.0%   
Dr. Grok 3 Beta           0.0%     0.0%     0.0%     72.2%   

🎯 CONSENSUS VALIDATION SUMMARY
============================================================
Total Questions: 100
Consensus Achieved: 54/100 (54.0%)
Consensus Correct: 48/54 (88.9% of consensus)
Overall Accuracy: 48/100 (48.0% of all questions)

❌ Incorrect Consensus Decisions (6):
  Q11: Consensus=A (87.5%), Correct=C
    Votes: A:7 , D:1 
  Q37: Consensus=A (100.0%), Correct=C
    Votes: A:8 
  [... more incorrect decisions ...]
```

### JSON Report
```json
{
  "timestamp": "2025-07-09T18:54:02",
  "summary": {
    "total_questions": 100,
    "consensus_achieved": 54,
    "consensus_correct": 48,
    "consensus_accuracy": 88.9,
    "overall_accuracy": 48.0
  },
  "model_performances": [
    {
      "model_name": "Dr. o1",
      "total_questions": 57,
      "correct_answers": 54,
      "accuracy_percentage": 94.7,
      "accuracy_by_type": {
        "other": 94.7
      }
    }
  ],
  "questions": [...]
}
```

## Key Metrics

### **Individual Model Accuracy**
- Percentage of questions each model answered correctly
- Ranked from highest to lowest accuracy
- Breakdown by question type when available

### **Consensus Accuracy**
- Percentage of consensus decisions that match the correct answer
- Only counts questions where consensus was achieved

### **Overall Accuracy** 
- Percentage of all questions where consensus was correct
- Includes questions without consensus (counted as incorrect)

## Interpreting Results

### **High Individual Accuracy (>70%)**
- Models like o1, GPT-4.1, GPT-4o, Claude Sonnet show strong medical coding knowledge
- These models are reliable contributors to consensus decisions

### **High Consensus Accuracy (88.9%)**
- Indicates the AI panel is very reliable when it reaches consensus
- Suggests the 70% consensus threshold is well-calibrated

### **Response Rate vs. Accuracy Trade-off**
- o1 has highest accuracy (94.7%) but lowest response rate (57/100)
- GPT-4.1 balances high accuracy (73%) with full response rate (100/100)

### **Technical Issues**
- o3 and Grok 3 Preview show 0% due to API/parsing issues
- Grok 3 Beta limited to 36 responses due to rate limiting

## Files Generated

- **`validation_report_YYYYMMDD_HHMMSS.json`**: Detailed validation results with model performance
- Saved in the current directory

## Fixed Answer Key

The answer extraction has been corrected to properly parse the PDF answer key:
- **Previous Issue**: Incorrect regex pattern was picking up random numbers
- **Fixed Pattern**: Now correctly extracts "Answer: C." format from the PDF
- **Result**: All 100 answers correctly extracted and validated

## Dependencies

The script uses only Python standard library modules:
- `json` - For loading/saving JSON files
- `os`, `glob` - For file system operations  
- `typing` - For type hints
- `dataclasses` - For data structures
- `collections` - For defaultdict and Counter

## Integration

This tool is designed to work with:
- **Medical Board AI Testing System** (generates test results)
- **Consensus Analyzer** (generates consensus reports)
- **Question Banks** (provides questions and answer keys)
- **PDF Parser** (extracts correct answers from PDF)

## Example Workflow

1. **Fix Answer Key**: `cd utilities/pdf_to_json && python3 pdf_parser.py test_1.pdf`
2. **Run AI Tests**: `cd medical_board && python3 medical_test.py --all`
3. **Generate Consensus**: `python3 consensus_analyzer.py 1`
4. **Validate with Model Performance**: `cd ../consensus_validation && python3 validate_consensus.py`
5. **Review Results**: Check individual model rankings and consensus accuracy
6. **Iterate**: Adjust AI panel or consensus thresholds based on performance data

