"""
Medical Code Embeddings Fetcher

This script fetches ICD-10-CM and HCPCS code data from the NLM Clinical Tables APIs
and creates embeddings for each question's answer choices to provide additional context
to AI models during testing.

APIs used:
- ICD-10-CM: https://clinicaltables.nlm.nih.gov/apidoc/icd10cm/v3/doc.html
- HCPCS: https://clinicaltables.nlm.nih.gov/apidoc/hcpcs/v3/doc.html
"""

import json
import requests
import time
from typing import Dict, List, Optional, Tuple
import os

class MedicalCodeFetcher:
    """Fetches medical code data from NLM Clinical Tables APIs"""
    
    def __init__(self):
        self.icd10_base_url = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"
        self.hcpcs_base_url = "https://clinicaltables.nlm.nih.gov/api/hcpcs/v3/search"
        self.session = requests.Session()
        
    def fetch_icd10_code(self, code: str) -> Optional[Dict]:
        """
        Fetch ICD-10-CM code information
        
        Args:
            code: ICD-10-CM code (e.g., "M25.511")
            
        Returns:
            Dictionary with code information or None if not found
        """
        try:
            # Search for exact code match
            params = {
                'terms': code,
                'ef': 'code,name',  # Get both code and description
                'maxList': 5
            }
            
            response = self.session.get(self.icd10_base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # API returns [count, codes_array, field_data_object, full_data_array]
            # Example: [1,["I10"],{"code":["I10"],"name":["Essential (primary) hypertension"]},[["I10","Essential (primary) hypertension"]]]
            if len(data) >= 3 and data[0] > 0:
                codes = data[1]
                field_data = data[2]
                
                # Look for exact match
                if codes and 'name' in field_data:
                    names = field_data['name']
                    for i, api_code in enumerate(codes):
                        if api_code.upper() == code.upper() and i < len(names):
                            return {
                                'code': api_code,
                                'description': names[i],
                                'system': 'ICD-10-CM',
                                'source': 'NLM Clinical Tables'
                            }
                
                # If no exact match but we have results, return first
                if codes and 'name' in field_data and field_data['name']:
                    return {
                        'code': codes[0],
                        'description': field_data['name'][0],
                        'system': 'ICD-10-CM',
                        'source': 'NLM Clinical Tables',
                        'note': f'Closest match for {code}'
                    }
            
            return None
            
        except Exception as e:
            print(f"Error fetching ICD-10-CM code {code}: {e}")
            return None
    
    def fetch_hcpcs_code(self, code: str) -> Optional[Dict]:
        """
        Fetch HCPCS code information
        
        Args:
            code: HCPCS code (e.g., "J7323")
            
        Returns:
            Dictionary with code information or None if not found
        """
        try:
            # Search for exact code match
            params = {
                'terms': code,
                'ef': 'code,short_description',  # Get code and short description
                'maxList': 5
            }
            
            response = self.session.get(self.hcpcs_base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # API returns [count, codes_array, field_data_object, full_data_array]
            # Example: [1,["J1020"],{"code":["J1020"],"short_description":[null]},[["J1020","Methylprednisolone 20 mg inj"]]]
            if len(data) >= 4 and data[0] > 0:
                codes = data[1]
                full_data = data[3]  # Use the full data array which has descriptions
                
                # Look for exact match
                for i, api_code in enumerate(codes):
                    if api_code.upper() == code.upper() and i < len(full_data):
                        full_entry = full_data[i]
                        description = full_entry[1] if len(full_entry) > 1 else "No description available"
                        return {
                            'code': api_code,
                            'description': description,
                            'system': 'HCPCS',
                            'source': 'NLM Clinical Tables'
                        }
                
                # If no exact match but we have results, return first
                if codes and full_data:
                    full_entry = full_data[0]
                    description = full_entry[1] if len(full_entry) > 1 else "No description available"
                    return {
                        'code': codes[0],
                        'description': description,
                        'system': 'HCPCS',
                        'source': 'NLM Clinical Tables',
                        'note': f'Closest match for {code}'
                    }
            
            return None
            
        except Exception as e:
            print(f"Error fetching HCPCS code {code}: {e}")
            return None
    
    def fetch_code_info(self, code: str, code_system: str) -> Optional[Dict]:
        """
        Fetch code information based on the code system
        
        Args:
            code: Medical code
            code_system: 'ICD', 'HCPCS', or 'CPT'
            
        Returns:
            Dictionary with code information or None if not found
        """
        if code_system.upper() == 'ICD':
            return self.fetch_icd10_code(code)
        elif code_system.upper() == 'HCPCS':
            return self.fetch_hcpcs_code(code)
        elif code_system.upper() == 'CPT':
            # CPT codes are copyrighted by AMA, so we can't fetch them
            return {
                'code': code,
                'description': 'CPT code (proprietary - description not available)',
                'system': 'CPT',
                'source': 'Not available (AMA copyright)',
                'note': 'CPT codes are copyrighted by the American Medical Association'
            }
        else:
            return None

def create_question_embeddings():
    """
    Create embeddings for ICD and HCPCS questions only using their respective APIs
    """
    # Load questions
    questions_file = '../00_question_banks/final_questions.json'
    
    if not os.path.exists(questions_file):
        print(f"Error: Questions file not found at {questions_file}")
        return
    
    with open(questions_file, 'r') as f:
        questions = json.load(f)
    
    fetcher = MedicalCodeFetcher()
    embeddings_data = []
    
    # Filter questions to only ICD and HCPCS types
    relevant_questions = [q for q in questions if q.get('question_type', '').upper() in ['ICD', 'HCPCS']]
    
    print(f"Processing {len(relevant_questions)} relevant questions (ICD and HCPCS only)...")
    print(f"Skipping {len(questions) - len(relevant_questions)} questions (CPT and other types)")
    
    for i, question in enumerate(relevant_questions, 1):
        question_number = question.get('question_number', i)
        question_type = question.get('question_type', 'other')
        choices = question.get('choices', {})
        
        print(f"\nProcessing question {question_number} ({question_type})")
        
        # Create embeddings for each choice
        choice_embeddings = []
        
        for choice_letter, choice_code in choices.items():
            print(f"  Fetching {question_type} data for choice {choice_letter}: {choice_code}")
            
            # Only fetch from appropriate API based on question type
            if question_type.upper() == 'ICD':
                code_info = fetcher.fetch_icd10_code(choice_code)
            elif question_type.upper() == 'HCPCS':
                code_info = fetcher.fetch_hcpcs_code(choice_code)
            else:
                code_info = None
            
            if code_info:
                choice_embeddings.append({
                    'choice': choice_letter,
                    'code': choice_code,
                    'embedding': code_info
                })
                print(f"    ✓ Found: {code_info.get('description', 'No description')[:80]}...")
            else:
                # Create placeholder for codes we can't fetch
                choice_embeddings.append({
                    'choice': choice_letter,
                    'code': choice_code,
                    'embedding': {
                        'code': choice_code,
                        'description': f'{question_type} code (no additional information available)',
                        'system': question_type,
                        'source': 'API fetch failed',
                        'note': f'Could not fetch {question_type} information from NLM API'
                    }
                })
                print(f"    ✗ No data found for {choice_code}")
            
            # Rate limiting - be nice to the API
            time.sleep(0.3)
        
        # Add to embeddings data
        embeddings_data.append({
            'question_number': question_number,
            'question_type': question_type,
            'question': question.get('question', ''),
            'choices': choice_embeddings
        })
        
        print(f"  Completed question {question_number} with {len(choice_embeddings)} choice embeddings")
    
    # Save embeddings to JSON file
    output_file = 'question_embeddings.json'
    with open(output_file, 'w') as f:
        json.dump(embeddings_data, f, indent=2)
    
    print(f"\n✓ Embeddings saved to {output_file}")
    print(f"✓ Created embeddings for {len(embeddings_data)} questions")
    
    # Create summary statistics
    icd_count = sum(1 for q in embeddings_data if q['question_type'] == 'ICD')
    hcpcs_count = sum(1 for q in embeddings_data if q['question_type'] == 'HCPCS')
    total_embeddings = sum(len(q['choices']) for q in embeddings_data)
    
    print(f"\nSummary:")
    print(f"  ICD questions: {icd_count}")
    print(f"  HCPCS questions: {hcpcs_count}")
    print(f"  Total embeddings created: {total_embeddings}")
    print(f"  Average embeddings per question: {total_embeddings/len(embeddings_data):.1f}")

if __name__ == "__main__":
    create_question_embeddings() 