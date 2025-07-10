"""
Test script to verify the medical board setup is working correctly
"""
import os
import json
import sys

def test_environment():
    """Test environment variables and dependencies"""
    print("🔍 Testing Environment Setup...")
    
    # Check for OpenRouter API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY environment variable not set")
        return False
    else:
        print("✅ OpenRouter API key found")
    
    # Test imports
    try:
        import requests
        print("✅ requests library available")
    except ImportError:
        print("❌ requests library not found. Run: pip install -r requirements.txt")
        return False
    
    return True

def test_questions_file():
    """Test that questions file exists and is valid"""
    print("\n📋 Testing Questions File...")
    
    questions_file = "../00_question_banks/test_1/test_1_questions.json"
    
    if not os.path.exists(questions_file):
        print(f"❌ Questions file not found: {questions_file}")
        print("   Run the PDF extraction tool first:")
        print("   cd ../utilities/pdf_to_json && python pdf_parser.py test_1.pdf")
        return False
    
    try:
        with open(questions_file, 'r') as f:
            questions = json.load(f)
        
        if not isinstance(questions, list):
            print("❌ Questions file should contain a list")
            return False
        
        if len(questions) == 0:
            print("❌ Questions file is empty")
            return False
        
        # Test first question structure
        first_q = questions[0]
        required_fields = ["question_number", "question", "choices", "question_type"]
        
        for field in required_fields:
            if field not in first_q:
                print(f"❌ Missing required field '{field}' in questions")
                return False
        
        if not isinstance(first_q["choices"], dict):
            print("❌ Choices should be a dictionary")
            return False
        
        choice_keys = set(first_q["choices"].keys())
        expected_keys = {"A", "B", "C", "D"}
        
        if choice_keys != expected_keys:
            print(f"❌ Expected choices A, B, C, D but got: {choice_keys}")
            return False
        
        print(f"✅ Questions file valid with {len(questions)} questions")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in questions file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading questions file: {e}")
        return False

def test_config():
    """Test configuration file"""
    print("\n⚙️ Testing Configuration...")
    
    try:
        from config import AI_DOCTORS, SYSTEM_PROMPTS
        
        if not AI_DOCTORS:
            print("❌ No AI doctors configured")
            return False
        
        print(f"✅ {len(AI_DOCTORS)} AI doctors configured:")
        for key, config in AI_DOCTORS.items():
            print(f"   - {config['display_name']} ({key})")
        
        if not SYSTEM_PROMPTS:
            print("❌ No system prompts configured")
            return False
        
        print(f"✅ {len(SYSTEM_PROMPTS)} system prompts configured")
        return True
        
    except ImportError as e:
        print(f"❌ Error importing config: {e}")
        return False
    except Exception as e:
        print(f"❌ Error in config: {e}")
        return False

def test_api_connection():
    """Test basic API connection (without making a real request)"""
    print("\n🌐 Testing API Configuration...")
    
    try:
        from ai_client import AIClient
        
        client = AIClient()
        
        if not client.api_key:
            print("❌ No API key available to client")
            return False
        
        if not client.base_url:
            print("❌ No base URL configured")
            return False
        
        print("✅ AI client configured correctly")
        print(f"   Base URL: {client.base_url}")
        print("   API Key: [REDACTED]")
        return True
        
    except Exception as e:
        print(f"❌ Error creating AI client: {e}")
        return False

def test_results_directory():
    """Test that results directory exists or can be created"""
    print("\n📁 Testing Results Directory...")
    
    results_dir = "../02_test_attempts"
    
    try:
        os.makedirs(results_dir, exist_ok=True)
        print(f"✅ Results directory ready: {results_dir}")
        return True
    except Exception as e:
        print(f"❌ Cannot create results directory: {e}")
        return False

def main():
    """Run all tests"""
    print("🏥 Medical Board Setup Test")
    print("=" * 50)
    
    tests = [
        test_environment,
        test_questions_file,
        test_config,
        test_api_connection,
        test_results_directory
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Ready to run medical board tests.")
        print("\nNext step:")
        print("  python medical_test.py --list")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 