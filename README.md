# Syntra: AI Medical Board Consensus Analysis System

A comprehensive system for testing AI models on medical board questions and analyzing consensus patterns through multi-round voting.

## System Overview

The Syntra system consists of four main components that work together to evaluate AI performance on medical coding questions:

1. **Question Bank Management** (`00_question_banks/`)
2. **AI Medical Board Testing** (`01_medical_board/`)
3. **Consensus Analysis** (`03_consensus_benchmarks/`)
4. **Consensus Validation** (`04_consensus_validation/`)

[Click here for the Notion doc](https://www.notion.so/Medical-Coding-AI-22dedbe1674080078fc5f925cd8877fd?source=copy_link)


## Workflow

### Standard Pipeline

1. **Question Bank Creation**: Create custom question banks from source tests
   ```bash
   cd utilities/question_selector
   python3 question_selector.py --random --test1-count 50 --test2-count 50
   ```

2. **AI Medical Board Testing**: Run multiple AI models on the question bank
   ```bash
   cd 01_medical_board
   python3 medical_test.py
   ```

3. **Consensus Analysis**: Perform multi-round voting to establish consensus answers
   ```bash
   cd 03_consensus_benchmarks
   python3 consensus_analyzer.py --mode all --auto
   ```

4. **Validation**: Compare consensus results against the official answer key
   ```bash
   cd 04_consensus_validation
   python3 validate_consensus.py
   ```

### Advanced Pipeline (with PDF extraction)

1. **PDF Extraction**: Extract questions from PDF test banks using `pdf_parser.py`
2. **Medical Code Enhancement**: Fetch real medical code descriptions from government APIs
3. **Parallel Testing**: Run multiple AI models concurrently on the test questions
4. **Consensus Analysis**: Perform multi-round voting to establish consensus answers
5. **Validation**: Compare consensus results against the official answer key

## Supported AI Models

- **OpenAI**: GPT-4.1, GPT-4o, GPT-4.1-mini, GPT-4o-mini
- **Anthropic**: Claude Sonnet 3.5, Claude Sonnet 3.7, Claude Sonnet 4
- **Google**: Gemini 2.5 Pro, Gemini 2.5 Flash, Gemini 2.5 Flash Preview
- **Mistral**: Mistral Medium
- **DeepSeek**: DeepSeek v3
- **xAI**: Grok 4

## Parallelism

- **Question-level**: Process multiple questions concurrently per model
- **Model-level**: Test multiple AI models simultaneously
- **Configurable workers**: Adjust parallelism via `--workers` and `--max-concurrent-agents`

## Consensus Strategy

- **Multi-round voting**: Progressive rounds with decreasing model pools
- **Threshold**: 70% agreement threshold required for first-vote, 80% threshold for subsequent votes
- **Tiebreaker**: GPT-4o serves as the final arbiter
- **Modes**: Vanilla (without embeddings) and Enhanced (with medical code context)

## Question Types

- **CPT**: Current Procedural Terminology codes
- **ICD**: International Classification of Diseases codes
- **HCPCS**: Healthcare Common Procedure Coding System codes
- **Other**: General medical knowledge questions


## Quick Start

### Standard Pipeline (Recommended)

#### 1. Create a Question Bank

```bash
cd utilities/question_selector
python3 question_selector.py --random --test1-count 50 --test2-count 50
```

This creates `final_questions.json` and `final_answers.json` in `00_question_banks/`.

#### 2. Run Medical Board Tests

```bash
cd 01_medical_board
python3 medical_test.py
```

Tests all configured AI models on the question bank.

#### 3. Analyze Consensus

```bash
cd 03_consensus_benchmarks
python3 consensus_analyzer.py --mode all --auto
```

Runs multi-round consensus analysis with automatic progression.

#### 4. Validate Results

```bash
cd 04_consensus_validation
python3 validate_consensus.py
```

Validates consensus decisions against the official answer key.

### Advanced Pipeline (with PDF extraction)

#### 1. Extract Questions from PDF

```bash
# Basic extraction
python utilities/pdf_to_json/pdf_parser.py test_1.pdf

# With debugging output
python utilities/pdf_to_json/pdf_parser.py test_1.pdf --debug

# Skip AI cleanup (regex-only extraction)
python utilities/pdf_to_json/pdf_parser.py test_1.pdf --no-ai

# List available PDFs
python utilities/pdf_to_json/pdf_parser.py --list
```

#### 2. Process Medical Codes

```bash
python 00_hcpcs_icd_apis/fetch_embeddings.py
```

#### 3. Run Medical Board Tests

```bash
# List available AI models
python 01_medical_board/medical_test.py --list-doctors

# Test specific model
python 01_medical_board/medical_test.py --doctor gpt_4o

# Test with embeddings enabled
python 01_medical_board/medical_test.py --embeddings --doctor claude_sonnet_3_5

# Test all models (vanilla and enhanced)
python 01_medical_board/medical_test.py --all

# Limit questions for quick testing
python 01_medical_board/medical_test.py --doctor gemini_2_5_pro --max-questions 10

# Custom parallelism settings
python 01_medical_board/medical_test.py --sequential --workers 1
python 01_medical_board/medical_test.py --max-concurrent-agents 2 --embeddings
```

#### 4. Run Consensus Analysis

```bash
# List available test folders
python 03_consensus_benchmarks/consensus_analyzer.py --list

# Run all modes (vanilla and enhanced)
python 03_consensus_benchmarks/consensus_analyzer.py --mode all --auto

# Run specific mode
python 03_consensus_benchmarks/consensus_analyzer.py --mode vanilla --auto
python 03_consensus_benchmarks/consensus_analyzer.py --mode enhanced --auto

# Start from specific test folder
python 03_consensus_benchmarks/consensus_analyzer.py --mode enhanced --test test_20250710_195405 --auto
```

#### 5. Run Consensus Validation

```bash
# Validate default final consensus report
python 04_consensus_validation/validate_consensus.py

# List available consensus reports
python 04_consensus_validation/validate_consensus.py --list

# Validate specific report
python 04_consensus_validation/validate_consensus.py --report consensus_report_20250710_121105.json
```

## System Architecture

### Data Flow

```
00_question_banks/
├── test_1/                    # Source test bank 1
├── test_2/                    # Source test bank 2
├── final_questions.json       # Active question bank
└── final_answers.json         # Corresponding answers

        ↓

01_medical_board/
├── medical_test.py           # AI testing engine
└── config.py                 # AI model configuration

        ↓

02_test_attempts/
└── test_YYYYMMDD_HHMMSS/     # Test result storage

        ↓

03_consensus_benchmarks/
├── consensus_analyzer.py     # Multi-round consensus analysis
└── consensus_reports/        # Consensus analysis results

        ↓

04_consensus_validation/
├── validate_consensus.py     # Validation against answer key
└── validation_report_*.json  # Validation results
```

### Directory Structure

```
syntra/
├── README.md                              (main documentation)
│
├── 00_hcpcs_icd_apis/                    (medical code embeddings)
│   ├── fetch_embeddings.py               (fetches medical codes from government APIs)
│   ├── question_embeddings.json          (generated embeddings cache)
│   └── requirements.txt
│
├── 00_question_banks/                    (test bank storage)
│   ├── test_1/
│   │   ├── test_1.pdf                    (original PDF test)
│   │   ├── test_1_questions.json         (extracted questions)
│   │   ├── test_1_answers.json           (answer key)
│   │   └── test_1_with_answers.pdf       (reference PDF with answers)
│   ├── test_2/
│   │   ├── test_2_questions.json         (extracted questions)
│   │   ├── test_2_answers.json           (answer key)
│   │   └── test_2_with_answers.pdf       (reference PDF with answers)
│   ├── final_questions.json              (active question bank)
│   └── final_answers.json                (active answer bank)
│
├── 01_medical_board/                     (core testing system)
│   ├── medical_test.py                   (main test runner)
│   ├── ai_client.py                      (LLM interface)
│   ├── config.py                         (system configuration)
│   ├── test_setup.py                     (setup verification)
│   └── requirements.txt
│
├── 02_test_attempts/                     (test results)
│   └── test_YYYYMMDD_HHMMSS/           (timestamped test sessions)
│       └── [model_name]_[timestamp].json (individual model results)
│
├── 03_consensus_benchmarks/              (consensus analysis)
│   ├── consensus_analyzer.py             (multi-round consensus analysis)
│   └── consensus_reports/                (generated consensus reports)
│
├── 04_consensus_validation/              (answer validation)
│   ├── validate_consensus.py             (validates against answer key)
│   └── validation_report_*.json          (validation results)
│
└── utilities/
    ├── pdf_to_json/                      (PDF extraction)
    │   └── pdf_parser.py                 (extracts questions from PDFs)
    ├── question_selector/                (question bank management)
    │   ├── question_selector.py          (bank creation tool)
    │   └── README.md                     (tool documentation)
    └── question_type_classifier/         (question classification)
        └── question_classifier.py        (classifies by CPT/ICD/HCPCS)
```

## Regarding Tool Call Usage on a Multiple Choice Test

  The system uses tool calls to select A/B/C/D choices. Here's how it
  works:

  1. Primary Method - Tool Calls (lines 59-84): The system defines a
  function tool called select_answer that forces the AI to respond with:
    - choice: Must be one of ["A", "B", "C", "D"]
    - reasoning: Explanation for the choice
  2. Fallback Parsing (lines 114-131): If tool calls fail, it has multiple
   fallback parsers:
    - _parse_reasoning_details(): For Gemini models that put responses in
  reasoning_details
    - _parse_response(): Pattern matching for various text formats
    - _parse_json_response(): For models that return JSON instead of tool
  calls
  3. Text Pattern Matching (lines 169-229): The _parse_response() method
  looks for:
    - A:, B., C) at the start
    - "Answer: A" patterns
    - "The answer is B" patterns
    - "I choose C" patterns
    - Standalone letters followed by explanations

