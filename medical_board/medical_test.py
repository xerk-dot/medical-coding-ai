"""
Medical Board Test Runner

This script administers the medical coding test to all AI doctors in the panel.
Each AI takes the test individually, one question at a time.
Results are saved to medical_board_judgements as JSON files.
"""
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from config import AI_DOCTORS, SYSTEM_PROMPTS, QUESTIONS_FILE, RESULTS_DIR, RATE_LIMIT_DELAY
from ai_client import AIClient


@dataclass
class TestResult:
    """Data class for individual question result"""
    question_number: int
    question: str
    question_type: str
    choices: Dict[str, str]
    selected_answer: Optional[str]
    reasoning: Optional[str]
    raw_response: Optional[str]
    success: bool
    error_message: Optional[str] = None


@dataclass
class DoctorTestSession:
    """Data class for complete test session"""
    doctor_name: str
    model_id: str
    start_time: str
    end_time: Optional[str]
    total_questions: int
    successful_answers: int
    results: List[TestResult]


class MedicalBoardTest:
    """Main test administration class"""
    
    def __init__(self):
        self.client = AIClient()
        self.questions = self._load_questions()
        self._ensure_results_dir()
    
    def _load_questions(self) -> List[Dict]:
        """Load questions from the JSON file"""
        try:
            with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            print(f"Loaded {len(questions)} questions from {QUESTIONS_FILE}")
            return questions
        except FileNotFoundError:
            print(f"Error: Questions file not found at {QUESTIONS_FILE}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in questions file: {e}")
            return []
    
    def _ensure_results_dir(self):
        """Ensure the results directory exists"""
        os.makedirs(RESULTS_DIR, exist_ok=True)
    
    def run_single_doctor_test(self, doctor_key: str) -> Optional[DoctorTestSession]:
        """
        Run the test for a single AI doctor
        
        Args:
            doctor_key: Key from AI_DOCTORS config
            
        Returns:
            DoctorTestSession with results, or None if doctor not found
        """
        if doctor_key not in AI_DOCTORS:
            print(f"Error: Doctor '{doctor_key}' not found in configuration")
            return None
        
        doctor_config = AI_DOCTORS[doctor_key]
        doctor_name = doctor_config["display_name"]
        model_id = doctor_config["model_id"]
        short_name = doctor_config["short_name"]
        
        print(f"\n🏥 Starting medical board exam for {doctor_name}")
        print(f"   Model: {model_id}")
        print(f"   Questions: {len(self.questions)}")
        
        # Initialize test session
        session = DoctorTestSession(
            doctor_name=doctor_name,
            model_id=model_id,
            start_time=datetime.now().isoformat(),
            end_time=None,
            total_questions=len(self.questions),
            successful_answers=0,
            results=[]
        )
        
        # Administer each question
        for i, question_data in enumerate(self.questions, 1):
            print(f"\n📝 Question {i}/{len(self.questions)}: {question_data['question_type']} question")
            
            result = self._ask_single_question(
                model_id=model_id,
                question_data=question_data
            )
            
            session.results.append(result)
            if result.success:
                session.successful_answers += 1
                print(f"   ✅ Answer: {result.selected_answer}")
            else:
                print(f"   ❌ Failed: {result.error_message}")
            
            # Rate limiting between questions
            time.sleep(RATE_LIMIT_DELAY)
        
        # Complete the session
        session.end_time = datetime.now().isoformat()
        
        # Save results
        self._save_test_results(session, short_name)
        
        # Print summary
        self._print_test_summary(session)
        
        return session
    
    def _ask_single_question(self, model_id: str, question_data: Dict) -> TestResult:
        """
        Ask a single question to the AI model
        
        Args:
            model_id: OpenRouter model identifier
            question_data: Question dictionary from JSON
            
        Returns:
            TestResult with the AI's response
        """
        question_type = question_data.get("question_type", "other")
        system_prompt = SYSTEM_PROMPTS.get(question_type, SYSTEM_PROMPTS["other"])
        
        try:
            selected_answer, reasoning, raw_response = self.client.ask_question(
                model_id=model_id,
                system_prompt=system_prompt,
                question=question_data["question"],
                choices=question_data["choices"]
            )
            
            if selected_answer:
                return TestResult(
                    question_number=question_data["question_number"],
                    question=question_data["question"],
                    question_type=question_type,
                    choices=question_data["choices"],
                    selected_answer=selected_answer,
                    reasoning=reasoning,
                    raw_response=raw_response,
                    success=True
                )
            else:
                return TestResult(
                    question_number=question_data["question_number"],
                    question=question_data["question"],
                    question_type=question_type,
                    choices=question_data["choices"],
                    selected_answer=None,
                    reasoning=None,
                    raw_response=raw_response,
                    success=False,
                    error_message=reasoning if reasoning else "No valid response received"
                )
                
        except Exception as e:
            return TestResult(
                question_number=question_data["question_number"],
                question=question_data["question"],
                question_type=question_type,
                choices=question_data["choices"],
                selected_answer=None,
                reasoning=None,
                raw_response=None,
                success=False,
                error_message=str(e)
            )
    
    def _save_test_results(self, session: DoctorTestSession, short_name: str):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{short_name}_{timestamp}.json"
        filepath = os.path.join(RESULTS_DIR, filename)
        
        # Convert to dict for JSON serialization
        session_dict = asdict(session)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_dict, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Results saved to: {filepath}")
        except Exception as e:
            print(f"\n❌ Error saving results: {e}")
    
    def _print_test_summary(self, session: DoctorTestSession):
        """Print a summary of the test results"""
        success_rate = (session.successful_answers / session.total_questions) * 100
        
        print(f"\n📊 Test Summary for {session.doctor_name}")
        print(f"   Total Questions: {session.total_questions}")
        print(f"   Successful Answers: {session.successful_answers}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Count by question type
        type_counts = {}
        type_success = {}
        
        for result in session.results:
            q_type = result.question_type
            if q_type not in type_counts:
                type_counts[q_type] = 0
                type_success[q_type] = 0
            
            type_counts[q_type] += 1
            if result.success:
                type_success[q_type] += 1
        
        print(f"\n   📋 Breakdown by Question Type:")
        for q_type in sorted(type_counts.keys()):
            rate = (type_success[q_type] / type_counts[q_type]) * 100
            print(f"     {q_type}: {type_success[q_type]}/{type_counts[q_type]} ({rate:.1f}%)")
    
    def run_all_doctors_test(self):
        """Run the test for all doctors in the AI panel"""
        print("🏥 Starting Medical Board Examination for All AI Doctors")
        print("="*60)
        
        all_results = []
        
        for doctor_key in AI_DOCTORS.keys():
            try:
                session = self.run_single_doctor_test(doctor_key)
                if session:
                    all_results.append(session)
                
                # Longer delay between doctors to be respectful to API
                print(f"\n⏱️  Waiting before next doctor...")
                time.sleep(RATE_LIMIT_DELAY * 3)
                
            except KeyboardInterrupt:
                print(f"\n⚠️  Test interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Error testing {doctor_key}: {e}")
                continue
        
        # Print overall summary
        if all_results:
            self._print_overall_summary(all_results)
    
    def _print_overall_summary(self, all_results: List[DoctorTestSession]):
        """Print summary across all doctors"""
        print("\n" + "="*60)
        print("🏆 OVERALL MEDICAL BOARD RESULTS")
        print("="*60)
        
        for session in sorted(all_results, key=lambda x: x.successful_answers, reverse=True):
            success_rate = (session.successful_answers / session.total_questions) * 100
            print(f"{session.doctor_name:<30} {session.successful_answers:>3}/{session.total_questions} ({success_rate:>5.1f}%)")


def main():
    """Main entry point"""
    import sys
    
    if not os.path.exists(QUESTIONS_FILE):
        print(f"❌ Error: Questions file not found at {QUESTIONS_FILE}")
        print("   Please ensure the questions have been extracted from PDF first.")
        return
    
    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print("   Please set your OpenRouter API key:")
        print("   export OPENROUTER_API_KEY='your_api_key_here'")
        return
    
    test = MedicalBoardTest()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        doctor_key = sys.argv[1]
        if doctor_key == "--list":
            print("Available AI Doctors:")
            for key, config in AI_DOCTORS.items():
                print(f"  {key}: {config['display_name']}")
            return
        elif doctor_key == "--all":
            test.run_all_doctors_test()
        elif doctor_key in AI_DOCTORS:
            test.run_single_doctor_test(doctor_key)
        else:
            print(f"❌ Unknown doctor: {doctor_key}")
            print("Use --list to see available doctors or --all to test all doctors")
    else:
        print("Medical Board Test Runner")
        print("\nUsage:")
        print("  python medical_test.py --all              # Test all doctors")
        print("  python medical_test.py --list             # List available doctors")
        print("  python medical_test.py claude_sonnet_4    # Test specific doctor")


if __name__ == "__main__":
    main() 