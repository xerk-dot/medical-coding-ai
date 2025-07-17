"""
Multi-Round Consensus Analyzer for Medical Board Results

Implements iterative voting with thresholds:
- First vote: 70% agreement required
- Second/subsequent votes: 80% agreement required

Automatically runs multiple rounds until all questions reach consensus.
"""
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass

# Add medical_board to path for direct imports
sys.path.append("../01_medical_board")
from medical_test import MedicalBoardTest

@dataclass
class QuestionConsensus:
    """Consensus result for a single question"""
    question_number: int
    question: str
    question_type: str
    choices: Dict[str, str]
    votes: Dict[str, List[str]]  # choice -> list of doctor names
    vote_counts: Dict[str, int]
    total_votes: int
    consensus_choice: Optional[str]
    consensus_percentage: float
    consensus_achieved: bool
    threshold_used: float
    vote_round: int

class ConsensusAnalyzer:
    """Multi-round consensus analyzer for AI medical board decisions"""
    
    def __init__(self, mode: str = "all", auto_continue: bool = False):
        self.mode = mode
        self.auto_continue = auto_continue
        self.results_dir = "../02_test_attempts"
        self.threshold_first = 0.7  # 70% consensus needed for first round
        self.threshold_subsequent = 0.8  # 80% consensus needed for subsequent rounds
        self.consensus_reports_dir = "./consensus_reports"
        self.questions_file = "../00_question_banks/final_questions.json"
        self.max_rounds = 5
        
        # Create directories
        os.makedirs(self.consensus_reports_dir, exist_ok=True)
    
    def get_available_test_folders(self) -> List[str]:
        """Get list of all available test folders sorted by date"""
        if not os.path.exists(self.results_dir):
            return []
            
        test_folders = []
        for item in os.listdir(self.results_dir):
            if os.path.isdir(os.path.join(self.results_dir, item)) and item.startswith("test_"):
                test_folders.append(item)
        
        return sorted(test_folders, reverse=True)
    
    def load_all_questions(self) -> List[Dict]:
        """Load all questions from the question bank"""
        with open(self.questions_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_test_results(self, test_folder: str) -> List[Dict]:
        """Load test results from a specific test folder"""
        test_path = os.path.join(self.results_dir, test_folder)
        if not os.path.exists(test_path):
            print(f"❌ Test folder not found: {test_path}")
            return []
        
        results = []
        for filename in os.listdir(test_path):
            if filename.endswith('.json'):
                file_path = os.path.join(test_path, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Filter by mode if needed
                    is_enhanced = data.get("use_embeddings", False) or "_enhanced_" in filename
                    
                    if self.mode == "vanilla" and is_enhanced:
                        continue
                    elif self.mode == "enhanced" and not is_enhanced:
                        continue
                    
                    results.append(data)
                except Exception as e:
                    print(f"⚠️  Error loading {file_path}: {e}")
        
        return results
    
    def create_questions_with_context(self, question_numbers: List[int], 
                                    previous_consensus: List[QuestionConsensus]) -> str:
        """Create a temporary questions file with previous vote context"""
        all_questions = self.load_all_questions()
        
        # Create temporary directory for this round
        temp_dir = os.path.join(os.getcwd(), "temp_consensus")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Filter questions and add context
        filtered_questions = []
        for q in all_questions:
            if q["question_number"] in question_numbers:
                # Find previous consensus for this question
                prev_result = next((r for r in previous_consensus if r.question_number == q["question_number"]), None)
                
                if prev_result:
                    # Add previous vote context
                    context = f"\n\n--- Previous Vote Results ---\n"
                    context += f"Consensus threshold not met. Previous votes:\n"
                    
                    for choice, doctors in sorted(prev_result.votes.items()):
                        percentage = (len(doctors) / prev_result.total_votes) * 100
                        context += f"• Choice {choice}: {len(doctors)} votes ({percentage:.1f}%) - {', '.join(doctors[:3])}"
                        if len(doctors) > 3:
                            context += f" and {len(doctors)-3} others"
                        context += "\n"
                    
                    context += f"\nPlease reconsider your answer based on the voting pattern above."
                    
                    # Create new question with context
                    new_question = q.copy()
                    new_question["question"] = q["question"] + context
                    filtered_questions.append(new_question)
                else:
                    filtered_questions.append(q)
        
        # Save to temporary file
        temp_file = os.path.join(temp_dir, "consensus_questions.json")
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_questions, f, indent=2)
        
        return temp_file
    
    def run_medical_tests_for_questions(self, questions_file: str, round_num: int) -> Optional[str]:
        """Run medical tests for specific questions and return test folder"""
        print(f"\n🤖 Running medical tests for round {round_num}...")
        
        # Load and display questions info
        questions_data = json.load(open(questions_file))
        num_questions = len(questions_data)
        question_numbers = [q.get("question_number", i+1) for i, q in enumerate(questions_data)]
        
        print(f"📋 Testing {num_questions} questions with all AI models...")
        print(f"   Questions: {', '.join(map(str, sorted(question_numbers)))}")
        
        # Create medical test instance
        use_embeddings = (self.mode == "enhanced")
        test = MedicalBoardTest(use_embeddings=use_embeddings, max_workers=2, questions_file=questions_file)
        
        # Get all doctor keys (excluding problematic models)
        from config import AI_DOCTORS
        all_doctor_keys = [key for key in AI_DOCTORS.keys() if key != "grok_4"]
        
        print(f"   🔄 Starting medical tests with {len(all_doctor_keys)} AI models...")
        start_time = time.time()
        
        # Run tests for all doctors
        try:
            test.run_multiple_doctors(all_doctor_keys, max_questions=None, max_concurrent_agents=4, parallel=True)
            
            # Find the latest test folder
            test_folders = sorted([f for f in os.listdir(self.results_dir) if f.startswith("test_")], reverse=True)
            if test_folders:
                latest_folder = test_folders[0]
                elapsed_time = time.time() - start_time
                print(f"✅ Tests completed in {elapsed_time:.1f}s. Results in: {latest_folder}")
                if num_questions > 0:
                    print(f"   ⏱️  Average: {elapsed_time/num_questions:.1f}s per question")
                return latest_folder
            else:
                print(f"❌ No test results found")
                return None
                
        except Exception as e:
            print(f"❌ Error running medical tests: {e}")
            return None
    
    def analyze_consensus_results(self, test_folder: str, round_num: int) -> List[QuestionConsensus]:
        """Analyze consensus for questions from test results"""
        results = self.load_test_results(test_folder)
        
        if not results:
            print(f"❌ No results found in {test_folder}")
            return []
        
        print(f"\n📊 Analyzing results from {len(results)} AI models:")
        for result in results:
            doctor_name = result.get("doctor_name", "Unknown")
            is_enhanced = result.get("use_embeddings", False)
            mode_suffix = " (Enhanced)" if is_enhanced else " (Vanilla)"
            print(f"   • {doctor_name}{mode_suffix}")
        
        # Determine threshold
        threshold = self.threshold_first if round_num == 1 else self.threshold_subsequent
        print(f"📏 Using {threshold * 100:.0f}% consensus threshold for round {round_num}")
        
        # Group responses by question number
        question_responses = defaultdict(list)
        
        for test_session in results:
            doctor_name = test_session["doctor_name"]
            
            for result in test_session.get("results", []):
                question_num = result["question_number"]
                
                if result["selected_answer"]:
                    # Clean the question text (remove previous context if any)
                    clean_question = result["question"].split("\n\n--- Previous Vote Results ---")[0]
                    
                    question_responses[question_num].append({
                        "doctor": doctor_name,
                        "answer": result["selected_answer"],
                        "reasoning": result.get("reasoning", ""),
                        "question": clean_question,
                        "question_type": result.get("question_type", "other"),
                        "choices": result["choices"]
                    })
        
        # Analyze consensus
        consensus_results = []
        
        for question_num in sorted(question_responses.keys()):
            responses = question_responses[question_num]
            
            if not responses:
                continue
            
            # Count votes
            vote_counts = Counter()
            votes_by_choice = defaultdict(list)
            
            for response in responses:
                choice = response["answer"]
                doctor = response["doctor"]
                vote_counts[choice] += 1
                votes_by_choice[choice].append(doctor)
            
            total_votes = len(responses)
            
            # Find consensus
            if vote_counts:
                consensus_choice = vote_counts.most_common(1)[0][0]
                consensus_count = vote_counts[consensus_choice]
                consensus_percentage = (consensus_count / total_votes) * 100
                consensus_achieved = consensus_percentage >= (threshold * 100)
            else:
                consensus_choice = None
                consensus_percentage = 0.0
                consensus_achieved = False
            
            # Create consensus result
            first_response = responses[0]
            consensus_result = QuestionConsensus(
                question_number=question_num,
                question=first_response["question"],
                question_type=first_response["question_type"],
                choices=first_response["choices"],
                votes=dict(votes_by_choice),
                vote_counts=dict(vote_counts),
                total_votes=total_votes,
                consensus_choice=consensus_choice,
                consensus_percentage=consensus_percentage,
                consensus_achieved=consensus_achieved,
                threshold_used=threshold,
                vote_round=round_num
            )
            
            consensus_results.append(consensus_result)
        
        return consensus_results
    
    def merge_consensus_results(self, all_results: List[QuestionConsensus], 
                              new_results: List[QuestionConsensus]) -> List[QuestionConsensus]:
        """Merge new consensus results with existing ones"""
        result_map = {r.question_number: r for r in all_results}
        
        # Update with new results
        for new_result in new_results:
            result_map[new_result.question_number] = new_result
        
        return sorted(result_map.values(), key=lambda x: x.question_number)
    
    def save_vote_report(self, results: List[QuestionConsensus], round_num: int, 
                        vote_history: Dict[int, List[Dict]]) -> str:
        """Save vote-specific report with all questions"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"consensus_report_vote_{round_num:02d}_{timestamp}.json"
        filepath = os.path.join(self.consensus_reports_dir, filename)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "vote_round": round_num,
            "mode": self.mode,
            "summary": {
                "total_questions": len(results),
                "consensus_achieved": sum(1 for r in results if r.consensus_achieved),
                "threshold_used": self.threshold_first if round_num == 1 else self.threshold_subsequent
            },
            "questions": []
        }
        
        for result in results:
            question_data = {
                "question_number": result.question_number,
                "question": result.question,
                "question_type": result.question_type,
                "choices": result.choices,
                "votes": result.votes,
                "vote_counts": result.vote_counts,
                "total_votes": result.total_votes,
                "consensus_choice": result.consensus_choice,
                "consensus_percentage": result.consensus_percentage,
                "consensus_achieved": result.consensus_achieved,
                "threshold_used": result.threshold_used,
                "vote_round": result.vote_round,
                "vote_history": vote_history.get(result.question_number, [])
            }
            report["questions"].append(question_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Vote report saved: {filename}")
        return filepath
    
    def save_final_report(self, all_results: List[QuestionConsensus], total_rounds: int, 
                         vote_history: Dict[int, List[Dict]]) -> str:
        """Save final consensus report with ALL questions from the original question bank"""
        filepath = os.path.join(self.consensus_reports_dir, "consensus_report_final.json")
        
        # Load ALL original questions to ensure complete coverage
        all_original_questions = self.load_all_questions()
        
        # Create a map of results by question number for quick lookup
        results_map = {r.question_number: r for r in all_results}
        
        # Calculate statistics
        questions_by_rounds = defaultdict(int)
        for q_num, history in vote_history.items():
            rounds_needed = len(history)
            questions_by_rounds[rounds_needed] += 1
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_rounds": total_rounds,
            "mode": self.mode,
            "summary": {
                "total_questions": len(all_results),
                "consensus_achieved": sum(1 for r in all_results if r.consensus_achieved),
                "questions_by_rounds_needed": dict(questions_by_rounds),
                "average_rounds_needed": sum(len(h) for h in vote_history.values()) / len(vote_history) if vote_history else 1
            },
            "questions": []
        }
        
        # Include only the questions that were actually tested
        for result in all_results:
            question_data = {
                "question_number": result.question_number,
                "question": result.question,
                "question_type": result.question_type,
                "choices": result.choices,
                "final_consensus_choice": result.consensus_choice,
                "final_consensus_percentage": result.consensus_percentage,
                "consensus_achieved": result.consensus_achieved,
                "rounds_needed": len(vote_history.get(result.question_number, [])),
                "vote_history": vote_history.get(result.question_number, [])
            }
            report["questions"].append(question_data)
        
        # Sort questions by question number
        report["questions"].sort(key=lambda x: x["question_number"])
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Final consensus report saved with {len(report['questions'])} tested questions: {filepath}")
        return filepath
    
    def run_consensus_analysis(self, initial_test_folder: Optional[str] = None):
        """Run complete multi-round consensus analysis"""
        print(f"🎯 Starting Multi-Round Consensus Analysis")
        print(f"📊 Mode: {self.mode}")
        print("=" * 60)
        
        # Get initial test folder
        if not initial_test_folder:
            test_folders = self.get_available_test_folders()
            if not test_folders:
                print("❌ No test folders found")
                return
            initial_test_folder = test_folders[0]
        
        print(f"📁 Starting from test folder: {initial_test_folder}")
        
        # Initialize tracking
        all_results = []
        vote_history = defaultdict(list)
        round_num = 0
        
        # First round - analyze existing results
        round_num = 1
        print(f"\n{'='*60}")
        print(f"🗳️  ROUND {round_num} (Threshold: {self.threshold_first * 100:.0f}%)")
        print(f"📋 Analyzing existing test results...")
        
        consensus_results = self.analyze_consensus_results(initial_test_folder, round_num)
        
        if not consensus_results:
            print("❌ No consensus results found")
            return
        
        # Update tracking
        all_results = consensus_results
        for result in consensus_results:
            vote_record = {
                "round": round_num,
                "test_folder": initial_test_folder,
                "votes": result.votes,
                "vote_counts": result.vote_counts,
                "consensus_choice": result.consensus_choice,
                "consensus_percentage": result.consensus_percentage,
                "consensus_achieved": result.consensus_achieved,
                "threshold_used": result.threshold_used
            }
            vote_history[result.question_number].append(vote_record)
        
        # Save first vote report
        self.save_vote_report(all_results, round_num, dict(vote_history))
        
        # Check status and continue rounds if needed
        while round_num < self.max_rounds:
            # Find questions that still need consensus
            failed_questions = [r.question_number for r in all_results if not r.consensus_achieved]
            
            # Print round summary
            consensus_achieved = sum(1 for r in all_results if r.consensus_achieved)
            print(f"\n✅ Round {round_num} Results: {consensus_achieved}/{len(all_results)} questions reached consensus")
            
            if not failed_questions:
                print(f"🎉 All questions have reached consensus!")
                break
            
            print(f"❌ {len(failed_questions)} questions need another round")
            if len(failed_questions) <= 20:
                print(f"   Questions: {', '.join(map(str, sorted(failed_questions)))}")
            else:
                print(f"   Questions: {', '.join(map(str, sorted(failed_questions[:10])))}, ... and {len(failed_questions)-10} more")
            
            # Ask user if they want to continue (unless auto_continue is enabled)
            if round_num < self.max_rounds:
                if self.auto_continue:
                    print(f"\nAuto-continuing to round {round_num + 1}...")
                else:
                    response = input(f"\nContinue to round {round_num + 1}? (y/n): ")
                    if response.lower() != 'y':
                        print("Stopping consensus analysis")
                        break
            
            # Prepare next round
            round_num += 1
            threshold = self.threshold_subsequent
            
            print(f"\n{'='*60}")
            print(f"🗳️  ROUND {round_num} (Threshold: {threshold * 100:.0f}%)")
            print(f"📝 Creating questions with previous vote context...")
            
            # Create questions file with previous vote context
            questions_file = self.create_questions_with_context(failed_questions, all_results)
            
            # Run medical tests for failed questions
            test_folder = self.run_medical_tests_for_questions(questions_file, round_num)
            if not test_folder:
                print("❌ Failed to run medical tests")
                break
            
            # Analyze new results
            print(f"\n🔍 Analyzing round {round_num} results...")
            new_consensus_results = self.analyze_consensus_results(test_folder, round_num)
            
            # Update tracking
            for result in new_consensus_results:
                vote_record = {
                    "round": round_num,
                    "test_folder": test_folder,
                    "votes": result.votes,
                    "vote_counts": result.vote_counts,
                    "consensus_choice": result.consensus_choice,
                    "consensus_percentage": result.consensus_percentage,
                    "consensus_achieved": result.consensus_achieved,
                    "threshold_used": result.threshold_used
                }
                vote_history[result.question_number].append(vote_record)
            
            # Merge results
            all_results = self.merge_consensus_results(all_results, new_consensus_results)
            
            # Save vote report
            self.save_vote_report(all_results, round_num, dict(vote_history))
        
        # Save final report
        self.save_final_report(all_results, round_num, dict(vote_history))
        
        # Print final summary
        print(f"\n{'='*60}")
        print(f"🏁 CONSENSUS ANALYSIS COMPLETE")
        print(f"{'='*60}")
        final_consensus = sum(1 for r in all_results if r.consensus_achieved)
        print(f"Total Questions: {len(all_results)}")
        print(f"Consensus Achieved: {final_consensus}/{len(all_results)} ({final_consensus/len(all_results)*100:.1f}%)")
        print(f"Total Rounds: {round_num}")
        
        # Show distribution of rounds needed
        rounds_distribution = defaultdict(int)
        for history in vote_history.values():
            rounds_distribution[len(history)] += 1
        
        print(f"\nRounds needed per question:")
        for rounds, count in sorted(rounds_distribution.items()):
            print(f"  {rounds} round{'s' if rounds > 1 else ''}: {count} questions")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Round Consensus Analyzer")
    parser.add_argument("--mode", choices=["vanilla", "enhanced", "all"], default="all",
                       help="Analysis mode")
    parser.add_argument("--test", type=str, default=None,
                       help="Initial test folder to start from")
    parser.add_argument("--list", action="store_true",
                       help="List available test folders")
    parser.add_argument("--auto", action="store_true",
                       help="Auto-continue through all rounds without user input")
    
    args = parser.parse_args()
    
    analyzer = ConsensusAnalyzer(mode=args.mode, auto_continue=args.auto)
    
    if args.list:
        available_folders = analyzer.get_available_test_folders()
        if available_folders:
            print("📂 Available test folders:")
            for i, folder in enumerate(available_folders[:20]):
                print(f"  {i+1}. {folder}")
            if len(available_folders) > 20:
                print(f"  ... and {len(available_folders) - 20} more")
        else:
            print("❌ No test folders found")
        return
    
    analyzer.run_consensus_analysis(args.test)

if __name__ == "__main__":
    main()