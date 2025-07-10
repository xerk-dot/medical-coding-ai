#!/usr/bin/env python3
"""
PDF to JSON Parser - 4-step systematic approach

This script parses a PDF test file and extracts questions/answers into JSON format.
Uses a systematic approach: extract text → create blocks → separate Q&A → AI cleanup
"""

import argparse
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List

import fitz  # PyMuPDF
import openai
from dotenv import load_dotenv

# ============================================================================
# STEP 1: EXTRACT ALL TEXT FROM PDF
# ============================================================================

def extract_all_text_from_pdf(pdf_file: str) -> str:
    """Extract all text from PDF without any preprocessing"""
    print(f"Extracting all text from: {pdf_file}")
    
    full_text = ""
    doc = fitz.open(pdf_file)
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        full_text += text + " "
    
    num_pages = len(doc)
    doc.close()
    
    # Clean up Medical Coding Ace text
    print("Cleaning up Medical Coding Ace text...")
    
    original_length = len(full_text)
    
    # Remove "Medical Coding Ace" in all forms
    full_text = re.sub(r'Medical\s*Coding\s*Ace', '', full_text, flags=re.IGNORECASE)
    full_text = re.sub(r'MedicalCodingAce', '', full_text, flags=re.IGNORECASE)
    
    # Clean up multiple spaces left by removals
    full_text = re.sub(r'\s+', ' ', full_text).strip()
    
    removed_chars = original_length - len(full_text)
    if removed_chars > 0:
        print(f"Removed {removed_chars} characters of Medical Coding Ace text")
    
    print(f"Extracted {len(full_text)} characters from {num_pages} pages")
    return full_text

# ============================================================================
# STEP 2: CREATE 100 QUESTION/ANSWER BLOCKS
# ============================================================================

def create_question_blocks(text: str) -> Dict[int, str]:
    """Create exactly 100 question/answer blocks from the full text"""
    print("Creating 100 question/answer blocks...")
    
    # Find question positions sequentially - look for 1. then 2. then 3. etc.
    question_positions = []
    
    # Start by finding question 1
    current_search_start = 0
    
    for question_num in range(1, 101):
        search_text = f'{question_num}.'
        found = False
        
        # Search for this question number starting after the previous question
        pos = text.find(search_text, current_search_start)
        
        while pos != -1:
            # Validate this is actually a question start
            # Check if it's not part of a larger number by looking at what comes before
            is_valid = True
            
            if pos > 0 and text[pos - 1].isdigit():
                # This might be part of a code like "I13.1014." 
                # We need to be more careful here
                
                # Look at the broader context to see if this makes sense as a question
                context_before = text[max(0, pos - 10):pos]
                context_after = text[pos:min(len(text), pos + 50)]
                
                # If this follows a pattern like "D.somenumber14." where 14 is our question
                # we need to check if what comes after looks like question text
                
                # Simple heuristic: if what comes after has letters and looks like question text
                # then this is probably a real question start
                after_number_dot = context_after[len(search_text):].strip()
                
                # If what follows starts with a capital letter or common question words
                if (after_number_dot and 
                    (after_number_dot[0].isupper() or 
                     any(after_number_dot.lower().startswith(word) for word in 
                         ['after', 'during', 'while', 'when', 'what', 'which', 'how', 'where', 'who']))):
                    is_valid = True
                else:
                    is_valid = False
            
            if is_valid:
                question_positions.append((question_num, pos))
                # Update search start for next question to be after this position
                current_search_start = pos + len(search_text)
                found = True
                break
            else:
                # Continue searching for this question number after this position
                pos = text.find(search_text, pos + 1)
        
        if not found:
            print(f"⚠️  Could not find question {question_num}")
            # Still update search start to continue looking for subsequent questions
            # Use the last found position or keep current position
            if question_positions:
                current_search_start = question_positions[-1][1] + 50  # Small offset
    
    print(f"Found question positions for {len(question_positions)} questions")
    if len(question_positions) < 100:
        missing = [i for i in range(1, 101) if i not in [num for num, _ in question_positions]]
        print(f"⚠️  Missing questions: {missing[:20]}{'...' if len(missing) > 20 else ''}")
        
        # Show found vs missing counts
        found_nums = [num for num, _ in question_positions]
        print(f"✅ Found: {sorted(found_nums)[:10]}{'...' if len(found_nums) > 10 else ''}")
    
    # Create blocks by extracting text between consecutive question positions
    blocks = {}
    for i, (question_num, start_pos) in enumerate(question_positions):
        if i + 1 < len(question_positions):
            # End at the start of the next question
            end_pos = question_positions[i + 1][1]
        else:
            # Last question goes to end of text
            end_pos = len(text)
        
        # Extract the full block (question + choices)
        block_text = text[start_pos:end_pos].strip()
        
        # Remove the question number prefix (e.g., "1.")
        if block_text.startswith(f'{question_num}.'):
            block_text = block_text[len(f'{question_num}.'):]
        
        blocks[question_num] = block_text.strip()
    
    print(f"✅ Created {len(blocks)} question/answer blocks")
    return blocks

