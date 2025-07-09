# Medical Board AI Testing System

This system administers medical coding tests to a panel of AI "doctors" and collects their responses for consensus analysis.

## Overview

The Medical Board system simulates a standardized medical coding examination where each AI model acts as a doctor taking the test. Each AI is asked questions one at a time using OpenRouter API, and their responses are collected and saved for analysis.

## Setup

### 1. Install Dependencies
```bash
cd medical_board
pip install -r requirements.txt
```

### 2. Configure OpenRouter API
Create a `.env` file in this directory:
```bash
cp .env.example .env
# Edit .env and add your OpenRouter API key
```

### 3. Ensure Test Questions Available
Make sure the questions file exists at `question_banks/test_1/test_1_questions.json`. If not, run the PDF extraction tool first:
```bash
cd ../utilities/pdf_to_json
python pdf_parser.py test_1.pdf
```

## Usage

### Test All AI Doctors
```bash
python medical_test.py --all
```

### Test a Specific AI Doctor
```bash
python medical_test.py claude_sonnet_4
```

### List Available AI Doctors
```bash
python medical_test.py --list
```

### Test Setup Verification
```bash
python test_setup.py
```

### Analyze Consensus Results
```bash
# After all doctors have completed their tests
python consensus_analyzer.py 1    # First round (70% threshold)
python consensus_analyzer.py 2    # Second round (85% threshold)
```

## AI Doctor Panel

The current medical AI panel includes:

- **Dr. claude-sonnet-4-20250514** (`claude_sonnet_4`)
- **Dr. gemini-2.5-flash** (`gemini_2_5_flash`)
- **Dr. gemini-2.5-pro** (`gemini_2_5_pro`)
- **Dr. deepseek-v3-0324** (`deepseek_v3`)
- **Dr. grok-3-preview-02-24** (`grok_3`)
- **Dr. gpt-4.1-2025-04-14** (`gpt_4_1`)
- **Dr. 4o** (`gpt_4o`)
- **Dr. o3-2025-04-16** (`o3`)
- **Dr. mistral-medium-2505** (`mistral_medium`)
- **Dr. o1** (`o1`)

## How It Works

### Question Administration
1. **Load Questions**: System loads questions from the JSON file
2. **Select System Prompt**: Based on question type (CPT, ICD, HCPCS, other)
3. **Ask Question**: Each AI gets the question with A/B/C/D choices
4. **Tool Use**: AIs use the `select_answer` function to choose their response
5. **Rate Limiting**: Delays between questions to respect API limits

### Response Collection
- **Selected Answer**: A, B, C, or D choice
- **Reasoning**: AI's explanation for their choice
- **Raw Response**: Complete API response for debugging
- **Success Status**: Whether the AI provided a valid response

### Results Storage
Test results are saved to `../medical_board_judgements/` as JSON files:
- **Filename Format**: `{doctor_short_name}_{timestamp}.json`
- **Content**: Complete test session with all questions and responses

## Question Types & System Prompts

The system uses specialized prompts based on question type:

- **CPT**: Current Procedural Terminology coding expertise
- **ICD**: ICD-10-CM diagnosis coding expertise  
- **HCPCS**: Healthcare Common Procedure Coding System expertise
- **other**: General medical knowledge

## Output Format

Each test session generates a JSON file with:

```json
{
  "doctor_name": "Dr. claude-sonnet-4-20250514",
  "model_id": "anthropic/claude-3.5-sonnet", 
  "start_time": "2025-01-16T10:30:00",
  "end_time": "2025-01-16T11:45:00",
  "total_questions": 100,
  "successful_answers": 87,
  "results": [
    {
      "question_number": 1,
      "question": "Which CPT code covers...",
      "question_type": "CPT",
      "choices": {"A": "40800", "B": "41105", "C": "41113", "D": "40804"},
      "selected_answer": "A",
      "reasoning": "Code 40800 specifically covers...",
      "raw_response": "...",
      "success": true
    }
  ]
}
```

## Configuration

### Adding New AI Models
Edit `config.py` to add new models to the `AI_DOCTORS` dictionary:

```python
"new_model": {
    "model_id": "provider/model-name",
    "display_name": "Dr. New Model",
    "short_name": "new_model"
}
```

### Adjusting Rate Limits
Modify these values in `config.py`:
- `RATE_LIMIT_DELAY`: Seconds between questions
- `MAX_RETRIES`: Number of retry attempts
- `REQUEST_TIMEOUT`: API request timeout

## Error Handling

The system handles various error conditions:
- **API Failures**: Retries with exponential backoff
- **Invalid Responses**: Fallback parsing for non-tool responses  
- **Network Issues**: Graceful degradation and error logging
- **Rate Limiting**: Automatic delays between requests

## Next Steps

After collecting test results from all AI doctors:

1. **Consensus Analysis**: Compare answers across models
2. **Performance Metrics**: Calculate accuracy by question type
3. **Voting Implementation**: Implement 70%/85% consensus thresholds
4. **Specialized Feedback**: Add medical AI experts for difficult cases 