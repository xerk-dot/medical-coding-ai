"""
Medical Board Test Suite

This module runs medical coding tests against multiple AI models and analyzes their performance.
It supports both regular testing and enhanced testing with medical code embeddings.
Includes parallel processing for faster testing at both question and agent levels.
"""
import json
import os
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ai_client import AIClient
from config import AI_DOCTORS, SYSTEM_PROMPTS, PARALLEL_WORKERS, RATE_LIMIT_DELAY

# Default settings for agent-level parallelism
DEFAULT_MAX_CONCURRENT_AGENTS = 4


class TestResult:
    """Result from a single question test"""
    def __init__(self, question_number: int, question: str, question_type: str, choices: Dict[str, str], 
                 correct_answer: str, selected_answer: Optional[str], 
                 reasoning: Optional[str], response_time: float = 0.0, 
                 raw_response: Optional[str] = None, success: bool = True, error_message: Optional[str] = None):
        self.question_number = question_number
        self.question = question
        self.question_type = question_type
        self.choices = choices
        self.correct_answer = correct_answer
        self.selected_answer = selected_answer
        self.reasoning = reasoning
        self.response_time = response_time
        self.raw_response = raw_response
        self.success = success  # Whether the API request was successful
        self.error_message = error_message


class DoctorTestResults:
    """Results from testing a single AI doctor"""
    def __init__(self, doctor_name: str, model_id: str):
        self.doctor_name = doctor_name
        self.model_id = model_id
        self.results: List[TestResult] = []
        self.total_questions = 0
        self.completed_answers = 0
        self.total_response_time = 0.0
    
    @property
    def completion_rate(self) -> float:
        """Percentage of questions that received an answer"""
        return (self.completed_answers / self.total_questions * 100) if self.total_questions > 0 else 0.0
    
    @property
    def average_response_time(self) -> float:
        """Average response time per question"""
        return (self.total_response_time / len(self.results)) if self.results else 0.0


class EmbeddingsLoader:
    """Class to load and provide medical code embeddings"""
    
    def __init__(self, embeddings_file: str = "../code_embeddings/question_embeddings.json"):
        self.embeddings_file = embeddings_file
        self.embeddings = {}
        self.load_embeddings()
    
    def load_embeddings(self):
        """Load embeddings from the JSON file"""
        if os.path.exists(self.embeddings_file):
            try:
                with open(self.embeddings_file, 'r') as f:
                    embeddings_data = json.load(f)
                
                # Index by question number for quick lookup
                for question_data in embeddings_data:
                    question_num = question_data.get('question_number')
                    if question_num:
                        self.embeddings[question_num] = question_data
                
                print(f"✓ Loaded embeddings for {len(self.embeddings)} questions")
            except Exception as e:
                print(f"⚠️  Warning: Could not load embeddings: {e}")
                self.embeddings = {}
        else:
            print(f"⚠️  Warning: Embeddings file not found at {self.embeddings_file}")
            self.embeddings = {}
    
    def get_embeddings_for_question(self, question_number: int) -> Optional[Dict]:
        """Get embeddings for a specific question"""
        return self.embeddings.get(question_number)
    
    def format_embeddings_context(self, question_number: int) -> str:
        """Format embeddings as additional context for AI models"""
        embeddings = self.get_embeddings_for_question(question_number)
        if not embeddings:
            return ""
        
        context = "\n\nAdditional Medical Code Information:\n"
        for choice in embeddings.get('choices', []):
            code = choice.get('code', '')
            description = choice.get('embedding', {}).get('description', '')
            system = choice.get('embedding', {}).get('system', '')
            
            if description and description != f'{system} code (no additional information available)':
                context += f"• {choice.get('choice', '')}: {code} - {description}\n"
        
        context += "\nPlease use this information to help inform your answer.\n"
        return context if len(context) > 50 else ""  # Only return if we have meaningful content


