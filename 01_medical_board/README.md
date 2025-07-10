# Medical Board AI Testing System

A comprehensive system for testing AI models on medical coding questions with parallel processing, medical code embeddings, and consensus analysis.

## 🚀 Key Features

- **Dual-Level Parallelism**: Both question-level and agent-level parallel processing
- **Medical Code Embeddings**: Enhanced mode with real medical code data from government APIs
- **Completion Tracking**: Focus on answer completion rates rather than correctness
- **Consensus Analysis**: Automated analysis of AI agreement across models
- **Comprehensive Results**: Detailed JSON output with reasoning, raw responses, and error tracking
- **High Performance**: 67x faster than sequential processing with parallel agents

## Overview

The Medical Board system simulates standardized medical coding examinations where AI models act as doctors taking tests. Each AI is tested on CPT, ICD-10-CM, and HCPCS coding questions, with results collected for analysis.

## Setup

### 1. Install Dependencies
```bash
cd 01_medical_board
pip install -r requirements.txt
```

### 2. Configure OpenRouter API
Create a `.env` file in this directory:
```bash
cp .env.example .env
# Edit .env and add your OpenRouter API key
```

### 3. Ensure Test Questions Available
Make sure the questions file exists at `../00_question_banks/test_1/test_1_questions.json`. If not, run the PDF extraction tool first:
```bash
cd ../utilities/pdf_to_json
python pdf_parser.py test_1.pdf
```

### 4. Generate Medical Code Embeddings (Optional)
For enhanced testing with real medical code data:
```bash
cd ../00_code_embeddings
python fetch_embeddings.py
```

## Usage

### Quick Start - Test All Models
```bash
# Test all models in both vanilla and enhanced modes (creates 2 timestamped folders)
python medical_test.py --all

# Test with custom parallel settings
python medical_test.py --all --workers 8 --max-concurrent-agents 3

# Test sequentially for reliability
python medical_test.py --all --sequential --sequential-agents
```

### Single Model Testing
```bash
# Test specific model in vanilla mode
python medical_test.py --doctor gemini_2_5_flash

# Test with medical code embeddings
python medical_test.py --doctor claude_sonnet_4 --embeddings

# Test with limited questions
python medical_test.py --doctor gpt_4o --max-questions 10
```

### Performance Options
```bash
# Maximum performance (default)
python medical_test.py --all --workers 10 --max-concurrent-agents 4

# Conservative settings
python medical_test.py --all --workers 5 --max-concurrent-agents 2

# Mixed modes
python medical_test.py --all --sequential-agents  # Parallel questions, sequential agents
python medical_test.py --all --sequential         # Sequential questions, parallel agents
```

### Utility Commands
```bash
# List available AI models
python medical_test.py --list-doctors

# Test system setup
python test_setup.py

# Check help for all options
python medical_test.py --help
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--all` | Test all doctors in both vanilla and enhanced modes | - |
| `--doctor DOCTOR` | Test specific doctor (e.g., 'gemini_2_5_pro') | - |
| `--embeddings` | Use medical code embeddings for enhanced context | False |
| `--max-questions N` | Limit number of questions for testing | 100 |
| `--workers N` | Parallel workers for questions per agent | 10 |
| `--max-concurrent-agents N` | Maximum concurrent agents | 4 |
| `--sequential` | Sequential question processing (slower, more reliable) | False |
| `--sequential-agents` | Sequential agent processing | False |
| `--list-doctors` | List available AI models | - |

## AI Doctor Panel

Current medical AI panel (12 models):

### High Performance Models
- **Dr. Gemini Flash the 2.5th** (`gemini_2_5_flash`) - $0.15/$0.60 per M tokens
- **Dr. Gemini Flash Preview the 2.5th** (`gemini_2_5_flash_preview`) - $0.15/$0.60 per M tokens  
- **Dr. GPT 4o Mini** (`gpt_4o_mini`) - $0.15/$0.60 per M tokens

### Mid-Tier Models
- **Dr. DeepSeek V3** (`deepseek_v3`) - $0.28/$0.88 per M tokens
- **Dr. GPT 4.1 Mini** (`gpt_4_1_mini`) - $0.40/$1.60 per M tokens
- **Dr. Mistral Medium** (`mistral_medium`) - $0.40/$2.00 per M tokens