## Results


<details>
<summary>Click to expand</summary>

#### 🎯 Consensus Validation Summary

| Metric                | Value                        |
|-----------------------|-----------------------------|
| **Total Questions**   | 100                         |
| **Consensus Achieved**| 100/100 (**100.0%**)        |
| **Consensus Correct** | 74/100 (**74.0% of consensus**) |

---

#### 📋 Accuracy by Question Type

| Type   | Total | Consensus | Correct | Accuracy   |
|--------|-------|-----------|---------|------------|
| CPT    | 65    | 65        | 44      | 67.7%      |
| HCPCS  | 7     | 7         | 5       | 71.4%      |
| ICD    | 13    | 13        | 10      | 76.9%      |
| other  | 15    | 15        | 15      | 100.0%     |

---

#### ❌ Incorrect Consensus Decisions (26)

<details>
<summary>Click to expand</summary>

| Question | Consensus (Pct) | Correct | Votes |
|----------|-----------------|---------|-------|
| Q1       | B (66.7%)       | C       |       |
| Q7       | D (66.7%)       | A       |       |
| Q11      | A (91.7%)       | C       |       |
| Q12      | A (75.0%)       | B       |       |
| Q17      | B (100.0%)      | A       |       |
| Q20      | A (91.7%)       | B       |       |
| Q23      | D (100.0%)      | B       |       |
| Q24      | A (66.7%)       | D       |       |
| Q30      | B (100.0%)      | C       |       |
| Q33      | A (66.7%)       | D       |       |
<!-- ... (remaining omitted for brevity, but keep all in actual file) -->
</details>