class MedicalBoardTest:
    """Main test runner for medical board tests"""
    
    def __init__(self, use_embeddings: bool = False, max_workers: int = None):
        self.ai_client = AIClient()
        self.use_embeddings = use_embeddings
        self.embeddings_loader = EmbeddingsLoader() if use_embeddings else None
        self.max_workers = max_workers or PARALLEL_WORKERS
        self.test_session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Shared timestamp for this test session
        
        if use_embeddings and self.embeddings_loader:
            print("🧠 Enhanced mode: Using medical code embeddings for additional context")
        else:
            print("📝 Standard mode: Running without embeddings")
    
    def load_questions(self, questions_file: str = "../question_banks/test_1/test_1_questions.json") -> List[Dict]:
        """Load questions from JSON file"""
        with open(questions_file, 'r') as f:
            return json.load(f)
    
    def load_answers(self, answers_file: str = "../question_banks/test_1/test_1_answers.json") -> Dict:
        """Load correct answers from JSON file and create lookup dictionary"""
        with open(answers_file, 'r') as f:
            answers_list = json.load(f)
        
        # Convert list to dictionary for quick lookup
        answers_dict = {}
        for answer_item in answers_list:
            question_number = answer_item.get('question_number')
            correct_answer = answer_item.get('correct_answer')
            if question_number and correct_answer:
                answers_dict[question_number] = correct_answer
        
        return answers_dict
    
    def _ask_single_question(self, model_id: str, system_prompt: str, question_data: Dict, 
                           correct_answer: str) -> TestResult:
        """Ask a single question to an AI model (synchronous version)"""
        question_number = question_data.get('question_number', 0)
        question = question_data.get('question', '')
        choices = question_data.get('choices', {})
        question_type = question_data.get('question_type', 'other')
        
        # Add embeddings context if enabled
        enhanced_question = question
        if self.use_embeddings and self.embeddings_loader:
            embeddings_context = self.embeddings_loader.format_embeddings_context(question_number)
            if embeddings_context:
                enhanced_question = question + embeddings_context
        
        start_time = datetime.now()
        success = True
        error_message = None
        
        try:
            selected_choice, reasoning, raw_response = self.ai_client.ask_question(
                model_id, system_prompt, enhanced_question, choices
            )
        except Exception as e:
            success = False
            error_message = str(e)
            selected_choice, reasoning, raw_response = None, f"Error: {e}", None
            
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        return TestResult(
            question_number=question_number,
            question=question,
            question_type=question_type,
            choices=choices,
            correct_answer=correct_answer,
            selected_answer=selected_choice,
            reasoning=reasoning,
            response_time=response_time,
            raw_response=raw_response,
            success=success,
            error_message=error_message
        )
    
    async def _ask_single_question_async(self, model_id: str, system_prompt: str, question_data: Dict, 
                                       correct_answer: str, semaphore: asyncio.Semaphore) -> TestResult:
        """Ask a single question to an AI model (async version with rate limiting)"""
        async with semaphore:  # Limit concurrent requests
            # Add small delay for rate limiting
            await asyncio.sleep(RATE_LIMIT_DELAY)
            
            question_number = question_data.get('question_number', 0)
            question = question_data.get('question', '')
            choices = question_data.get('choices', {})
            question_type = question_data.get('question_type', 'other')
            
            # Add embeddings context if enabled
            enhanced_question = question
            if self.use_embeddings and self.embeddings_loader:
                embeddings_context = self.embeddings_loader.format_embeddings_context(question_number)
                if embeddings_context:
                    enhanced_question = question + embeddings_context
            
            # Run the synchronous AI client call in a thread pool
            loop = asyncio.get_event_loop()
            
            start_time = datetime.now()
            success = True
            error_message = None
            
            try:
                selected_choice, reasoning, raw_response = await loop.run_in_executor(
                    None,
                    lambda: self.ai_client.ask_question(model_id, system_prompt, enhanced_question, choices)
                )
            except Exception as e:
                print(f"   ❌ Error on question {question_number}: {e}")
                success = False
                error_message = str(e)
                selected_choice, reasoning, raw_response = None, f"Error: {e}", None
            
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            return TestResult(
                question_number=question_number,
                question=question,
                question_type=question_type,
                choices=choices,
                correct_answer=correct_answer,
                selected_answer=selected_choice,
                reasoning=reasoning,
                response_time=response_time,
                raw_response=raw_response,
                success=success,
                error_message=error_message
            )
    
    async def _process_questions_parallel(self, model_id: str, questions: List[Dict], 
                                        answers: Dict, max_workers: int = None) -> List[TestResult]:
        """Process multiple questions in parallel with rate limiting"""
        if max_workers is None:
            max_workers = self.max_workers
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_workers)
        
        # Create tasks for all questions
        tasks = []
        for question_data in questions:
            question_number = question_data.get('question_number', 0)
            question_type = question_data.get('question_type', 'other')
            
            # Get correct answer
            correct_answer = answers.get(question_number)
            if not correct_answer:
                print(f"   ⚠️  No correct answer found for question {question_number}")
                continue
            
            # Get system prompt based on question type
            system_prompt = SYSTEM_PROMPTS.get(question_type, SYSTEM_PROMPTS['other'])
            
            # Create async task
            task = self._ask_single_question_async(model_id, system_prompt, question_data, correct_answer, semaphore)
            tasks.append(task)
        
        # Process all questions in parallel
        print(f"   🚀 Processing {len(tasks)} questions in parallel (max {max_workers} concurrent)")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"   ❌ Task {i+1} failed: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    def run_single_doctor_test(self, doctor_key: str, max_questions: Optional[int] = None, 
                             parallel: bool = True) -> Optional[DoctorTestResults]:
        """Run test for a single doctor (wrapper for async version)"""
        if parallel:
            return asyncio.run(self.run_single_doctor_test_async(doctor_key, max_questions))
        else:
            return self._run_single_doctor_test_sequential(doctor_key, max_questions)
    
    async def run_single_doctor_test_async(self, doctor_key: str, max_questions: Optional[int] = None) -> Optional[DoctorTestResults]:
        """Run test for a single doctor (async version with parallel processing)"""
        if doctor_key not in AI_DOCTORS:
            print(f"❌ Doctor '{doctor_key}' not found in configuration")
            return None
        
        doctor_config = AI_DOCTORS[doctor_key]
        doctor_name = doctor_config["display_name"]
        model_id = doctor_config["model_id"]
        
        print(f"\n🏥 Testing {doctor_name}")
        print(f"   Model: {model_id}")
        
        # Load questions and answers
        questions = self.load_questions()
        answers = self.load_answers()
        
        if max_questions:
            questions = questions[:max_questions]
        
        results = DoctorTestResults(doctor_name, model_id)
        results.total_questions = len(questions)
        
        # Process questions in parallel
        start_time = time.time()
        test_results = await self._process_questions_parallel(model_id, questions, answers)
        end_time = time.time()
        
        # Process results
        total_response_time = 0.0
        completed_count = 0
        
        for test_result in test_results:
            results.results.append(test_result)
            total_response_time += test_result.response_time
            
            if test_result.selected_answer:
                completed_count += 1
        
        results.completed_answers = completed_count
        results.total_response_time = total_response_time
        
        # Print summary
        processing_time = end_time - start_time
        print(f"   ✅ Completed {completed_count}/{len(questions)} questions in {processing_time:.1f}s")
        
        # Save results to file
        self._save_results(results)
        
        print(f"\n📊 {doctor_name} Results:")
        print(f"   Completion Rate: {results.completion_rate:.1f}% ({results.completed_answers}/{results.total_questions})")
        print(f"   Average Response Time: {results.average_response_time:.1f}s")
        print(f"   Total Processing Time: {processing_time:.1f}s")
        
        return results
    
    async def run_multiple_doctors_async(self, doctor_keys: List[str], max_questions: Optional[int] = None,
                                       max_concurrent_agents: int = DEFAULT_MAX_CONCURRENT_AGENTS) -> List[DoctorTestResults]:
        """Run tests for multiple doctors in parallel"""
        print(f"🚀 Running parallel tests for {len(doctor_keys)} agents (max {max_concurrent_agents} concurrent)")
        
        # Create semaphore to limit concurrent agents
        agent_semaphore = asyncio.Semaphore(max_concurrent_agents)
        
        async def run_single_agent_with_semaphore(doctor_key: str) -> Optional[DoctorTestResults]:
            """Run a single agent test with semaphore control"""
            async with agent_semaphore:
                try:
                    return await self.run_single_doctor_test_async(doctor_key, max_questions)
                except Exception as e:
                    print(f"❌ Error testing {doctor_key}: {e}")
                    return None
        
        # Create tasks for all agents
        tasks = [run_single_agent_with_semaphore(doctor_key) for doctor_key in doctor_keys]
        
        # Run all agent tests in parallel with progress tracking
        print(f"⏳ Processing {len(tasks)} agents in parallel...")
        start_time = time.time()
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Process results and filter out failures
        valid_results = []
        failed_count = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"❌ Agent {doctor_keys[i]} failed: {result}")
                failed_count += 1
            elif result is not None:
                valid_results.append(result)
            else:
                failed_count += 1
        
        success_count = len(valid_results)
        print(f"\n✅ Parallel agent testing completed in {total_time:.1f}s")
        print(f"   Success: {success_count}/{len(doctor_keys)} agents")
        if failed_count > 0:
            print(f"   Failed: {failed_count} agents")
        
        return valid_results
    
    def run_multiple_doctors(self, doctor_keys: List[str], max_questions: Optional[int] = None,
                           max_concurrent_agents: int = DEFAULT_MAX_CONCURRENT_AGENTS,
                           parallel: bool = True) -> List[DoctorTestResults]:
        """Run tests for multiple doctors (wrapper for async version)"""
        if parallel and len(doctor_keys) > 1:
            return asyncio.run(self.run_multiple_doctors_async(doctor_keys, max_questions, max_concurrent_agents))
        else:
            # Sequential fallback
            results = []
            for doctor_key in doctor_keys:
                try:
                    result = self.run_single_doctor_test(doctor_key, max_questions, parallel)
                    if result:
                        results.append(result)
                except Exception as e:
                    print(f"Error testing {doctor_key}: {e}")
            return results
    
    def _run_single_doctor_test_sequential(self, doctor_key: str, max_questions: Optional[int] = None) -> Optional[DoctorTestResults]:
        """Run test for a single doctor (sequential version - original implementation)"""
        if doctor_key not in AI_DOCTORS:
            print(f"❌ Doctor '{doctor_key}' not found in configuration")
            return None
        
        doctor_config = AI_DOCTORS[doctor_key]
        doctor_name = doctor_config["display_name"]
        model_id = doctor_config["model_id"]
        
        print(f"\n🏥 Testing {doctor_name} (Sequential Mode)")
        print(f"   Model: {model_id}")
        
        # Load questions and answers
        questions = self.load_questions()
        answers = self.load_answers()
        
        if max_questions:
            questions = questions[:max_questions]
        
        results = DoctorTestResults(doctor_name, model_id)
        results.total_questions = len(questions)
        
        for i, question_data in enumerate(questions, 1):
            question_number = question_data.get('question_number', i)
            question_type = question_data.get('question_type', 'other')
            
            print(f"   Question {i}/{len(questions)}: #{question_number} ({question_type})")
            
            # Get correct answer
            correct_answer = answers.get(question_number)
            if not correct_answer:
                print(f"   ⚠️  No correct answer found for question {question_number}")
                continue
            
            # Get system prompt based on question type
            system_prompt = SYSTEM_PROMPTS.get(question_type, SYSTEM_PROMPTS['other'])
            
            # Ask the question
            test_result = self._ask_single_question(model_id, system_prompt, question_data, correct_answer)
            results.results.append(test_result)
            
            if test_result.selected_answer:
                results.completed_answers += 1
                print(f"   ✍🏻 Answered: {test_result.selected_answer}")
            else:
                print(f"   ⚠️  No answer provided")
            
            results.total_response_time += test_result.response_time
        
        # Save results to file
        self._save_results(results)
        
        print(f"\n📊 {doctor_name} Results:")
        print(f"   Completion Rate: {results.completion_rate:.1f}% ({results.completed_answers}/{results.total_questions})")
        print(f"   Average Response Time: {results.average_response_time:.1f}s")
        
        return results
    
    def _save_results(self, results: DoctorTestResults):
        """Save test results to JSON file in timestamped folder"""
        # Create timestamped test folder using shared session timestamp
        test_folder = f"../test_attempts/test_{self.test_session_timestamp}"
        os.makedirs(test_folder, exist_ok=True)
        
        # Generate filename with individual result timestamp
        individual_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
        doctor_key = results.doctor_name.lower().replace(" ", "_").replace("dr._", "").replace(".", "_").replace("(", "").replace(")", "").replace("the_", "")
        
        # Add suffix for enhanced mode
        mode_suffix = "_enhanced" if self.use_embeddings else ""
        filename = f"{test_folder}/{doctor_key}{mode_suffix}_{individual_timestamp}.json"
        
        # Prepare data for JSON serialization
        results_data = {
            "doctor_name": results.doctor_name,
            "model_id": results.model_id,
            "timestamp": individual_timestamp,
            "test_session_timestamp": self.test_session_timestamp,
            "total_questions": results.total_questions,
            "completed_answers": results.completed_answers,
            "completion_rate": results.completion_rate,
            "average_response_time": results.average_response_time,
            "use_embeddings": self.use_embeddings,
            "embeddings_count": len(self.embeddings_loader.embeddings) if self.embeddings_loader else 0,
            "results": []
        }
        
        for result in results.results:
            results_data["results"].append({
                "question_number": result.question_number,
                "question": result.question,
                "question_type": result.question_type,
                "choices": result.choices,
                "selected_answer": result.selected_answer,
                "reasoning": result.reasoning,
                "response_time": result.response_time,
                "raw_response": result.raw_response,
                "success": result.success,
                "error_message": result.error_message
            })
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"💾 Results saved to {filename}")


