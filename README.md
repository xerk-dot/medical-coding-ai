# Medical Coding AI

A multi-AI consensus system for determining proper medical codes from test questions.

## Project Structure

```
syntra/
├── question_banks/          # PDF test files and extracted questions
├── medical_board/           # AI doctor testing system
├── medical_board_judgements/ # Test results from AI doctors
├── solvers/                 # AI consensus solving logic
├── solving_attempts/        # Results from solving sessions
└── utilities/
    ├── pdf_to_json/        # PDF extraction tools
    └── question_type_classifier/  # Question classification tools
```

## Quick Start

### Steps to run locally:

1. Place PDF into the `question_banks` folder
2. Run `pdf_to_json` to get the questions into JSON format
3. Run `question_type_classifier` to get the questions classified
4. Run the medical board test to have AI doctors take the exam

### Running the Medical Board Test

```bash
cd medical_board

# Install dependencies
pip install -r requirements.txt

# Set up OpenRouter API key
cp .env.example .env
# Edit .env with your OpenRouter API key

# Test all AI doctors
python medical_test.py --all

# Or test a specific doctor
python medical_test.py claude_sonnet_4
```

## System Overview

### Round 1: Default Multi-AI Consensus

Each doctor (AI model) has to determine the proper medical code:

#### The Medical AI Panel
- **Dr. claude-sonnet-4-20250514**
- **Dr. gemini-2.5-flash** 
- **Dr. gemini-2.5-pro**
- **Dr. deepseek-v3-0324**
- **Dr. grok-3-preview-02-24**
- **Dr. gpt-4.1-2025-04-14**
- **Dr. 4o**
- **Dr. o3-2025-04-16**
- **Dr. mistral-medium-2505**
- **Dr. o1**

### Consensus Thresholds

- **First vote**: Requires 70% agreement
- **Second/subsequent votes**: Raises to 85% agreement

If the first vote fails, the AIs receive the votes and justifications from other AIs before the second round.

### Tool Use
AIs can use tools to determine A/B/C/D answer choices.

## Pipeline Roadmap

### Round 2: Default (w/ vector database)
Enhanced consensus with vector database support.

### Round 3: No 'doctors' (no AI), purely vectors
Vector-only approach for comparison.

### Other Strategies:
- **Question Generation**: Use AI to generate four potential questions given the answer choices, then compare questions via vectors
- **Answer Generation**: Use AI to generate four potential answers, then have another layer where AIs/vectors determine the closest answer choice
- **Specialized Medical AI Feedback**: When first vote fails, rely on feedback from:
  - Dr. SapBERT
  - Dr. BioGPT
  - Dr. BioMedLM
  - Dr. UmlsBERT
  - Dr. ClinicalBERT

