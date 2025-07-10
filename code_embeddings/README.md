# Medical Code Embeddings System

This system implements real-time medical code lookups using official government APIs to enhance AI model performance on medical coding questions.

## APIs Implemented

- **ICD-10-CM API**: https://clinicaltables.nlm.nih.gov/apidoc/icd10cm/v3/doc.html
- **HCPCS API**: https://clinicaltables.nlm.nih.gov/apidoc/hcpcs/v3/doc.html

**Note**: CPT codes are not available as they are copyrighted by the American Medical Association.

## Implementation

### 1. Code Embeddings Fetcher (`fetch_embeddings.py`)

Fetches real medical code descriptions for ICD and HCPCS questions:
- Filters questions to only ICD and HCPCS types (ignores CPT and other types)
- Uses official NLM Clinical Tables APIs for accurate, up-to-date information
- Creates embeddings for all 4 answer choices per question
- Saves results to `question_embeddings.json`

### 2. Enhanced Medical Test System

The medical test system now supports embeddings with a `--embeddings` flag:

```bash
# Standard mode (no embeddings)
python3 medical_test.py --doctor gemini_2_5_pro

# Enhanced mode (with medical code embeddings)
python3 medical_test.py --embeddings --doctor gemini_2_5_pro

# Test specific number of questions with embeddings
python3 medical_test.py --embeddings --doctor gemini_2_5_pro --max-questions 10
```

### 3. Embeddings Integration

When enabled, the system:
- Loads pre-generated embeddings from `question_embeddings.json`
- Adds detailed medical code descriptions as context to relevant questions
- Only provides embeddings for questions where real API data was successfully fetched
- Enhances AI model understanding without changing the core question

## Usage

### Step 1: Generate Embeddings

```bash
cd code_embeddings
python3 fetch_embeddings.py
```

This creates embeddings for 20 questions (13 ICD + 7 HCPCS) out of 100 total questions.

### Step 2: Run Enhanced Tests

```bash
cd ../medical_board
python3 medical_test.py --embeddings --doctor gemini_2_5_pro
```

## Example Enhancement

**Original Question:**
> During a routine check-up, Mark was diagnosed with essential (primary) hypertension. Which ICD 10 CM code represents this condition?
> 
> A: I10  
> B: I11.9  
> C: I12.9  
> D: I13.10

**With Embeddings:**
> [Same question] + Additional Medical Code Information:
> • A: I10 - Essential (primary) hypertension
> • B: I11.9 - Hypertensive heart disease without heart failure  
> • C: I12.9 - Hypertensive chronic kidney disease with stage 1 through stage 4 chronic kidney disease, or unspecified chronic kidney disease
> • D: I13.10 - Hypertensive heart and chronic kidney disease without heart failure, with stage 1 through stage 4 chronic kidney disease, or unspecified chronic kidney disease

## Files Generated

- `question_embeddings.json` - Contains embeddings for ICD and HCPCS questions
- Enhanced test results include `"use_embeddings": true` flag in JSON output

## Benefits

1. **Improved Accuracy**: AI models get real medical code descriptions to make informed decisions
2. **Educational Value**: Shows how additional context affects AI performance  
3. **Official Sources**: Uses government APIs for authoritative medical code information
4. **Selective Enhancement**: Only adds context where official data is available