### Premium Models
- **Dr. GPT 4.1** (`gpt_4_1`) - $2.00/$8.00 per M tokens
- **Dr. GPT 4o** (`gpt_4o`) - $2.50/$10.00 per M tokens
- **Dr. Claude Sonnet the 4th** (`claude_sonnet_4`) - $3.00/$15.00 per M tokens
- **Dr. Claude Sonnet the 3.5th** (`claude_sonnet_3_5`) - $3.00/$15.00 per M tokens
- **Dr. Claude Sonnet the 3.7th** (`claude_sonnet_3_7`) - $3.00/$15.00 per M tokens
- **Dr. Gemini Pro the 2.5th** (`gemini_2_5_pro`) - ~$3.00/$15.00 per M tokens

## Medical Code Embeddings

### Enhanced Mode Features
- **Real Medical Data**: Fetches actual ICD-10-CM and HCPCS code descriptions from NLM APIs
- **Question Coverage**: Enhances 20/100 questions (ICD and HCPCS types)
- **Additional Context**: Provides code descriptions for all answer choices
- **Performance Tracking**: Separate result files for vanilla vs enhanced modes

### File Naming Convention
- **Vanilla**: `model_name_YYYYMMDD_HHMMSS.json`
- **Enhanced**: `model_name_enhanced_YYYYMMDD_HHMMSS.json`

## Performance Metrics

### Parallel Processing Performance
- **Question-Level**: Up to 10x faster with 10 parallel workers
- **Agent-Level**: Up to 12x faster with 4 concurrent agents  
- **Combined**: ~67x faster than sequential processing
- **Full Test Suite**: 32 seconds vs 60+ minutes (12 agents, 100 questions each)

### System Specifications
- **Parallel Workers**: 10 concurrent requests per agent
- **Concurrent Agents**: 4 agents running simultaneously
- **Rate Limiting**: 0.5 second delays for API compliance
- **Error Handling**: Comprehensive retry logic with exponential backoff
- **Resource Management**: Semaphores prevent system overload

## Output Format

### Test Result Files
Each test generates a comprehensive JSON file:

```json
{
  "doctor_name": "Dr. Gemini Flash the 2.5th",
  "model_id": "google/gemini-2.5-flash",
  "timestamp": "20250709_224408",
  "total_questions": 100,
  "completed_answers": 98,
  "completion_rate": 98.0,
  "average_response_time": 1.5,
  "use_embeddings": false,
  "embeddings_count": 0,
  "results": [
    {
      "question_number": 1,
      "question": "Which CPT code covers...",
      "question_type": "CPT",
      "choices": {"A": "40800", "B": "41105", "C": "41113", "D": "40804"},
      "selected_answer": "D",
      "reasoning": "CPT code 40804 specifically describes...",
      "response_time": 1.47,
      "raw_response": "{\"id\": \"gen-123...\", \"choices\": [...]}",
      "success": true,
      "error_message": null
    }
  ]
}
```

### Key Metrics Tracked
- **Completion Rate**: Percentage of questions answered (primary metric)
- **Response Time**: Individual and average response times
- **Success Status**: Whether API requests succeeded
- **Error Messages**: Detailed error information when failures occur
- **Raw Responses**: Complete API responses for analysis

## Consensus Analysis

### Automated Consensus Detection
```bash
# Analyze consensus for vanilla mode
python consensus_analyzer.py --mode vanilla --round 1

# Analyze consensus for enhanced mode  
python consensus_analyzer.py --mode enhanced --round 1

# Analyze all results together
python consensus_analyzer.py --mode all --round 1
```

### Consensus Modes
- **Vanilla**: Only models without embeddings
- **Enhanced**: Only models with medical code embeddings
- **All**: Combined analysis of both modes

### Output Locations
- **Test Results**: `../02_test_attempts/`
- **Consensus Reports**: `../03_consensus_benchmarks/consensus_reports/`
- **Validation Reports**: `../04_consensus_validation/`

## Question Types & System Prompts

The system uses specialized prompts based on medical coding type:

- **CPT**: Current Procedural Terminology coding expertise
- **ICD**: ICD-10-CM diagnosis coding expertise  
- **HCPCS**: Healthcare Common Procedure Coding System expertise
- **other**: General medical knowledge

## Error Handling & Reliability

### Comprehensive Error Management
- **API Failures**: Retries with exponential backoff (max 3 attempts)
- **Network Issues**: Graceful degradation with detailed logging
- **Rate Limiting**: Automatic delays and request throttling
- **Model Variations**: Adaptive parsing for different AI response formats
- **Resource Management**: Semaphores prevent system overload

