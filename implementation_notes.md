# Medical Coding AI

A multi-AI consensus system for determining proper medical codes from test questions.

## Project Structure

```
syntra/
├── 00_question_banks/          # PDF test files and extracted questions
├── solvers/                 # AI consensus solving logic
├── solving_attempts/        # Results from solving sessions
└── utilities/
    ├── pdf_to_json/        # PDF extraction tools
    └── question_type_classifier/  # Question classification tools
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


In the medical board folder, there is a script that you can run to have all the AIs take the test. this python script will use open router to have each AI take the test. The AI will be asked one question at a time. tool use for ABCD. the questions are from test_1_questions.json

Each test submission is saved as a json in the 02_test_attempts as a json featuring the AI's answers, the model, the time the test was completed. the file will be named the name of the model (short form)_date-finished

