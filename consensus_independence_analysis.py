#!/usr/bin/env python3
"""
Analysis script to identify AI models with the best consensus independence.
This script analyzes which models voted correctly when the consensus was wrong.
"""

import json
import os
from collections import defaultdict
from typing import Dict, List, Tuple, Set

def load_json(file_path: str) -> dict:
    """Load JSON data from file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def get_wrong_consensus_questions(validation_report: dict) -> List[int]:
    """Extract question numbers where consensus was wrong."""
    wrong_questions = []
    for question in validation_report['questions']:
        if not question['is_consensus_correct']:
            wrong_questions.append(question['question_number'])
    return wrong_questions

def analyze_consensus_voting(consensus_report: dict, wrong_questions: List[int], 
                           validation_report: dict) -> Dict[str, Dict]:
    """
    Analyze which models voted correctly when consensus was wrong.
    Returns model statistics including independence scores.
    """
    model_stats = defaultdict(lambda: {
        'correct_when_consensus_wrong': 0,
        'total_wrong_consensus_questions': 0,
        'independence_score': 0.0,
        'correct_votes_details': []
    })
    
    # Create a mapping of question numbers to correct answers
    correct_answers = {}
    for question in validation_report['questions']:
        correct_answers[question['question_number']] = question['correct_answer']
    
    # Analyze each question where consensus was wrong
    for question in consensus_report['questions']:
        if question['question_number'] in wrong_questions:
            correct_answer = correct_answers[question['question_number']]
            
            # Look through all voting rounds to find who voted correctly
            if 'vote_history' in question:
                # Use the final round votes to see who stood their ground
                final_round = question['vote_history'][-1]
                
                # Find models that voted for the correct answer in the final round
                if correct_answer in final_round['votes']:
                    correct_voters = final_round['votes'][correct_answer]
                    
                    for model in correct_voters:
                        model_stats[model]['correct_when_consensus_wrong'] += 1
                        model_stats[model]['correct_votes_details'].append({
                            'question': question['question_number'],
                            'correct_answer': correct_answer,
                            'consensus_choice': question['final_consensus_choice'],
                            'consensus_percentage': question['final_consensus_percentage']
                        })
                
                # Count total wrong consensus questions for each model that participated
                for round_data in question['vote_history']:
                    for choice_votes in round_data['votes'].values():
                        for model in choice_votes:
                            if model not in [stats['model'] for stats in model_stats.values() if 'model' in stats]:
                                model_stats[model]['total_wrong_consensus_questions'] = len(wrong_questions)
    
    # Calculate independence scores
    for model, stats in model_stats.items():
        if len(wrong_questions) > 0:
            stats['independence_score'] = stats['correct_when_consensus_wrong'] / len(wrong_questions)
        stats['total_wrong_consensus_questions'] = len(wrong_questions)
    
    return dict(model_stats)

def get_individual_performance(test_results_dir: str, correct_answers: dict) -> Dict[str, Dict]:
    """
    Get individual model performance from standalone tests.
    """
    model_performance = defaultdict(lambda: {
        'total_questions': 0,
        'correct_answers': 0,
        'accuracy': 0.0,
        'test_file': ''
    })
    
    # Look for test results in the first round (standalone performance)
    first_round_dir = os.path.join(test_results_dir, 'test_20250710_195405')
    
    if os.path.exists(first_round_dir):
        for filename in os.listdir(first_round_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(first_round_dir, filename)
                
                try:
                    test_data = load_json(file_path)
                    
                    # Extract model name from filename or test data
                    model_name = extract_model_name(filename, test_data)
                    
                    if 'results' in test_data:
                        total = len(test_data['results'])
                        correct = 0
                        
                        for result in test_data['results']:
                            question_num = result.get('question_number')
                            answer = result.get('selected_answer', '').strip().upper()
                            
                            if question_num in correct_answers:
                                if answer == correct_answers[question_num]:
                                    correct += 1
                        
                        model_performance[model_name] = {
                            'total_questions': total,
                            'correct_answers': correct,
                            'accuracy': correct / total if total > 0 else 0.0,
                            'test_file': filename
                        }
                
                except Exception as e:
                    print(f"Error processing {filename}: {e}")
    
    return dict(model_performance)

def extract_model_name(filename: str, test_data: dict) -> str:
    """Extract standardized model name from filename or test data."""
    # Remove timestamp and file extension
    name_part = filename.split('_20250710')[0]
    
    # Mapping to standardize names
    name_mappings = {
        'claude_sonnet_3_5th': 'Dr. Claude Sonnet the 3.5th',
        'claude_sonnet_3_7th': 'Dr. Claude Sonnet the 3.7th', 
        'claude_sonnet_4th': 'Dr. Claude Sonnet the 4th',
        'deepseek_v3': 'Dr. DeepSeek V3',
        'gemini_flash_2_5th': 'Dr. Gemini Flash the 2.5th',
        'gemini_flash_preview_2_5th': 'Dr. Gemini Flash Preview the 2.5th',
        'gemini_pro_2_5th': 'Dr. Gemini Pro the 2.5th',
        'gpt_4_1': 'Dr. GPT 4.1',
        'gpt_4_1_mini': 'Dr. GPT 4.1 Mini',
        'gpt_4o': 'Dr. GPT 4o',
        'gpt_4o_mini': 'Dr. GPT 4o Mini',
        'mistral_medium': 'Dr. Mistral Medium'
    }
    
    return name_mappings.get(name_part, name_part)

def main():
    """Main analysis function."""
    print("🔍 Analyzing AI Model Consensus Independence")
    print("=" * 50)
    
    # File paths
    validation_file = "/Users/jeremyj/Documents/source/repos/syntra/04_consensus_validation/documentation_run/validation_report_20250710_204452.json"
    consensus_file = "/Users/jeremyj/Documents/source/repos/syntra/03_consensus_benchmarks/documentation_run/consensus_reports/consensus_report_final.json"
    test_results_dir = "/Users/jeremyj/Documents/source/repos/syntra/02_test_attempts/documentation_run"
    
    # Load data
    print("📂 Loading data files...")
    validation_report = load_json(validation_file)
    consensus_report = load_json(consensus_file)
    
    # Extract correct answers for individual performance analysis
    correct_answers = {}
    for question in validation_report['questions']:
        correct_answers[question['question_number']] = question['correct_answer']
    
    # Get questions where consensus was wrong
    wrong_questions = get_wrong_consensus_questions(validation_report)
    print(f"❌ Found {len(wrong_questions)} questions where consensus was wrong")
    print(f"   Questions: {sorted(wrong_questions)}")
    
    # Analyze consensus independence
    print("\n🎯 Analyzing consensus independence...")
    model_independence = analyze_consensus_voting(consensus_report, wrong_questions, validation_report)
    
    # Get individual performance
    print("📊 Analyzing individual performance...")
    individual_performance = get_individual_performance(test_results_dir, correct_answers)
    
    # Combine results and generate report
    print("\n" + "=" * 70)
    print("🏆 MODEL CONSENSUS INDEPENDENCE ANALYSIS RESULTS")
    print("=" * 70)
    
    # Sort models by independence score
    sorted_models = sorted(model_independence.items(), 
                          key=lambda x: x[1]['independence_score'], 
                          reverse=True)
    
    print(f"\n📈 TOP PERFORMERS (Independence Score = Correct when consensus wrong / Total wrong consensus questions)")
    print(f"   Total questions where consensus was wrong: {len(wrong_questions)}")
    print("-" * 70)
    
    for i, (model, stats) in enumerate(sorted_models, 1):
        independence_score = stats['independence_score']
        correct_count = stats['correct_when_consensus_wrong']
        
        # Get individual performance if available
        individual_acc = individual_performance.get(model, {}).get('accuracy', 0.0)
        
        print(f"{i:2d}. {model}")
        print(f"    🎯 Independence Score: {independence_score:.3f} ({correct_count}/{len(wrong_questions)})")
        print(f"    📊 Individual Accuracy: {individual_acc:.3f}")
        print(f"    🔄 Consensus Resistance: {correct_count} times voted correctly vs wrong consensus")
        
        if stats['correct_votes_details']:
            print(f"    ✅ Correct votes on questions: {[d['question'] for d in stats['correct_votes_details'][:5]]}{'...' if len(stats['correct_votes_details']) > 5 else ''}")
        print()
    
    # Detailed breakdown of wrong consensus questions
    print("\n📋 DETAILED BREAKDOWN OF WRONG CONSENSUS QUESTIONS")
    print("-" * 70)
    
    for question in consensus_report['questions']:
        if question['question_number'] in wrong_questions:
            correct_answer = correct_answers[question['question_number']]
            consensus_choice = question['final_consensus_choice']
            consensus_pct = question['final_consensus_percentage']
            
            print(f"\n❌ Question {question['question_number']}: {question.get('question_type', 'Unknown')}")
            print(f"   Correct Answer: {correct_answer} | Consensus Choice: {consensus_choice} ({consensus_pct:.1f}%)")
            
            # Show who voted correctly in the final round
            if 'vote_history' in question and question['vote_history']:
                final_round = question['vote_history'][-1]
                if correct_answer in final_round['votes']:
                    correct_voters = final_round['votes'][correct_answer]
                    print(f"   🎯 Models that voted CORRECTLY: {', '.join(correct_voters)}")
                else:
                    print(f"   😞 No models voted correctly in final round")
    
    # Calculate composite scores
    print("\n" + "=" * 70)
    print("🎖️ COMPOSITE RANKING (Independence + Individual Accuracy)")
    print("=" * 70)
    
    composite_scores = []
    for model, independence_stats in model_independence.items():
        individual_acc = individual_performance.get(model, {}).get('accuracy', 0.0)
        independence_score = independence_stats['independence_score']
        
        # Composite score: 60% independence, 40% individual accuracy
        # This weights independence higher since it's the main focus
        composite_score = (0.6 * independence_score) + (0.4 * individual_acc)
        
        composite_scores.append({
            'model': model,
            'composite_score': composite_score,
            'independence_score': independence_score,
            'individual_accuracy': individual_acc,
            'correct_when_wrong': independence_stats['correct_when_consensus_wrong']
        })
    
    # Sort by composite score
    composite_scores.sort(key=lambda x: x['composite_score'], reverse=True)
    
    print("Ranking based on 60% Independence Score + 40% Individual Accuracy:")
    print("-" * 70)
    
    for i, score_data in enumerate(composite_scores, 1):
        model = score_data['model']
        composite = score_data['composite_score']
        independence = score_data['independence_score']
        accuracy = score_data['individual_accuracy']
        correct_count = score_data['correct_when_wrong']
        
        print(f"{i:2d}. {model}")
        print(f"    🏆 Composite Score: {composite:.3f}")
        print(f"    🎯 Independence: {independence:.3f} ({correct_count}/26 correct vs wrong consensus)")
        print(f"    📊 Individual Accuracy: {accuracy:.3f}")
        print()
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("📊 SUMMARY STATISTICS")
    print("=" * 70)
    
    if model_independence:
        avg_independence = sum(stats['independence_score'] for stats in model_independence.values()) / len(model_independence)
        best_independence_model = max(model_independence.items(), key=lambda x: x[1]['independence_score'])
        best_composite_model = composite_scores[0]
        
        print(f"Average Independence Score: {avg_independence:.3f}")
        print(f"Best Independent Model: {best_independence_model[0]} (Score: {best_independence_model[1]['independence_score']:.3f})")
        print(f"Best Composite Model: {best_composite_model['model']} (Score: {best_composite_model['composite_score']:.3f})")
        
        # Models with high independence (>0.1 since max is 0.192)
        high_independence = [name for name, stats in model_independence.items() 
                           if stats['independence_score'] > 0.1]
        print(f"Models with >10% independence: {len(high_independence)}")
        if high_independence:
            print(f"   {', '.join(high_independence)}")
        
        # Key insights
        print(f"\n🔍 KEY INSIGHTS:")
        print(f"• Out of 26 wrong consensus decisions, only {len([q for q in wrong_questions if any(stats['correct_when_consensus_wrong'] > 0 for stats in model_independence.values())])} had any model vote correctly")
        
        # Questions where NO model voted correctly
        no_correct_questions = []
        for question in consensus_report['questions']:
            if question['question_number'] in wrong_questions:
                correct_answer = correct_answers[question['question_number']]
                if 'vote_history' in question and question['vote_history']:
                    final_round = question['vote_history'][-1]
                    if correct_answer not in final_round['votes'] or not final_round['votes'][correct_answer]:
                        no_correct_questions.append(question['question_number'])
        
        print(f"• {len(no_correct_questions)} questions had NO models vote correctly: {sorted(no_correct_questions)}")
        print(f"• This suggests strong groupthink on questions: {', '.join(map(str, sorted(no_correct_questions)[:5]))}{'...' if len(no_correct_questions) > 5 else ''}")

if __name__ == "__main__":
    main()