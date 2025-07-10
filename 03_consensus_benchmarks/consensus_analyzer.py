"""
Consensus Analyzer for Medical Board Results

Implements the voting thresholds:
- First vote: 70% agreement required
- Second/subsequent votes: 85% agreement required
"""
import json
import os
import glob
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass

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


class ConsensusAnalyzer:
    """Analyzes consensus among AI doctors on medical coding questions"""
    
    def __init__(self, results_dir: str = "../02_test_attempts", mode: str = "all"):
        self.results_dir = results_dir
        self.mode = mode  # "vanilla", "enhanced", or "all"
        self.threshold_first = 0.7  # 70% consensus needed for first round
        self.threshold_subsequent = 0.8  # 80% consensus needed for subsequent rounds
        
    def get_available_test_folders(self) -> List[str]:
        """Get list of all available test folders sorted by date"""
        if not os.path.exists(self.results_dir):
            return []
            
        # Find all test_YYYYMMDD_HHMMSS folders
        test_folders = []
        for item in os.listdir(self.results_dir):
            if os.path.isdir(os.path.join(self.results_dir, item)) and item.startswith("test_"):
                test_folders.append(item)
        
        # Sort by timestamp (folder name) descending
        test_folders.sort(reverse=True)
        return test_folders
    
    def get_test_folder(self, test_folder_name: Optional[str] = None) -> Optional[str]:
        """Get test folder path - either specified or latest with matching files"""
        available_folders = self.get_available_test_folders()
        
        if not available_folders:
            print(f"❌ No test folders found in {self.results_dir}")
            return None
        
        # If specific folder requested, validate it exists
        if test_folder_name:
            if test_folder_name not in available_folders:
                print(f"❌ Test folder '{test_folder_name}' not found")
                print(f"Available folders: {', '.join(available_folders[:5])}...")
                return None
            return os.path.join(self.results_dir, test_folder_name)
        
        # Otherwise find latest folder with matching files
        for folder_name in available_folders:
            folder_path = os.path.join(self.results_dir, folder_name)
            
            # Check if this folder has files matching our mode
            has_matching_files = False
            for filename in os.listdir(folder_path):
                if filename.endswith('.json'):
                    is_enhanced = "_enhanced_" in filename
                    
                    if self.mode == "vanilla" and not is_enhanced:
                        has_matching_files = True
                        break
                    elif self.mode == "enhanced" and is_enhanced:
                        has_matching_files = True
                        break
                    elif self.mode == "all":
                        has_matching_files = True
                        break
            
            if has_matching_files:
                print(f"📁 Using test folder with {self.mode} results: {folder_name}")
                return folder_path
                
        print(f"❌ No test folders found containing {self.mode} results")
        return None
    
    def load_all_results(self, test_folder_name: Optional[str] = None) -> List[Dict]:
        """Load all test results from specified or latest test folder, filtered by mode"""
        # Get the test folder
        test_folder = self.get_test_folder(test_folder_name)
        if not test_folder:
            print("❌ No valid test folder found")
            return []
        
        # Find all JSON files in the test folder
        json_files = []
        if os.path.exists(test_folder):
            for filename in os.listdir(test_folder):
                if filename.endswith('.json'):
                    json_files.append(os.path.join(test_folder, filename))
        
        if not json_files:
            print(f"❌ No JSON files found in {test_folder}")
            return []
        
        # Filter files based on mode
        filtered_files = []
        for file_path in json_files:
            filename = os.path.basename(file_path)
            is_enhanced = "_enhanced_" in filename
            
            if self.mode == "vanilla" and not is_enhanced:
                filtered_files.append(file_path)
            elif self.mode == "enhanced" and is_enhanced:
                filtered_files.append(file_path)
            elif self.mode == "all":
                filtered_files.append(file_path)
        
        if not filtered_files:
            print(f"❌ No files found matching mode '{self.mode}' in {test_folder}")
            return []
        
        # Load and parse JSON files
        results = []
        models_found = set()
        
        for file_path in filtered_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract model info for tracking
                model_name = data.get("doctor_name", "Unknown")
                model_id = data.get("model_id", "unknown")
                is_enhanced = data.get("use_embeddings", False)
                
                mode_suffix = " (Enhanced)" if is_enhanced else " (Vanilla)"
                display_name = f"{model_name}{mode_suffix}"
                
                models_found.add(display_name)
                results.append(data)
                
                filename = os.path.basename(file_path)
                print(f"Using latest result for {model_name}: {filename}")
                
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"⚠️  Error loading {file_path}: {e}")
                continue
        
        print(f"Loaded {len(results)} latest test result files from {len(models_found)} models ({self.mode} mode)")
        return results
    
    def analyze_consensus(self, round_number: int = 1, test_folder_name: Optional[str] = None) -> List[QuestionConsensus]:
        """
        Analyze consensus across all AI doctors for each question
        
        Args:
            round_number: Voting round (affects threshold)
            test_folder_name: Specific test folder to analyze (uses latest if None)
            
        Returns:
            List of QuestionConsensus objects
        """
        results = self.load_all_results(test_folder_name)
        
        if not results:
            print("No test results found to analyze")
            return []
        
        # Load question types for backward compatibility
        question_types = self.load_question_types()
        
        # Determine threshold based on round
        threshold = self.threshold_first if round_number == 1 else self.threshold_subsequent
        
        # Group responses by question number
        question_responses = defaultdict(list)
        
        for test_session in results:
            doctor_name = test_session["doctor_name"]
            
            for result in test_session.get("results", []):
                if result["selected_answer"]:  # Only check if an answer was provided
                    question_num = result["question_number"]
                    question_responses[question_num].append({
                        "doctor": doctor_name,
                        "answer": result["selected_answer"],
                        "reasoning": result.get("reasoning", ""),
                        "question": result["question"],
                        "question_type": result.get("question_type", question_types.get(question_num, "other")),
                        "choices": result["choices"]
                    })
        
        # Analyze consensus for each question
        consensus_results = []
        
        for question_num in sorted(question_responses.keys()):
            responses = question_responses[question_num]
            
            if not responses:
                continue
            
            # Count votes for each choice
            vote_counts = Counter()
            votes_by_choice = defaultdict(list)
            
            for response in responses:
                choice = response["answer"]
                doctor = response["doctor"]
                vote_counts[choice] += 1
                votes_by_choice[choice].append(doctor)
            
            total_votes = len(responses)
            
            # Find consensus choice (most votes)
            if vote_counts:
                consensus_choice = vote_counts.most_common(1)[0][0]
                consensus_count = vote_counts[consensus_choice]
                consensus_percentage = (consensus_count / total_votes) * 100
                consensus_achieved = consensus_percentage >= (threshold * 100)
            else:
                consensus_choice = None
                consensus_count = 0
                consensus_percentage = 0.0
                consensus_achieved = False
            
            # Use first response for question metadata
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
                threshold_used=threshold
            )
            
            consensus_results.append(consensus_result)
        
        return consensus_results
    
    def load_question_types(self) -> Dict[int, str]:
        """Load question types from the questions file for backward compatibility"""
        try:
            questions_file = "../00_question_banks/test_1/test_1_questions.json"
            with open(questions_file, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            
            question_types = {}
            for q in questions:
                question_types[q["question_number"]] = q.get("question_type", "other")
            
            return question_types
            
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def print_consensus_summary(self, consensus_results: List[QuestionConsensus]):
        """Print a summary of consensus results"""
        if not consensus_results:
            print("No consensus results to display")
            return
        
        total_questions = len(consensus_results)
        consensus_achieved = sum(1 for r in consensus_results if r.consensus_achieved)
        consensus_rate = (consensus_achieved / total_questions) * 100
        
        print(f"\n🏆 CONSENSUS ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total Questions Analyzed: {total_questions}")
        print(f"Consensus Achieved: {consensus_achieved}/{total_questions} ({consensus_rate:.1f}%)")
        print(f"Threshold Used: {consensus_results[0].threshold_used * 100:.0f}%")
        
        # Breakdown by question type
        type_stats = defaultdict(lambda: {"total": 0, "consensus": 0})
        
        for result in consensus_results:
            q_type = result.question_type
            type_stats[q_type]["total"] += 1
            if result.consensus_achieved:
                type_stats[q_type]["consensus"] += 1
        
        print(f"\n📋 Consensus by Question Type:")
        for q_type in sorted(type_stats.keys()):
            stats = type_stats[q_type]
            rate = (stats["consensus"] / stats["total"]) * 100
            print(f"  {q_type:<8}: {stats['consensus']:>2}/{stats['total']:<2} ({rate:>5.1f}%)")
        
        # Show failed consensus questions
        failed_consensus = [r for r in consensus_results if not r.consensus_achieved]
        
        if failed_consensus:
            print(f"\n❌ Questions without consensus ({len(failed_consensus)}):")
            for result in failed_consensus[:10]:  # Show first 10
                print(f"  Q{result.question_number}: {result.consensus_percentage:.1f}% "
                      f"for choice {result.consensus_choice}")
                
                # Show vote breakdown
                vote_summary = []
                for choice, count in sorted(result.vote_counts.items()):
                    vote_summary.append(f"{choice}:{count}")
                print(f"    Votes: {', '.join(vote_summary)}")
        
        print()
    
    def get_questions_needing_second_vote(self, consensus_results: List[QuestionConsensus]) -> List[int]:
        """Get list of question numbers that need a second vote (failed first round consensus)"""
        return [r.question_number for r in consensus_results if not r.consensus_achieved]
    
    def save_consensus_report(self, consensus_results: List[QuestionConsensus], filename: Optional[str] = None):
        """Save detailed consensus report to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mode_suffix = f"_{self.mode}" if self.mode != "all" else ""
            filename = f"consensus_report{mode_suffix}_{timestamp}.json"
        
        # Convert to serializable format
        report = {
            "timestamp": datetime.now().isoformat(),
            "mode": self.mode,
            "summary": {
                "total_questions": len(consensus_results),
                "consensus_achieved": sum(1 for r in consensus_results if r.consensus_achieved),
                "threshold_used": consensus_results[0].threshold_used if consensus_results else None
            },
            "questions": []
        }
        
        for result in consensus_results:
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
                "threshold_used": result.threshold_used
            }
            report["questions"].append(question_data)
        
        # Ensure consensus reports directory exists
        consensus_reports_dir = "../03_consensus_benchmarks/consensus_reports"
        os.makedirs(consensus_reports_dir, exist_ok=True)
        
        filepath = os.path.join(consensus_reports_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"💾 Consensus report saved to: {filepath}")
        except Exception as e:
            print(f"❌ Error saving consensus report: {e}")


def main():
    """Main entry point for consensus analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Medical Board Consensus Analyzer")
    parser.add_argument("--mode", choices=["vanilla", "enhanced", "all"], default="all",
                       help="Analysis mode: vanilla (no embeddings), enhanced (with embeddings), or all")
    parser.add_argument("--round", type=int, default=1,
                       help="Consensus round number (affects threshold)")
    parser.add_argument("--test", type=str, default=None,
                       help="Specific test folder to analyze (e.g., test_20250709_225521)")
    parser.add_argument("--list", action="store_true",
                       help="List available test folders")
    
    args = parser.parse_args()
    
    analyzer = ConsensusAnalyzer(mode=args.mode)
    
    # Handle --list option
    if args.list:
        available_folders = analyzer.get_available_test_folders()
        if available_folders:
            print("📂 Available test folders:")
            for i, folder in enumerate(available_folders[:20]):  # Show first 20
                print(f"  {i+1}. {folder}")
            if len(available_folders) > 20:
                print(f"  ... and {len(available_folders) - 20} more")
        else:
            print("❌ No test folders found")
        return
    
    mode_desc = {"vanilla": "Vanilla (No Embeddings)", "enhanced": "Enhanced (With Embeddings)", "all": "All Models"}
    print(f"🗳️  Analyzing Medical Board Consensus - {mode_desc[args.mode]} (Round {args.round})")
    
    # Analyze consensus
    consensus_results = analyzer.analyze_consensus(args.round, args.test)
    
    if not consensus_results:
        print("No test results found for analysis")
        return
    
    # Print summary
    analyzer.print_consensus_summary(consensus_results)
    
    # Save detailed report
    analyzer.save_consensus_report(consensus_results)
    
    # Check for second round needs
    if args.round == 1:
        failed_questions = analyzer.get_questions_needing_second_vote(consensus_results)
        if failed_questions:
            print(f"\n🔄 {len(failed_questions)} questions need a second vote with higher threshold")
            print(f"   Run: python consensus_analyzer.py --mode {args.mode} --round 2")


if __name__ == "__main__":
    main() 