---

#### 📊 Individual Model Success/Failure Breakdown

✅ Loaded answer key with 100 questions

| Model Name                         | Correct | Incorrect | Total | Accuracy   |
|-------------------------------------|---------|-----------|-------|------------|
| Dr. GPT 4.1                        | 75      | 25        | 100   | 75.0%      |
| Dr. Claude Sonnet the 3.5th         | 74      | 26        | 100   | 74.0%      |
| Dr. Gemini Pro the 2.5th            | 73      | 27        | 100   | 73.0%      |
| Dr. GPT 4o                          | 71      | 29        | 100   | 71.0%      |
| Dr. Claude Sonnet the 3.7th         | 71      | 29        | 100   | 71.0%      |
| Dr. Claude Sonnet the 4th           | 68      | 32        | 100   | 68.0%      |
| Dr. DeepSeek V3                     | 67      | 33        | 100   | 67.0%      |
| Dr. Gemini Flash Preview the 2.5th  | 66      | 34        | 100   | 66.0%      |
| Dr. Gemini Flash the 2.5th          | 65      | 35        | 100   | 65.0%      |
| Dr. Mistral Medium                  | 63      | 37        | 100   | 63.0%      |
| Dr. GPT 4o Mini                     | 62      | 38        | 100   | 62.0%      |
| Dr. GPT 4.1 Mini                    | 62      | 38        | 100   | 62.0%      |