# ============================================================================
# STEP 3: SEPARATE QUESTION AND CHOICES
# ============================================================================

def separate_question_and_choices(block_text: str) -> tuple[str, dict]:
    """Separate a question/answer block into question and A/B/C/D choices"""
    
    # Find where the question ends - look for both ? and :
    question_end_pos = -1
    question_mark_pos = block_text.find('?')
    colon_pos = block_text.find(':')
    
    # Use whichever comes first (or the only one found)
    if question_mark_pos != -1 and colon_pos != -1:
        question_end_pos = min(question_mark_pos, colon_pos)
        question_terminator = block_text[question_end_pos]
    elif question_mark_pos != -1:
        question_end_pos = question_mark_pos
        question_terminator = '?'
    elif colon_pos != -1:
        question_end_pos = colon_pos
        question_terminator = ':'
    else:
        # No question mark or colon found, treat entire text as question
        return block_text.strip(), {"A": "", "B": "", "C": "", "D": ""}
    
    # Split at the question terminator
    question_part = block_text[:question_end_pos + 1].strip()
    choices_part = block_text[question_end_pos + 1:].strip()
    
    # Extract A.B.C.D. choices from the choices part
    choices = {"A": "", "B": "", "C": "", "D": ""}
    
    if choices_part:
        # Debug: show what we're working with
        # print(f"DEBUG: Choices part: '{choices_part}'")
        
        # Pattern to match A.text B.text C.text D.text
        # The text is often run together like: "A.40800B.41105C.41113D.40804"
        # We need to split on capital letters followed by periods
        
        # First, let's find all the choice positions
        choice_positions = []
        for letter in ['A', 'B', 'C', 'D']:
            pattern = f'{letter}.'
            pos = choices_part.find(pattern)
            if pos != -1:
                choice_positions.append((letter, pos))
        
        # Sort by position
        choice_positions.sort(key=lambda x: x[1])
        
        # Extract text between positions
        for i, (letter, start_pos) in enumerate(choice_positions):
            # Find where this choice's text starts (after the letter and period)
            text_start = start_pos + 2  # Skip "A."
            
            # Find where this choice's text ends
            if i + 1 < len(choice_positions):
                # Next choice starts
                text_end = choice_positions[i + 1][1]
            else:
                # Last choice goes to end
                text_end = len(choices_part)
            
            # Extract and clean the choice text
            choice_text = choices_part[text_start:text_end].strip()
            
            # Clean up the text - remove trailing numbers that might be CPT codes
            # But be careful not to remove codes that are the actual answer
            # For now, just clean obvious artifacts
            choice_text = re.sub(r'\s*Medical\s+Coding\s+Ace.*?$', '', choice_text, flags=re.IGNORECASE).strip()
            
            choices[letter] = choice_text
    
    return question_part, choices

# ============================================================================
# STEP 4: BUILD JSON STRUCTURE  
# ============================================================================

