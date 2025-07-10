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

Results are stored in:
- **Test Attempts**: `../test_attempts/` (individual AI responses)
- **Consensus Reports**: `../consensus_benchmarks/consensus_reports/` (consensus analysis)

## AI Doctor Panel

The current medical AI panel includes:

- **Dr. claude-sonnet-4-20250514** (`claude_sonnet_4`)
- **Dr. gemini-2.5-flash** (`gemini_2_5_flash`)
- **Dr. gemini-2.5-pro** (`gemini_2_5_pro`)
- **Dr. deepseek-v3-0324** (`deepseek_v3`)
- **Dr. grok-3-preview-02-24** (`grok_3`)
- **Dr. gpt-4.1-2025-04-14** (`gpt_4_1`)
- **Dr. 4o** (`gpt_4o`)
- **Dr. o3** (`o3`)
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
- **Tool-Based Selection**: AIs use `select_answer` function for A/B/C/D choices
- **Enhanced Parsing**: Fallback parsing for models that return JSON in content
- **Error Handling**: Comprehensive retry logic with exponential backoff
- **Validation**: Ensures only valid A/B/C/D choices are accepted

### Results Storage
Test results are saved to `../test_attempts/` as JSON files:
- **Filename Format**: `{doctor_short_name}_{timestamp}.json`
- **Content**: Complete test session with all questions, responses, and metadata

## Question Types & System Prompts

The system uses specialized prompts based on question type:

- **CPT**: Current Procedural Terminology coding expertise
- **ICD**: ICD-10-CM diagnosis coding expertise  
- **HCPCS**: Healthcare Common Procedure Coding System expertise
- **other**: General medical knowledge

## Performance Optimizations

### Recent Improvements (2025)
- **Parallel Processing**: 10 concurrent workers process all questions simultaneously
- **Cost Optimization**: Models run in ascending cost order
- **Enhanced Parsing**: Handles multiple response formats (tool calls, JSON, text)
- **Improved Error Handling**: Better fallback mechanisms for different AI behaviors
- **Real-time Progress**: Live completion tracking with question numbers

### Configuration
- **Parallel Workers**: 10 concurrent question processors
- **Rate Limiting**: 0.5 second delays between requests
- **Retry Logic**: 3 attempts with exponential backoff
- **Timeout**: 60 seconds per request

## Output Format

Each test session generates a JSON file with:

```json
{
  "doctor_name": "Dr. Gemini Flash the 2.5th",
  "model_id": "google/gemini-2.5-flash", 
  "start_time": "2025-07-09T17:56:00",
  "end_time": "2025-07-09T17:57:00",
  "total_questions": 100,
  "completed_answers": 100,
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

## Recent Test Results

Latest performance results show:
- **Perfect Performers**: Gemini Flash, Mistral Medium, GPT-4.1, GPT-4o, Claude Sonnet (100%)
- **Good Performers**: DeepSeek V3 (77%), o1 (57%)
- **Improved Models**: o3 and Grok 3 (fixed model IDs and parsing)

## Configuration

### Adding New AI Models
Edit `config.py` to add new models to the `AI_DOCTORS` dictionary:

```python
"new_model": {
    "model_id": "provider/model-name",
    "display_name": "Dr. New Model",
    "short_name": "new_model",
    "cost_tier": 3,
    "cost_note": "$X.XX/$Y.YY per M tokens"
}
```

### Adjusting Performance Settings
Modify these values in `config.py`:
- `RATE_LIMIT_DELAY`: Seconds between requests (default: 0.5)
- `MAX_RETRIES`: Number of retry attempts (default: 3)
- `REQUEST_TIMEOUT`: API request timeout (default: 60)
- `PARALLEL_WORKERS`: Concurrent question processors (default: 10)

## Error Handling

The system handles various error conditions:
- **API Failures**: Retries with exponential backoff
- **Invalid Responses**: Multiple parsing strategies (tool calls, JSON, text)
- **Network Issues**: Graceful degradation and error logging
- **Rate Limiting**: Automatic delays between requests
- **Model Variations**: Adaptive parsing for different AI response formats

## Special Requirements

### BYOK (Bring Your Own Key) Models
Some models require special setup:
- **o3**: Requires BYOK configuration at OpenRouter
- **o3-pro**: Requires BYOK configuration

### Model Availability
- Model IDs are current as of Summer 2025
- Some models may have limited availability or require special access
- Check OpenRouter documentation for the latest model availability

## Consensus Analysis

After collecting test results from all AI doctors:

1. **Consensus Analysis**: Compare answers across models using voting thresholds
2. **Performance Metrics**: Calculate accuracy by question type and model
3. **Voting Implementation**: 70% threshold for first round, 85% for subsequent rounds
4. **Detailed Reports**: Generate comprehensive analysis of model performance

## Next Steps

After running tests:
1. **Run Consensus Analysis**: `python consensus_analyzer.py 1`
2. **Review Results**: 
   - Individual responses: `../test_attempts/`
   - Consensus reports: `../consensus_benchmarks/consensus_reports/`
3. **Analyze Performance**: Compare model completion rates across question types
4. **Cost Analysis**: Review cost efficiency of different models

## Troubleshooting

### Common Issues
- **API Key**: Ensure `OPENROUTER_API_KEY` is set in `.env`
- **Questions File**: Run PDF extraction if questions JSON is missing
- **Model Errors**: Check OpenRouter for model availability and requirements
- **Rate Limits**: Adjust `RATE_LIMIT_DELAY` if encountering rate limiting

### Getting Help
- Run `python test_setup.py` to verify configuration
- Check error messages in console output
- Review raw responses in result JSON files for debugging 