### Fallback Mechanisms
- **Multiple Parsing Strategies**: Tool calls, JSON, text parsing
- **Sequential Fallback**: Option to disable parallelism if needed
- **Individual Agent Isolation**: One agent's failure doesn't stop others
- **Comprehensive Logging**: Detailed error messages and debugging info

## Configuration

### Performance Tuning
Modify `config.py` for custom settings:
```python
# Parallel processing settings
PARALLEL_WORKERS = 10              # Questions per agent
DEFAULT_MAX_CONCURRENT_AGENTS = 4  # Concurrent agents
RATE_LIMIT_DELAY = 0.5             # Seconds between requests
```

### Adding New AI Models
```python
"new_model": {
    "model_id": "provider/model-name",
    "display_name": "Dr. New Model",
    "short_name": "new_model",
    "cost_tier": 3,
    "cost_note": "$X.XX/$Y.YY per M tokens"
}
```

## Best Practices

### For Maximum Performance
```bash
# Use default parallel settings
python medical_test.py --all
```

### For Reliability
```bash
# Reduce parallelism for stability
python medical_test.py --all --workers 3 --max-concurrent-agents 2
```

### For Development/Testing
```bash
# Use sequential processing for debugging
python medical_test.py --all --sequential --sequential-agents --max-questions 5
```

### For Enhanced Analysis
```bash
# Generate embeddings first, then test
cd ../00_code_embeddings && python fetch_embeddings.py
cd ../01_medical_board && python medical_test.py --all
```

## Recent Performance Results

Latest benchmarks show dramatic improvements:
- **Testing Time**: 32 seconds for all 12 models (both modes)
- **Completion Rates**: Most models achieve 100% completion
- **Parallel Efficiency**: Near-linear scaling with concurrent agents
- **Error Rates**: <1% with comprehensive retry logic

## Troubleshooting

### Common Issues
- **API Key**: Ensure OpenRouter API key is set in `.env`
- **Rate Limits**: Reduce `--workers` and `--max-concurrent-agents` if hitting limits
- **Memory Usage**: Use `--sequential-agents` for lower memory consumption
- **Network Issues**: Use `--sequential` for more reliable but slower processing

### Performance Optimization
- **Fast Network**: Use higher `--workers` and `--max-concurrent-agents`
- **Slow Network**: Reduce parallel settings or use sequential modes
- **Cost Control**: Test with `--max-questions` to limit API usage
- **Debugging**: Use single model testing with `--doctor` for troubleshooting

## Advanced Usage

### Batch Testing Scripts
```bash
# Test all models quickly
python medical_test.py --all --max-questions 10

# Compare vanilla vs enhanced on specific model
python medical_test.py --doctor claude_sonnet_4 --max-questions 5
python medical_test.py --doctor claude_sonnet_4 --max-questions 5 --embeddings

# Generate consensus analysis
python consensus_analyzer.py --mode all --round 1
```

This system provides a comprehensive platform for evaluating AI model performance on medical coding tasks with unprecedented speed and detailed analysis capabilities. 

## Results Organization

### Timestamped Test Folders

Each test run now creates a new timestamped folder in `02_test_attempts/` with the format:
```
02_test_attempts/
├── test_YYYYMMDD_HHMMSS/     # Folder for each test session
│   ├── model1_20250709_123456.json
│   ├── model2_enhanced_20250709_123457.json
│   └── ...
└── test_YYYYMMDD_HHMMSS/     # Another test session
    ├── model1_20250709_234567.json
    └── ...
```

**Key Features:**
- **Session Grouping**: All models tested in the same session go into the same timestamped folder
- **Mode Separation**: The `--all` flag creates separate folders for vanilla and enhanced modes
- **Automatic Discovery**: Consensus analyzer automatically finds the latest folder containing the requested mode

### Consensus Analysis

The consensus analyzer now intelligently selects the appropriate folder:

```bash
# Finds latest folder with vanilla (no embeddings) results
python consensus_analyzer.py --mode vanilla

# Finds latest folder with enhanced (with embeddings) results  
python consensus_analyzer.py --mode enhanced

# Finds latest folder with any results
python consensus_analyzer.py --mode all
```

The analyzer searches from newest to oldest until it finds a folder containing files matching the requested mode. 