def build_json_from_blocks(question_blocks: Dict[int, str]) -> List[Dict]:
    """Build JSON structure from question/answer blocks"""
    print("Building JSON structure from blocks...")
    
    json_questions = []
    
    for question_num in sorted(question_blocks.keys()):
        block_text = question_blocks[question_num]
        question_text, choices = separate_question_and_choices(block_text)
        
        # Only include if we have a reasonable question
        if len(question_text) > 10:
            json_questions.append({
                "question_number": question_num,
                "question": question_text,
                "choices": choices
            })
    
    print(f"✅ Built JSON for {len(json_questions)} questions")
    return json_questions

# ============================================================================
# STEP 5: USE AI ONLY FOR TEXT CLEANUP (PARALLEL)
# ============================================================================

def load_openai_key():
    """Load OpenAI API key from .env file"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('OPENAI_API_KEY='):
                    api_key = line.strip().split('=', 1)[1]
                    if openai:
                        openai.api_key = api_key
                    return True
    return False

def cleanup_batch_with_ai(batch_info):
    """Clean up a single batch of questions with AI"""
    batch_num, batch = batch_info
    
    try:
        # Create prompt for this batch
        batch_text = "Questions to clean up:\n\n"
        for q in batch:
            batch_text += f"Question {q['question_number']}: {q['question']}\n"
            batch_text += f"A: {q['choices']['A']}\n"
            batch_text += f"B: {q['choices']['B']}\n"
            batch_text += f"C: {q['choices']['C']}\n"
            batch_text += f"D: {q['choices']['D']}\n\n"
        
        prompt = f"""Clean up the text formatting in these medical coding questions. Fix run-together words by adding proper spaces, but keep all the same meaning and information.

For example:
- "Duringaregularcheckup" should become "During a regular checkup"
- "Dr.Stevens" should become "Dr. Stevens"
- "CPTcode" should become "CPT code"

Return ONLY a JSON array with the cleaned questions:
[
  {{
    "question_number": 1,
    "question": "cleaned question text",
    "choices": {{
      "A": "cleaned choice A",
      "B": "cleaned choice B",
      "C": "cleaned choice C",
      "D": "cleaned choice D"
    }}
  }}
]

{batch_text}"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You fix text formatting by adding proper spaces between words. Keep all the same information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=3000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
        if json_match:
            try:
                cleaned_batch = json.loads(json_match.group())
                return batch_num, cleaned_batch, None
            except json.JSONDecodeError as e:
                return batch_num, None, f"JSON parse error: {e}"
        else:
            return batch_num, None, "No JSON found in response"
            
    except Exception as e:
        return batch_num, None, f"API error: {e}"