def main():
    """Main function with command-line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Medical Board Test Suite")
    parser.add_argument("--embeddings", action="store_true", 
                       help="Use medical code embeddings for enhanced context")
    parser.add_argument("--doctor", type=str, 
                       help="Test specific doctor (e.g., 'gemini_2_5_pro')")
    parser.add_argument("--max-questions", type=int, 
                       help="Limit number of questions for testing")
    parser.add_argument("--list-doctors", action="store_true",
                       help="List available doctors")
    parser.add_argument("--all", action="store_true",
                       help="Test all doctors in both vanilla and enhanced modes")
    parser.add_argument("--sequential", action="store_true",
                       help="Use sequential processing instead of parallel (slower but more reliable)")
    parser.add_argument("--workers", type=int, default=PARALLEL_WORKERS,
                       help=f"Number of parallel workers for questions (default: {PARALLEL_WORKERS})")
    parser.add_argument("--max-concurrent-agents", type=int, default=DEFAULT_MAX_CONCURRENT_AGENTS,
                       help=f"Maximum concurrent agents when testing multiple models (default: {DEFAULT_MAX_CONCURRENT_AGENTS})")
    parser.add_argument("--sequential-agents", action="store_true",
                       help="Test agents sequentially instead of in parallel")
    
    args = parser.parse_args()
    
    if args.list_doctors:
        print("Available doctors:")
        for key, config in AI_DOCTORS.items():
            print(f"  {key}: {config['display_name']} ({config['model_id']})")
        return
    
    # Set processing modes
    parallel_questions = not args.sequential
    parallel_agents = not args.sequential_agents
    
    if parallel_questions:
        print(f"🚀 Question-level parallelism enabled (max {args.workers} concurrent requests per agent)")
    else:
        print("🐌 Sequential question processing enabled")
    
    if parallel_agents and not args.doctor:
        print(f"🤖 Agent-level parallelism enabled (max {args.max_concurrent_agents} concurrent agents)")
    elif not args.doctor:
        print("🐌 Sequential agent processing enabled")
    
    if args.all:
        # Test all doctors in both modes with parallel processing
        print("🏥 Testing all doctors in both vanilla and enhanced modes...")
        all_doctor_keys = list(AI_DOCTORS.keys())
        
        # Test vanilla mode first
        print("\n" + "="*60)
        print("📝 VANILLA MODE (No Embeddings)")
        print("="*60)
        vanilla_test = MedicalBoardTest(use_embeddings=False, max_workers=args.workers)
        
        if parallel_agents:
            vanilla_results = vanilla_test.run_multiple_doctors(
                all_doctor_keys, args.max_questions, args.max_concurrent_agents, parallel_questions
            )
        else:
            vanilla_results = []
            for doctor_key in all_doctor_keys:
                try:
                    result = vanilla_test.run_single_doctor_test(doctor_key, args.max_questions, parallel_questions)
                    if result:
                        vanilla_results.append(result)
                except Exception as e:
                    print(f"Error testing {doctor_key} (vanilla): {e}")
        
        # Test enhanced mode
        print("\n" + "="*60)
        print("🧠 ENHANCED MODE (With Embeddings)")
        print("="*60)
        enhanced_test = MedicalBoardTest(use_embeddings=True, max_workers=args.workers)
        
        if parallel_agents:
            enhanced_results = enhanced_test.run_multiple_doctors(
                all_doctor_keys, args.max_questions, args.max_concurrent_agents, parallel_questions
            )
        else:
            enhanced_results = []
            for doctor_key in all_doctor_keys:
                try:
                    result = enhanced_test.run_single_doctor_test(doctor_key, args.max_questions, parallel_questions)
                    if result:
                        enhanced_results.append(result)
                except Exception as e:
                    print(f"Error testing {doctor_key} (enhanced): {e}")
        
        # Print comparison summary
        print("\n" + "="*80)
        print("📊 COMPARISON SUMMARY - COMPLETION RATES")
        print("="*80)
        print(f"{'Doctor':<35} {'Vanilla':<10} {'Enhanced':<10} {'Difference':<12}")
        print("-" * 80)
        
        for doctor_key in AI_DOCTORS.keys():
            doctor_name = AI_DOCTORS[doctor_key]["display_name"]
            vanilla_result = next((r for r in vanilla_results if r.doctor_name == doctor_name), None)
            enhanced_result = next((r for r in enhanced_results if r.doctor_name == doctor_name), None)
            
            vanilla_rate = vanilla_result.completion_rate if vanilla_result else 0.0
            enhanced_rate = enhanced_result.completion_rate if enhanced_result else 0.0
            difference = enhanced_rate - vanilla_rate
            
            vanilla_str = f"{vanilla_rate:.1f}%" if vanilla_result else "N/A"
            enhanced_str = f"{enhanced_rate:.1f}%" if enhanced_result else "N/A"
            diff_str = f"{difference:+.1f}%" if vanilla_result and enhanced_result else "N/A"
            
            print(f"{doctor_name:<35} {vanilla_str:<10} {enhanced_str:<10} {diff_str:<12}")
        
        return
    
    # Create test runner
    test = MedicalBoardTest(use_embeddings=args.embeddings, max_workers=args.workers)
    
    if args.doctor:
        # Test specific doctor
        result = test.run_single_doctor_test(args.doctor, args.max_questions, parallel_questions)
        if not result:
            print(f"Failed to test doctor: {args.doctor}")
    else:
        # Test all doctors in the specified mode
        mode_name = "Enhanced (with embeddings)" if args.embeddings else "Vanilla (no embeddings)"
        print(f"Running {mode_name} tests for all doctors...")
        all_doctor_keys = list(AI_DOCTORS.keys())
        
        if parallel_agents:
            test.run_multiple_doctors(all_doctor_keys, args.max_questions, args.max_concurrent_agents, parallel_questions)
        else:
            for doctor_key in all_doctor_keys:
                try:
                    test.run_single_doctor_test(doctor_key, args.max_questions, parallel_questions)
                except Exception as e:
                    print(f"Error testing {doctor_key}: {e}")


if __name__ == "__main__":
    main() 