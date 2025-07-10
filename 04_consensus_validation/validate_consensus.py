#!/usr/bin/env python3
"""
Consensus Validation Script

This script compares the latest consensus report with the official answer key
to determine how accurate the AI consensus is compared to the ground truth.
"""

import json
import os
import glob
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class ValidationResult:
    """Result of validating consensus against answer key"""
    question_number: int
    question_type: str
    correct_answer: str
    consensus_choice: Optional[str]
    consensus_achieved: bool
    consensus_percentage: float
    is_consensus_correct: bool
    total_votes: int
    vote_breakdown: Dict[str, int]

class ConsensusValidator:
    """Validates consensus results against the official answer key"""
    
    def __init__(self):
        self.answer_key_file = "../00_question_banks/test_1/test_1_answers.json"
        self.consensus_reports_dir = "../03_consensus_benchmarks/consensus_reports"
        self.questions_file = "../00_question_banks/test_1/test_1_questions.json"
    
    def load_answer_key(self) -> Dict[int, str]:
        """Load the official answer key"""
        try:
            with open(self.answer_key_file, 'r', encoding='utf-8') as f:
                answers = json.load(f)
            
            answer_key = {}
            for item in answers:
                answer_key[item["question_number"]] = item["correct_answer"]
            
            print(f"✅ Loaded answer key with {len(answer_key)} questions")
            return answer_key
            
        except FileNotFoundError:
            print(f"❌ Answer key not found: {self.answer_key_file}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in answer key: {e}")
            return {}
    
    def load_question_types(self) -> Dict[int, str]:
        """Load question types from the questions file"""
        try:
            with open(self.questions_file, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            
            question_types = {}
            for q in questions:
                question_types[q["question_number"]] = q.get("question_type", "other")
            
            print(f"✅ Loaded question types for {len(question_types)} questions")
            return question_types
            
        except FileNotFoundError:
            print(f"❌ Questions file not found: {self.questions_file}")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in questions file: {e}")
            return {}
    
    def get_available_consensus_reports(self) -> List[str]:
        """Get list of all available consensus reports sorted by date"""
        pattern = os.path.join(self.consensus_reports_dir, "consensus_report_*.json")
        files = glob.glob(pattern)
        # Sort by filename (which includes timestamp) descending
        return sorted(files, reverse=True)
    
    def get_consensus_report(self, report_filename: Optional[str] = None) -> Optional[str]:
        """Get consensus report path - either specified or latest"""
        available_reports = self.get_available_consensus_reports()
        
        if not available_reports:
            print(f"❌ No consensus reports found in {self.consensus_reports_dir}")
            return None
        
        # If specific report requested, validate it exists
        if report_filename:
            # Handle both full path and just filename
            if os.path.exists(report_filename):
                return report_filename
            
            # Try in consensus reports directory
            full_path = os.path.join(self.consensus_reports_dir, report_filename)
            if os.path.exists(full_path):
                print(f"📊 Using consensus report: {report_filename}")
                return full_path
            
            print(f"❌ Consensus report '{report_filename}' not found")
            print(f"Available reports (showing first 10):")
            for report in available_reports[:10]:
                print(f"  - {os.path.basename(report)}")
            return None
        
        # Use latest report
        latest_file = available_reports[0]
        print(f"📊 Using latest consensus report: {os.path.basename(latest_file)}")
        return latest_file
    
    def load_consensus_report(self, filepath: str) -> Optional[Dict]:
        """Load a consensus report"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            print(f"✅ Loaded consensus report with {len(report.get('questions', []))} questions")
            return report
            
        except FileNotFoundError:
            print(f"❌ Consensus report not found: {filepath}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in consensus report: {e}")
            return None
    
    def validate_consensus(self, report_filename: Optional[str] = None) -> List[ValidationResult]:
        """Validate a consensus report against the answer key
        
        Args:
            report_filename: Specific consensus report to validate (uses latest if None)
        """
        # Load data
        answer_key = self.load_answer_key()
        question_types = self.load_question_types()
        
        if not answer_key:
            print("❌ Cannot validate without answer key")
            return []
        
        # Get consensus report
        report_file = self.get_consensus_report(report_filename)
        if not report_file:
            print("❌ Cannot validate without consensus report")
            return []
        
        consensus_report = self.load_consensus_report(report_file)
        if not consensus_report:
            print("❌ Cannot validate without valid consensus report")
            return []
        
        # Validate each question
        validation_results = []
        
        for question_data in consensus_report.get("questions", []):
            question_num = question_data["question_number"]
            correct_answer = answer_key.get(question_num)
            
            if not correct_answer:
                print(f"⚠️  No answer key found for question {question_num}")
                continue
            
            consensus_choice = question_data.get("consensus_choice")
            consensus_achieved = question_data.get("consensus_achieved", False)
            consensus_percentage = question_data.get("consensus_percentage", 0.0)
            
            # Determine if consensus is correct
            is_consensus_correct = False
            if consensus_achieved and consensus_choice:
                is_consensus_correct = consensus_choice == correct_answer
            
            result = ValidationResult(
                question_number=question_num,
                question_type=question_types.get(question_num, "other"),
                correct_answer=correct_answer,
                consensus_choice=consensus_choice,
                consensus_achieved=consensus_achieved,
                consensus_percentage=consensus_percentage,
                is_consensus_correct=is_consensus_correct,
                total_votes=question_data.get("total_votes", 0),
                vote_breakdown=question_data.get("vote_counts", {})
            )
            
            validation_results.append(result)
        
        return validation_results
    
    def print_model_success_failure_summary(self, results: List[ValidationResult]):
        """Print individual model success/failure statistics"""
        print(f"\n📊 INDIVIDUAL MODEL SUCCESS/FAILURE BREAKDOWN")
        print("=" * 80)
        
        # Track each model's performance on each question
        model_stats = defaultdict(lambda: {"correct": 0, "incorrect": 0, "total": 0})
        
        # Get the answer key for comparison
        answer_key = self.load_answer_key()
        
        # Process each question to see how each model performed
        for result in results:
            question_num = result.question_number
            correct_answer = answer_key.get(question_num)
            
            if not correct_answer:
                continue
            
            # Check each model's vote for this question
            if hasattr(result, 'votes_by_doctor') and result.votes_by_doctor:
                for doctor_name, votes in result.votes_by_doctor.items():
                    if votes:  # If the doctor voted
                        model_stats[doctor_name]["total"] += 1
                        # Take the first vote if multiple (shouldn't happen but just in case)
                        doctor_vote = votes[0] if isinstance(votes, list) else votes
                        
                        if doctor_vote == correct_answer:
                            model_stats[doctor_name]["correct"] += 1
                        else:
                            model_stats[doctor_name]["incorrect"] += 1
        
        # If we don't have votes_by_doctor, fall back to loading individual test results
        if not model_stats:
            print("⚠️  No individual vote data found in consensus report")
            print("   Loading individual test results for model performance...")
            
            # Load individual test results
            individual_results = self.load_individual_test_results()
            
            for model_name, test_session in individual_results.items():
                doctor_name = test_session.get("doctor_name", model_name)
                test_results = test_session.get("results", [])
                
                for test_result in test_results:
                    if test_result.get("success") and test_result.get("selected_answer"):
                        question_num = test_result["question_number"]
                        selected_answer = test_result["selected_answer"]
                        correct_answer = answer_key.get(question_num)
                        
                        if correct_answer:
                            model_stats[doctor_name]["total"] += 1
                            if selected_answer == correct_answer:
                                model_stats[doctor_name]["correct"] += 1
                            else:
                                model_stats[doctor_name]["incorrect"] += 1
        
        # Sort models by accuracy
        sorted_models = sorted(model_stats.items(), 
                             key=lambda x: (x[1]["correct"] / x[1]["total"]) if x[1]["total"] > 0 else 0, 
                             reverse=True)
        
        print(f"{'Model Name':<35} {'Correct':<8} {'Incorrect':<10} {'Total':<8} {'Accuracy':<10}")
        print("-" * 80)
        
        for model_name, stats in sorted_models:
            if stats["total"] > 0:
                accuracy = (stats["correct"] / stats["total"]) * 100
                print(f"{model_name:<35} {stats['correct']:<8} {stats['incorrect']:<10} {stats['total']:<8} {accuracy:<10.1f}%")
        
        # Show summary statistics
        if sorted_models:
            print(f"\n📈 Summary Statistics:")
            total_models = len([m for m in sorted_models if m[1]["total"] > 0])
            best_model = sorted_models[0] if sorted_models else None
            worst_model = sorted_models[-1] if sorted_models else None
            
            print(f"   Total Active Models: {total_models}")
            if best_model:
                best_accuracy = (best_model[1]["correct"] / best_model[1]["total"]) * 100
                print(f"   🏆 Best Model: {best_model[0]} ({best_accuracy:.1f}%)")
            if worst_model and worst_model != best_model:
                worst_accuracy = (worst_model[1]["correct"] / worst_model[1]["total"]) * 100
                print(f"   🔻 Worst Model: {worst_model[0]} ({worst_accuracy:.1f}%)")
            
            # Calculate average accuracy
            total_correct = sum(stats["correct"] for _, stats in sorted_models)
            total_answered = sum(stats["total"] for _, stats in sorted_models)
            if total_answered > 0:
                avg_accuracy = (total_correct / total_answered) * 100
                print(f"   📊 Average Accuracy: {avg_accuracy:.1f}%")
    
    def load_individual_test_results(self) -> Dict[str, Dict]:
        """Load individual test results from all AI models"""
        02_test_attempts_dir = "../02_test_attempts"
        pattern = os.path.join(02_test_attempts_dir, "*.json")
        files = glob.glob(pattern)
        
        # Group files by model name and find the latest for each
        model_files = defaultdict(list)
        
        for file_path in files:
            filename = os.path.basename(file_path)
            # Skip consensus report files
            if filename.startswith('consensus_report') or filename.startswith('validation_report'):
                continue
                
            # Extract model name and timestamp from filename like "model_name_YYYYMMDD_HHMMSS.json"
            parts = filename.replace('.json', '').split('_')
            if len(parts) >= 3:
                # Model name is everything except the last two parts (date and time)
                model_name = '_'.join(parts[:-2])
                timestamp = '_'.join(parts[-2:])  # YYYYMMDD_HHMMSS
                model_files[model_name].append((timestamp, file_path))
        
        # Get the latest file for each model
        latest_results = {}
        for model_name, file_list in model_files.items():
            # Sort by timestamp (descending) and take the first (latest)
            file_list.sort(key=lambda x: x[0], reverse=True)
            latest_timestamp, latest_file = file_list[0]
            
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    latest_results[model_name] = data
            except Exception as e:
                print(f"❌ Error loading {latest_file}: {e}")
        
        return latest_results
    
    def print_validation_summary(self, results: List[ValidationResult]):
        """Print a comprehensive validation summary"""
        if not results:
            print("❌ No validation results to display")
            return
        
        total_questions = len(results)
        consensus_achieved = sum(1 for r in results if r.consensus_achieved)
        consensus_correct = sum(1 for r in results if r.is_consensus_correct)
        
        print(f"\n🎯 CONSENSUS VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Questions: {total_questions}")
        print(f"Consensus Achieved: {consensus_achieved}/{total_questions} ({consensus_achieved/total_questions*100:.1f}%)")
        print(f"Consensus Correct: {consensus_correct}/{consensus_achieved} ({consensus_correct/consensus_achieved*100:.1f}% of consensus)")
        print(f"Overall Accuracy: {consensus_correct}/{total_questions} ({consensus_correct/total_questions*100:.1f}% of all questions)")
        
        # Breakdown by question type
        type_stats = defaultdict(lambda: {"total": 0, "consensus": 0, "correct": 0})
        
        for result in results:
            q_type = result.question_type
            type_stats[q_type]["total"] += 1
            if result.consensus_achieved:
                type_stats[q_type]["consensus"] += 1
                if result.is_consensus_correct:
                    type_stats[q_type]["correct"] += 1
        
        print(f"\n📋 Accuracy by Question Type:")
        print(f"{'Type':<8} {'Total':<6} {'Consensus':<10} {'Correct':<8} {'Accuracy':<10}")
        print("-" * 50)
        
        for q_type in sorted(type_stats.keys()):
            stats = type_stats[q_type]
            consensus_rate = (stats["consensus"] / stats["total"]) * 100
            if stats["consensus"] > 0:
                accuracy_rate = (stats["correct"] / stats["consensus"]) * 100
            else:
                accuracy_rate = 0.0
            
            print(f"{q_type:<8} {stats['total']:<6} {stats['consensus']:<10} {stats['correct']:<8} {accuracy_rate:<10.1f}%")
        
        # Show incorrect consensus decisions
        incorrect_consensus = [r for r in results if r.consensus_achieved and not r.is_consensus_correct]
        
        if incorrect_consensus:
            print(f"\n❌ Incorrect Consensus Decisions ({len(incorrect_consensus)}):")
            for result in incorrect_consensus[:10]:  # Show first 10
                print(f"  Q{result.question_number}: Consensus={result.consensus_choice} "
                      f"({result.consensus_percentage:.1f}%), Correct={result.correct_answer}")
                
                # Show vote breakdown
                vote_summary = []
                for choice, count in sorted(result.vote_breakdown.items()):
                    marker = "✓" if choice == result.correct_answer else " "
                    vote_summary.append(f"{choice}:{count}{marker}")
                print(f"    Votes: {', '.join(vote_summary)}")
        
        # Show questions where consensus was achieved but wrong
        no_consensus_but_correct = []
        for result in results:
            if not result.consensus_achieved:
                # Check if the correct answer had the most votes
                if result.vote_breakdown:
                    most_voted = max(result.vote_breakdown.items(), key=lambda x: x[1])
                    if most_voted[0] == result.correct_answer:
                        no_consensus_but_correct.append(result)
        
        if no_consensus_but_correct:
            print(f"\n🤔 No Consensus but Correct Answer Led ({len(no_consensus_but_correct)}):")
            for result in no_consensus_but_correct[:5]:  # Show first 5
                correct_votes = result.vote_breakdown.get(result.correct_answer, 0)
                percentage = (correct_votes / result.total_votes) * 100
                print(f"  Q{result.question_number}: Correct answer {result.correct_answer} "
                      f"had {correct_votes}/{result.total_votes} votes ({percentage:.1f}%)")
    
    def save_validation_report(self, results: List[ValidationResult], filename: Optional[str] = None):
        """Save detailed validation report to JSON"""
        if not filename:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"validation_report_{timestamp}.json"
        
        # Calculate summary statistics
        total_questions = len(results)
        consensus_achieved = sum(1 for r in results if r.consensus_achieved)
        consensus_correct = sum(1 for r in results if r.is_consensus_correct)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_questions": total_questions,
                "consensus_achieved": consensus_achieved,
                "consensus_correct": consensus_correct,
                "consensus_accuracy": (consensus_correct / consensus_achieved * 100) if consensus_achieved > 0 else 0,
                "overall_accuracy": (consensus_correct / total_questions * 100) if total_questions > 0 else 0
            },
            "questions": []
        }
        
        for result in results:
            question_data = {
                "question_number": result.question_number,
                "question_type": result.question_type,
                "correct_answer": result.correct_answer,
                "consensus_choice": result.consensus_choice,
                "consensus_achieved": result.consensus_achieved,
                "consensus_percentage": result.consensus_percentage,
                "is_consensus_correct": result.is_consensus_correct,
                "total_votes": result.total_votes,
                "vote_breakdown": result.vote_breakdown
            }
            report["questions"].append(question_data)
        
        filepath = os.path.join(".", filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Validation report saved to: {filepath}")
        except Exception as e:
            print(f"\n❌ Error saving validation report: {e}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Medical Board Consensus Validator")
    parser.add_argument("--report", type=str, default=None,
                       help="Specific consensus report to validate (e.g., consensus_report_20250710_121105.json)")
    parser.add_argument("--list", action="store_true",
                       help="List available consensus reports")
    
    args = parser.parse_args()
    
    validator = ConsensusValidator()
    
    # Handle --list option
    if args.list:
        available_reports = validator.get_available_consensus_reports()
        if available_reports:
            print("📂 Available consensus reports:")
            for i, report in enumerate(available_reports[:20]):  # Show first 20
                print(f"  {i+1}. {os.path.basename(report)}")
            if len(available_reports) > 20:
                print(f"  ... and {len(available_reports) - 20} more")
        else:
            print("❌ No consensus reports found")
        return
    
    print("🔍 Consensus Validation Tool")
    print("Comparing AI consensus with official answer key...")
    print("=" * 60)
    
    # Validate consensus
    results = validator.validate_consensus(args.report)
    
    if not results:
        print("❌ No validation results to display")
        return
    
    # Print summary
    validator.print_validation_summary(results)
    
    # Print individual model success/failure breakdown
    validator.print_model_success_failure_summary(results)
    
    # Save detailed report
    validator.save_validation_report(results)
    
    print(f"\n✅ Validation complete!")

if __name__ == "__main__":
    main() 