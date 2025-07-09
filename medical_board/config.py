"""
Configuration for the Medical Board AI Testing System
"""
import os
from typing import Dict, List

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# AI Models Configuration - The Medical AI Panel
AI_DOCTORS: Dict[str, Dict[str, str]] = {
    "claude_sonnet_4": {
        "model_id": "anthropic/claude-3.5-sonnet",
        "display_name": "Dr. claude-sonnet-4-20250514",
        "short_name": "claude_sonnet_4"
    },
    "gemini_2_5_flash": {
        "model_id": "google/gemini-2.5-flash",
        "display_name": "Dr. gemini-2.5-flash",
        "short_name": "gemini_2_5_flash"
    },
    "gemini_2_5_pro": {
        "model_id": "google/gemini-2.5-pro",
        "display_name": "Dr. gemini-2.5-pro",
        "short_name": "gemini_2_5_pro"
    },
    "deepseek_v3": {
        "model_id": "deepseek/deepseek-v3",
        "display_name": "Dr. deepseek-v3-0324",
        "short_name": "deepseek_v3"
    },
    "grok_3": {
        "model_id": "x-ai/grok-3-preview",
        "display_name": "Dr. grok-3-preview-02-24",
        "short_name": "grok_3"
    },
    "gpt_4_1": {
        "model_id": "openai/gpt-4.1-2025-04-14",
        "display_name": "Dr. gpt-4.1-2025-04-14",
        "short_name": "gpt_4_1"
    },
    "gpt_4o": {
        "model_id": "openai/gpt-4o",
        "display_name": "Dr. 4o",
        "short_name": "gpt_4o"
    },
    "o3": {
        "model_id": "openai/o3-2025-04-16",
        "display_name": "Dr. o3-2025-04-16",
        "short_name": "o3"
    },
    "mistral_medium": {
        "model_id": "mistral/mistral-medium-2505",
        "display_name": "Dr. mistral-medium-2505",
        "short_name": "mistral_medium"
    },
    "o1": {
        "model_id": "openai/o1",
        "display_name": "Dr. o1",
        "short_name": "o1"
    }
}

# System prompts for different question types
SYSTEM_PROMPTS = {
    "CPT": """You are a medical coding expert specializing in CPT (Current Procedural Terminology) codes. 
You have extensive knowledge of medical procedures and their corresponding CPT codes. 
Analyze each question carefully and select the most appropriate CPT code from the given choices.
You must respond with only A, B, C, or D followed by a brief explanation of your reasoning.""",
    
    "ICD": """You are a medical coding expert specializing in ICD-10-CM (International Classification of Diseases) codes.
You have extensive knowledge of medical diagnoses and their corresponding ICD-10-CM codes.
Analyze each question carefully and select the most appropriate ICD-10-CM code from the given choices.
You must respond with only A, B, C, or D followed by a brief explanation of your reasoning.""",
    
    "HCPCS": """You are a medical coding expert specializing in HCPCS (Healthcare Common Procedure Coding System) codes.
You have extensive knowledge of medical supplies, equipment, and procedures covered by HCPCS codes.
Analyze each question carefully and select the most appropriate HCPCS code from the given choices.
You must respond with only A, B, C, or D followed by a brief explanation of your reasoning.""",
    
    "other": """You are a medical expert with comprehensive knowledge of medical terminology, anatomy, physiology, and healthcare procedures.
Analyze each question carefully and select the most appropriate answer from the given choices.
You must respond with only A, B, C, or D followed by a brief explanation of your reasoning."""
}

# File paths
QUESTIONS_FILE = "question_banks/test_1/test_1_questions.json"
RESULTS_DIR = "medical_board_judgements"

# Testing configuration
MAX_RETRIES = 3
REQUEST_TIMEOUT = 60
RATE_LIMIT_DELAY = 1  # seconds between requests 