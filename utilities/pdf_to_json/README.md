# PDF to JSON Parser

A systematic 4-step approach to extract questions and answers from PDF test files into clean JSON format.

## Quick Start

```bash
cd utilities/pdf_to_json

# Process a file from the default test_1 directory
python pdf_parser.py test_1.pdf

# Process a file from any location
python pdf_parser.py /path/to/your/pdf/file.pdf

# Process a file from test_2 directory
python pdf_parser.py test_2/test_2_with_answers.pdf
```

## How It Works

1. **Extract ALL text** from PDF (no preprocessing that loses content)
2. **Create 100 question blocks** using sequential boundary detection
3. **Separate questions from A/B/C/D choices** handling both `?` and `:` terminators
4. **AI cleanup** with parallel processing for perfect formatting

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. OpenAI API Key (Required for AI cleanup)
Create `.env` file in this directory:
```
OPENAI_API_KEY=your_api_key_here
```

## Commands

```bash
# Full processing with AI cleanup
python pdf_parser.py test_1.pdf

# Process file from specific path
python pdf_parser.py /path/to/test_2/test_2_with_answers.pdf

# Skip AI cleanup (faster, but text won't be formatted)
python pdf_parser.py test_1.pdf --no-ai

# Save raw extracted text for debugging
python pdf_parser.py test_1.pdf --debug

# List available PDF files in default directory
python pdf_parser.py --list

# List available PDF files in specific directory
python pdf_parser.py --list /path/to/test_2
```

## What This Produces

**Perfect JSON output** with all 100 questions:

```json
{
  "question_number": 1,
  "question": "During a regular checkup, Dr. Stevens discovered a suspicious lesion on the floor of Paul's mouth and decided to perform an excision. Which CPT code covers the excision of an oral lesion?",
  "choices": {
    "A": "40800",
    "B": "41105", 
    "C": "41113",
    "D": "40804"
  }
}
```

## Key Features

- ✅ **Finds all 100 questions** using sequential boundary detection
- ✅ **Handles both question marks and colons** as question terminators
- ✅ **Cleans up "Medical Coding Ace" text** automatically
- ✅ **Parallel AI processing** for 4x faster text cleanup
- ✅ **Perfect choice extraction** for A/B/C/D options

## Output

Results are saved in the same directory as the input PDF file:
- Questions: `[basename]_questions.json`
- Answers (if `_with_answers.pdf` file exists): `[basename]_answers.json`

For example:
- Input: `/path/to/test_2/test_2.pdf`
- Output: `/path/to/test_2/test_2_questions.json`

The parser successfully extracts all 100 questions with properly formatted text and complete A/B/C/D choices. 