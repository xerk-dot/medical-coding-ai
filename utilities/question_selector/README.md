# Question Selector

A utility for creating custom question banks from available test datasets. This tool allows you to select specific questions from test_1 and test_2 to create new question banks stored in the `00_question_banks` directory.

## Features

- **Discover available test banks** from the 00_question_banks directory
- **Create custom question banks** by selecting questions from multiple test sources
- **Random or sequential selection** of questions
- **Maintain question-answer correspondence** when shuffling
- **Track source information** for each question (original test and question number)
- **Generate final_questions.json and final_answers.json** for use in other operations

## Available Test Banks

The tool automatically discovers test banks in the `00_question_banks` directory:

- **test_1**: 100 questions with answers (CPT, ICD, HCPCS, other)
- **test_2**: 100 questions with answers (CPT, ICD, HCPCS, other)

## Usage

### List Available Test Banks

```bash
python3 question_selector.py --list
```

This will show:
- Number of questions in each test
- Whether answers are available
- Question types present in each test

### Create a Random Question Bank

```bash
# Create a bank with 50 questions from each test (100 total)
python3 question_selector.py --random --test1-count 50 --test2-count 50

# Create a custom-sized bank
python3 question_selector.py --random --test1-count 25 --test2-count 75 --output custom_bank
```

### Create a Sequential Question Bank

```bash
# Take first 50 questions from each test (no randomization)
python3 question_selector.py --test1-count 50 --test2-count 50 --no-shuffle
```

### Command Line Options

- `--list`: List available test banks and their details
- `--random`: Randomly select questions from each test
- `--output NAME`: Set output file base name (default: "final")
- `--test1-count N`: Number of questions to select from test_1 (default: 50)
- `--test2-count N`: Number of questions to select from test_2 (default: 50)
- `--no-shuffle`: Don't shuffle the final question order

## Output Files

The tool creates two files in the `00_question_banks` directory:

1. **`final_questions.json`** (or `{output_name}_questions.json`)
   - Contains the selected questions with renumbered question_number (1, 2, 3...)
   - Includes source tracking: `source_test` and `original_question_number`

2. **`final_answers.json`** (or `{output_name}_answers.json`)
   - Contains corresponding answers with matching question numbers
   - Includes same source tracking information

## Example Output Structure

### Questions File
```json
[
  {
    "question_number": 1,
    "question": "Dr. Lopez performs an excision of a tumor on the knee joint, deep, measuring 3.5 cm. What CPT code should be used for this procedure?",
    "choices": {
      "A": "27327",
      "B": "27328",
      "C": "27329",
      "D": "27330"
    },
    "question_type": "CPT",
    "source_test": "test_2",
    "original_question_number": 1
  }
]
```

### Answers File
```json
[
  {
    "question_number": 1,
    "correct_answer": "A",
    "source_test": "test_2", 
    "original_question_number": 1
  }
]
```

## Integration with Other Tools

The created question banks (`final_questions.json` and `final_answers.json`) serve as the source for all other operations in the system. These files can be used by:

- Assessment tools
- Validation systems
- Report generators
- Any other components that need access to the question bank

## Question Bank Structure

Each question contains:
- `question_number`: Sequential number in the new bank (1, 2, 3...)
- `question`: The question text
- `choices`: Multiple choice options (A, B, C, D)
- `question_type`: Type of question (CPT, ICD, HCPCS, other)
- `source_test`: Original test name (test_1, test_2)
- `original_question_number`: Original question number in source test

Each answer contains:
- `question_number`: Matching question number
- `correct_answer`: The correct choice (A, B, C, or D)
- `source_test`: Original test name
- `original_question_number`: Original question number in source test

## Examples

### Create a Balanced Random Bank
```bash
python3 question_selector.py --random --test1-count 50 --test2-count 50
```

### Create a Test_1 Heavy Bank
```bash
python3 question_selector.py --random --test1-count 80 --test2-count 20 --output test1_heavy
```

### Create a Small Sample Bank
```bash
python3 question_selector.py --random --test1-count 10 --test2-count 10 --output sample
```

The generated question banks will be available in `../../00_question_banks/` and ready for use by other system components.