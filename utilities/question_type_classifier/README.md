# Question Type Classifier

A utility to automatically classify medical coding questions by type (CPT, ICD, HCPCS, or other) and append this information to the JSON file.

## Quick Start

```bash
cd utilities/question_type_classifier
python question_classifier.py
```

## How It Works

The classifier uses regex patterns to identify key terms in questions:

1. **CPT Questions** - Contain terms like "CPT", "CPT code", "which CPT"
2. **ICD Questions** - Contain terms like "ICD", "ICD-10", "ICD-10-CM", "ICD code"  
3. **HCPCS Questions** - Contain terms like "HCPCS", "HCPCS Level II", "HCPCS code"
4. **Other Questions** - Don't contain any of the above terms (anatomy, medical terminology, etc.)

## Features

- ✅ **Regex-based classification** using comprehensive pattern matching
- ✅ **Case-insensitive matching** to catch variations in capitalization
- ✅ **Preserves existing data** - only adds `question_type` field
- ✅ **Statistics reporting** - shows count of each question type
- ✅ **Example display** - shows sample questions for verification
- ✅ **Dry-run mode** - preview results without saving changes

## Usage

### Basic Classification
```bash
# Classify questions in the default file
python question_classifier.py
```

### Advanced Options
```bash
# Specify a different JSON file
python question_classifier.py --input /path/to/questions.json

# Show more examples of each type (default: 3)
python question_classifier.py --examples 5

# Preview classification without saving changes
python question_classifier.py --dry-run
```

## Output Format

The script adds a `question_type` field to each question:

```json
{
  "question_number": 1,
  "question": "Which CPT code covers the excision of an oral lesion?",
  "choices": {
    "A": "40800",
    "B": "41105",
    "C": "41113", 
    "D": "40804"
  },
  "question_type": "CPT"
}
```

## Classification Patterns

### CPT Patterns
- `\bcpt\b` - Matches "CPT" as a whole word
- `\bcpt\s+code\b` - Matches "CPT code"
- `\bwhich\s+cpt\b` - Matches "which CPT"
- `\bcpt\s+coding\b` - Matches "CPT coding"

### ICD Patterns  
- `\bicd\b` - Matches "ICD" as a whole word
- `\bicd\s*-?\s*10\b` - Matches "ICD-10" or "ICD 10"
- `\bicd\s*-?\s*10\s*-?\s*cm\b` - Matches "ICD-10-CM"
- `\bwhich\s+icd\b` - Matches "which ICD"
- `\bicd\s+code\b` - Matches "ICD code"

### HCPCS Patterns
- `\bhcpcs\b` - Matches "HCPCS" as a whole word
- `\bhcpcs\s+level\s+ii\b` - Matches "HCPCS Level II"
- `\bwhich\s+hcpcs\b` - Matches "which HCPCS"
- `\bhcpcs\s+code\b` - Matches "HCPCS code"

## Example Output

```
🎯 Question Type Classifier
📁 Input file: /path/to/test_1_questions.json
✅ Loaded 100 questions from /path/to/test_1_questions.json
🔍 Classifying questions by type...

📊 Classification Results:
   CPT questions:    65
   ICD questions:    15
   HCPCS questions:   8
   Other questions:  12
   Total:           100

📝 Examples by Question Type:

CPT Questions:
  1. Q1: During a regular checkup, Dr. Stevens discovered a suspicious lesion on the floor of Paul's mou...
  2. Q2: While shaving, Robert accidentally caused a small cut on his chin that later became infected. ...
  3. Q3: Lucas, a professional swimmer, developed a cyst in his arm due to repetitive motion. The docto...

ICD Questions:
  1. Q13: During a routine check-up, Mark was diagnosed with essential (primary) hypertension. Which IC...
  2. Q18: During a routine check-up, Brian was diagnosed with benign essential hypertension. What ICD 1...
  3. Q22: After a trip to a tropical country, Jessica was diagnosed with Dengue fever without warning s...

HCPCS Questions:
  1. Q15: David uses a manual wheelchair due to his mobility limitations. Which HCPCS Level II code per...
  2. Q25: During his physical therapy, John was provided with a therapeutic elastic band. Which HCPCS L...
  3. Q30: For his severe back pain, Dr. Simmons administers an epidural injection to Mike. Which HCPCS ...

Other Questions:
  1. Q8: The Relative Value Unit (RVU) associated with a CPT code reflects:...
  2. Q9: What does the term 'bradycardia' refer to?...
  3. Q21: Which part of the brain is responsible for regulating vital functions like heartbeat and breat...

✅ Successfully updated /path/to/test_1_questions.json
✅ Classification complete!
```

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library) 