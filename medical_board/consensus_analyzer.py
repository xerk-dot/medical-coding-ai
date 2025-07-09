"""
Consensus Analyzer for Medical Board Results

Implements the voting thresholds:
- First vote: 70% agreement required
- Second/subsequent votes: 85% agreement required
"""
import json
import os
import glob
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
    """Analyzes consensus across multiple AI doctor test results"""
    
    def __init__(self, results_dir: str = "../medical_board_judgements"):
        self.results_dir = results_dir
        self.threshold_first = 0.70  # 70% for first vote
        self.threshold_subsequent = 0.85  # 85% for subsequent votes
    
    def load_all_results(self) -> List[Dict]:
        """Load all test result files from the judgements directory"""
        pattern = os.path.join(self.results_dir, "*.json")
        files = glob.glob(pattern)
        
        results = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results.append(data)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        print(f"Loaded {len(results)} test result files")
        return results
    
    def analyze_consensus(self, round_number: int = 1) -> List[QuestionConsensus]:
        """
        Analyze consensus across all AI doctors for each question
        
        Args:
            round_number: Voting round (affects threshold)
            
        Returns:
            List of QuestionConsensus objects
        """
        results = self.load_all_results()
        
        if not results:
            print("No test results found to analyze")
            return []
        
        # Determine threshold based on round
        threshold = self.threshold_first if round_number == 1 else self.threshold_subsequent
        
        # Group responses by question number
        question_responses = defaultdict(list)
        
        for test_session in results:
            doctor_name = test_session["doctor_name"]
            
            for result in test_session.get("results", []):
                if result["success"] and result["selected_answer"]:
                    question_num = result["question_number"]
                    question_responses[question_num].append({
                        "doctor": doctor_name,
                        "answer": result["selected_answer"],
                        "reasoning": result.get("reasoning", ""),
                        "question": result["question"],
                        "question_type": result["question_type"],
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
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"consensus_report_{timestamp}.json"
        
        # Convert to serializable format
        report = {
            "timestamp": datetime.now().isoformat(),
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
        
        filepath = os.path.join(self.results_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"💾 Consensus report saved to: {filepath}")
        except Exception as e:
            print(f"❌ Error saving consensus report: {e}")


def main():
    """Main entry point for consensus analysis"""
    import sys
    
    analyzer = ConsensusAnalyzer()
    
    # Determine round number from command line
    round_number = 1
    if len(sys.argv) > 1:
        try:
            round_number = int(sys.argv[1])
        except ValueError:
            print("Invalid round number. Using round 1.")
    
    print(f"🗳️  Analyzing Medical Board Consensus (Round {round_number})")
    
    # Analyze consensus
    consensus_results = analyzer.analyze_consensus(round_number)
    
    if not consensus_results:
        print("No test results found for analysis")
        return
    
    # Print summary
    analyzer.print_consensus_summary(consensus_results)
    
    # Save detailed report
    analyzer.save_consensus_report(consensus_results)
    
    # Check for second round needs
    if round_number == 1:
        failed_questions = analyzer.get_questions_needing_second_vote(consensus_results)
        if failed_questions:
            print(f"\n🔄 {len(failed_questions)} questions need a second vote with 85% threshold")
            print("   Run: python consensus_analyzer.py 2")


if __name__ == "__main__":
    main() 