def cleanup_text_with_ai(questions: List[Dict]) -> List[Dict]:
    """Use AI to clean up text formatting and spacing (parallel processing)"""
    
    if not openai or not load_openai_key():
        print("AI not available - returning questions without text cleanup")
        return questions
    
    print(f"Cleaning up text formatting with AI for {len(questions)} questions...")
    
    # Split into batches of 10 questions
    batch_size = 10
    batches = []
    for i in range(0, len(questions), batch_size):
        batch = questions[i:i + batch_size]
        batches.append((i // batch_size, batch))
    
    print(f"Processing {len(batches)} batches in parallel...")
    
    # Process all batches in parallel
    cleaned_questions = [None] * len(questions)  # Pre-allocate with correct size
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all batches to thread pool
        future_to_batch = {executor.submit(cleanup_batch_with_ai, batch_info): batch_info for batch_info in batches}
        
        # Collect results as they complete
        for future in as_completed(future_to_batch):
            batch_info = future_to_batch[future]
            batch_num, original_batch = batch_info
            
            try:
                result_batch_num, cleaned_batch, error = future.result()
                
                if cleaned_batch:
                    print(f"✅ Batch {result_batch_num + 1}: Cleaned {len(cleaned_batch)} questions")
                    # Insert cleaned questions at correct positions
                    start_idx = result_batch_num * batch_size
                    for i, q in enumerate(cleaned_batch):
                        if start_idx + i < len(cleaned_questions):
                            cleaned_questions[start_idx + i] = q
                else:
                    print(f"❌ Batch {result_batch_num + 1}: {error}, using original")
                    # Use original batch
                    start_idx = result_batch_num * batch_size
                    for i, q in enumerate(original_batch):
                        if start_idx + i < len(cleaned_questions):
                            cleaned_questions[start_idx + i] = q
                            
            except Exception as e:
                print(f"❌ Batch {batch_num + 1}: Exception {e}, using original")
                # Use original batch
                start_idx = batch_num * batch_size
                for i, q in enumerate(original_batch):
                    if start_idx + i < len(cleaned_questions):
                        cleaned_questions[start_idx + i] = q
    
    # Filter out any None values and return
    final_questions = [q for q in cleaned_questions if q is not None]
    print(f"✅ Parallel cleanup complete: {len(final_questions)} questions processed")
    
    return final_questions

# ============================================================================
# ANSWER EXTRACTION FUNCTIONS
# ============================================================================

def extract_answers_from_pdf(answers_pdf_file: str) -> Dict[int, str]:
    """Extract answers from the _with_answers.pdf file"""
    print(f"\n=== Extracting Answers ===")
    print(f"Processing: {answers_pdf_file}")
    
    # Extract all text from the answers PDF
    raw_text = extract_all_text_from_pdf(answers_pdf_file)
    if not raw_text:
        print("ERROR: Could not extract text from answers PDF")
        return {}
    
    answers = {}
    
    # Look for answer patterns like "Answer: C. 41113" where C is the correct choice
    # The pattern is: Answer: followed by a letter (A, B, C, or D) and then a dot
    pattern = r'Answer:\s*([A-D])\.'
    matches = re.findall(pattern, raw_text)
    
    print(f"Found {len(matches)} answer patterns")
    
    # The answers should be in sequential order (1, 2, 3, ...)
    for i, answer_letter in enumerate(matches, 1):
        if i <= 100:  # Valid question range
            answers[i] = answer_letter
    
    print(f"✅ Extracted answers for {len(answers)} questions")
    
    # Debug: show first few answers
    if answers:
        print("First 10 answers:")
        for i in range(1, min(11, len(answers) + 1)):
            if i in answers:
                print(f"  Q{i}: {answers[i]}")
    
    return answers

def create_answers_json(answers_dict: Dict[int, str], output_file: str):
    """Create JSON file with answers"""
    print(f"Saving answers to: {output_file}")
    
    # Convert to list format matching question numbers
    answers_list = []
    for question_num in range(1, 101):
        if question_num in answers_dict:
            answers_list.append({
                "question_number": question_num,
                "correct_answer": answers_dict[question_num]
            })
        else:
            # Add placeholder for missing answers
            answers_list.append({
                "question_number": question_num,
                "correct_answer": "N/A"
            })
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(answers_list, f, indent=2, ensure_ascii=False)
        print(f"✅ Answers saved successfully")
    except Exception as e:
        print(f"❌ Error saving answers: {e}")

# ============================================================================
# SUPPORTING FUNCTIONS
# ============================================================================

def save_raw_text(text: str, filename: str):
    """Save raw extracted text for debugging"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Raw text saved to: {filename}")

def create_questions_json(questions: List[Dict], output_file: str):
    """Create JSON file with questions"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2, ensure_ascii=False)
    print(f"Questions saved to: {output_file}")

def list_test_files():
    """List available test PDF files"""
    project_root = Path(__file__).parent.parent.parent
    test_dir = project_root / "00_question_banks/test_1"
    
    if not test_dir.exists():
        print("No test directory found at 00_question_banks/test_1")
        return []
    
    pdf_files = list(test_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in 00_question_banks/test_1")
        return []
    
    print("Available PDF files in 00_question_banks/test_1:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf_file.name}")
    
    return pdf_files

# ============================================================================
# MAIN FUNCTION UPDATES
# ============================================================================

def parse_pdf(pdf_file: str, save_debug: bool = False, use_ai_cleanup: bool = True):
    """Main parsing function using the systematic approach"""
    print(f"\n=== PDF to JSON Parser ===")
    print(f"Processing: {pdf_file}")
    
    # Step 1: Extract ALL text from PDF
    print(f"\n=== Step 1: Extract Text ===")
    raw_text = extract_all_text_from_pdf(pdf_file)
    if not raw_text:
        print("ERROR: Could not extract text from PDF")
        return
    
    # Save raw text for debugging if requested
    if save_debug:
        base_name = os.path.splitext(os.path.basename(pdf_file))[0]
        debug_file = f"debug_{base_name}_raw_text.txt"
        save_raw_text(raw_text, debug_file)
    
    # Step 2: Create 100 question/answer blocks
    print(f"\n=== Step 2: Create Question Blocks ===")
    question_blocks = create_question_blocks(raw_text)
    
    if not question_blocks:
        print("ERROR: No question blocks found!")
        return
    
    # Step 3: Build JSON structure from blocks
    print(f"\n=== Step 3: Build JSON Structure ===")
    questions = build_json_from_blocks(question_blocks)
    
    if not questions:
        print("ERROR: No valid questions extracted!")
        return
    
    # Step 4: Use AI to clean up text formatting (optional, parallel)
    if use_ai_cleanup:
        print(f"\n=== Step 4: AI Text Cleanup (Parallel) ===")
        questions = cleanup_text_with_ai(questions)
    else:
        print(f"\n=== Step 4: Skipped (AI cleanup disabled) ===")
    
    # Save results
    print(f"\n=== Saving Results ===")
    base_name = os.path.splitext(os.path.basename(pdf_file))[0]
    output_dir = Path(__file__).parent.parent.parent / "00_question_banks/test_1"
    output_dir.mkdir(exist_ok=True)
    
    questions_file = output_dir / f"{base_name}_questions.json"
    create_questions_json(questions, str(questions_file))
    
    # Check for answers file and extract answers if available
    answers_pdf_path = output_dir / f"{base_name}_with_answers.pdf"
    if answers_pdf_path.exists():
        print(f"\n=== Answer Extraction ===")
        print(f"Found answers file: {answers_pdf_path}")
        
        answers_dict = extract_answers_from_pdf(str(answers_pdf_path))
        if answers_dict:
            answers_file = output_dir / f"{base_name}_answers.json"
            create_answers_json(answers_dict, str(answers_file))
        else:
            print("⚠️  No answers could be extracted")
    else:
        print(f"\n=== Answer Extraction ===")
        print(f"No answers file found (looking for: {answers_pdf_path.name})")
    
    # Summary
    print(f"\n=== Summary ===")
    print(f"✅ Questions extracted: {len(questions)}")
    if questions:
        question_nums = [q['question_number'] for q in questions]
        print(f"✅ Question range: {min(question_nums)} - {max(question_nums)}")
        
        # Show which questions we found
        missing = []
        for i in range(1, 101):
            if i not in question_nums:
                missing.append(i)
        if missing:
            print(f"❌ Missing questions: {missing[:10]}{'...' if len(missing) > 10 else ''}")
        else:
            print("✅ All 100 questions found!")
    print("✅ Complete!")

def main():
    parser = argparse.ArgumentParser(
        description="Simple PDF to JSON Parser - Extract text, use regex, then parallel AI cleanup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process test file
  %(prog)s test_1.pdf
  
  # Save raw text for debugging
  %(prog)s test_1.pdf --debug
  
  # Skip AI text cleanup
  %(prog)s test_1.pdf --no-ai
  
  # List available files
  %(prog)s --list
        """
    )
    
    parser.add_argument(
        "pdf_file",
        nargs="?",
        help="PDF file to process"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available PDF files"
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Save raw extracted text for debugging"
    )
    
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip AI text cleanup"
    )
    
    args = parser.parse_args()
    
    # Handle --list
    if args.list:
        list_test_files()
        return 0
    
    # Validate arguments
    if not args.pdf_file:
        parser.print_help()
        return 1
    
    # Resolve file path
    pdf_path = Path(args.pdf_file)
    if not pdf_path.is_absolute():
        project_root = Path(__file__).parent.parent.parent
        test_path = project_root / "00_question_banks/test_1" / args.pdf_file
        if test_path.exists():
            pdf_path = test_path
        elif not pdf_path.exists():
            print(f"ERROR: PDF file not found: {args.pdf_file}")
            return 1
    
    # Run parser
    use_ai = not args.no_ai
    parse_pdf(str(pdf_path), args.debug, use_ai)
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