**Summary Statistics:**
- **Total Active Models:** 12
- **Average Accuracy:** 68.1%

---

#### 🔄 Self-Correction Analysis (Multi-Round Questions)

| Model Name                         | Improved | Worsened | Stayed Right | Stayed Wrong |
|-------------------------------------|----------|----------|--------------|-------------|
| Dr. Gemini Flash the 2.5th          | 13       | 4        | 4            | 15          |
| Dr. Gemini Flash Preview the 2.5th  | 13       | 4        | 4            | 15          |
| Dr. GPT 4.1 Mini                    | 11       | 5        | 6            | 14          |
| Dr. GPT 4o Mini                     | 9        | 4        | 8            | 15          |
| Dr. DeepSeek V3                     | 7        | 6        | 9            | 14          |
| Dr. Claude Sonnet the 4th           | 6        | 4        | 10           | 16          |
| Dr. GPT 4o                          | 4        | 1        | 13           | 18          |
| Dr. Mistral Medium                  | 4        | 0        | 10           | 22          |
| Dr. Gemini Pro the 2.5th            | 3        | 4        | 12           | 17          |
| Dr. Claude Sonnet the 3.7th         | 3        | 0        | 12           | 21          |
| Dr. GPT 4.1                         | 2        | 5        | 12           | 17          |
| Dr. Claude Sonnet the 3.5th         | 2        | 4        | 12           | 18          |

**Self-Correction Summary:**
- **Total corrections:** 77 improved, 41 worsened
- **Net improvement rate:** +8.3%

Notes: Key insight: GPT-4.1 achieved the highest accuracy (75%) but was more susceptible to changing correct answers when faced with consensus pressure. Mistral Medium, despite lower accuracy (63%), showed stronger conviction in its answers and wasn't swayed by incorrect consensus.
</details>

## Which AI would I choose for health data?

```python3
python3 consensus_independence_analysis.py
```

Out of 100 consensus decisions, 26 were incorrect (74% accuracy). The study reveals concerning patterns of groupthink while identifying models with superior independent reasoning capabilities.

1. **Dr. Gemini Pro the 2.5th** 
    - Independence: 15.4% (4/26 correct when consensus wrong)
    - Individual Accuracy: 73.0%
    - Resisted wrong consensus on questions: 1, 70, 75, 81
2. **Dr. Claude Sonnet the 3.7th**
    - Independence: 15.4% (4/26 correct when consensus wrong)
    - Individual Accuracy: 71.0%
    - Resisted wrong consensus on questions: 34, 47, 70, 75
3. **Dr. Mistral Medium**
    - Independence: 19.2% (5/26 correct when consensus wrong) - **HIGHEST INDEPENDENCE**
    - Individual Accuracy: 63.0%
    - Resisted wrong consensus on questions: 1, 12, 33, 38, 81

Widespread Groupthink Problem

- **15 out of 26 wrong consensus questions** had NO models vote correctly in the final round
- Questions with 100% groupthink: 7, 11, 17, 20, 23, 24, 30, 41, 46, 57, 59, 64, 65, 91, 97
- This represents 57% of wrong decisions where ALL models were swayed by group pressure

### Current limitations, future improvements:

- Unbalanced categories: 65% CPT vs 13% ICD vs 7% HCPCS skews results.
- CPT codes do not have a free, public API as they are copyrighted by the AMA. Including APIs for them would substantially boast the scores.
- Small sample size: 100 questions isn't sufficient for definitive model ranking
- Single domain focus: Only medical coding, not broader medical knowledge
- No difficulty stratification: Easy and complex questions weighted equally