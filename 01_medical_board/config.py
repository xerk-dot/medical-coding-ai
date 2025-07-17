"""
Configuration for the Medical Board AI Testing System
"""
import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# AI Models Configuration - The Medical AI Panel (ordered by cost - cheapest first)
# Updated with Summer 2025 OpenRouter pricing
AI_DOCTORS: Dict[str, Dict[str, str]] = {
   """  "grok_4": {
        "model_id": "x-ai/grok-4",
        "display_name": "Dr. Grok the 4th",
        "short_name": "grok_4",
        "cost_tier": 5,  # $0.15/$0.60 per M tokens
        "cost_note": "$3.00/$15.00 per M tokens"
    }, 
    "kim_k2": {
        "model_id": "moonshootai/kimi-k2",
        "display_name": "Dr. Kimi K2",
        "short_name": "kim_k2",
        "cost_tier": 2,  # $0.15/$0.60 per M tokens
        "cost_note": "$0.14/M input, $2.49/M output"
    },
    
    "gemini_2_5_flash": {
        "model_id": "google/gemini-2.5-flash",
        "display_name": "Dr. Gemini Flash the 2.5th",
        "short_name": "gemini_2_5_flash",
        "cost_tier": 1,  # $0.15/$0.60 per M tokens
        "cost_note": "$0.15/$0.60 per M tokens"
    },"""
    "deepseek_v3": {
        "model_id": "deepseek/deepseek-chat-v3-0324",
        "display_name": "Dr. DeepSeek V3",
        "short_name": "deepseek_v3",
        "cost_tier": 2,  # $0.28/$0.88 per M tokens
        "cost_note": "$0.28/$0.88 per M tokens"
    },
    "mistral_medium": {
        "model_id": "mistralai/mistral-medium-3",
        "display_name": "Dr. Mistral Medium",
        "short_name": "mistral_medium",
        "cost_tier": 3,  # $0.40/$2.00 per M tokens
        "cost_note": "$0.40/$2.00 per M tokens"
    },
    "gpt_4_1": {
        "model_id": "openai/gpt-4.1",
        "display_name": "Dr. GPT 4.1",
        "short_name": "gpt_4_1",
        "cost_tier": 4,  # $2.00/$8.00 per M tokens
        "cost_note": "$2.00/$8.00 per M tokens"
    },
    "gpt_4o": {
        "model_id": "openai/gpt-4o",
        "display_name": "Dr. GPT 4o",
        "short_name": "gpt_4o",
        "cost_tier": 5,  # $2.50/$10.00 per M tokens
        "cost_note": "$2.50/$10.00 per M tokens"
    },
    "gpt_4_1_mini": {
        "model_id": "openai/gpt-4.1-mini",
        "display_name": "Dr. GPT 4.1 Mini",
        "short_name": "gpt_4_1_mini",
        "cost_tier": 3,  # $0.40/$1.60 per M tokens
        "cost_note": "$0.40/$1.60 per M tokens"
    },
    "gpt_4o_mini": {
        "model_id": "openai/gpt-4o-mini",
        "display_name": "Dr. GPT 4o Mini",
        "short_name": "gpt_4o_mini",
        "cost_tier": 1,  # $0.15/$0.60 per M tokens
        "cost_note": "$0.15/$0.60 per M tokens"
    },
    # "claude_sonnet_4": {
    #     "model_id": "anthropic/claude-sonnet-4",
    #     "display_name": "Dr. Claude Sonnet the 4th",
    #     "short_name": "claude_sonnet_4",
    #     "cost_tier": 6,  # $3.00/$15.00 per M tokens
    #     "cost_note": "$3.00/$15.00 per M tokens"
    # },
    # "claude_sonnet_3.5": {
    #     "model_id": "anthropic/claude-3.5-sonnet",
    #     "display_name": "Dr. Claude Sonnet the 3.5th",
    #     "short_name": "claude_sonnet_3.5",
    #     "cost_tier": 6,  # $3.00/$15.00 per M tokens
    #     "cost_note": "$3.00/$15.00 per M tokens"
    # },
    # "claude_sonnet_3.7": {
    #     "model_id": "anthropic/claude-3.7-sonnet",
    #     "display_name": "Dr. Claude Sonnet the 3.7th",
    #     "short_name": "claude_sonnet_3.7",
    #     "cost_tier": 6,  # $3.00/$15.00 per M tokens
    #     "cost_note": "$3.00/$15.00 per M tokens"
    # },
    # "gemini_2_5_pro": {
    #     "model_id": "google/gemini-2.5-pro",
    #     "display_name": "Dr. Gemini Pro the 2.5th",
    #     "short_name": "gemini_2_5_pro",
    #     "cost_tier": 6,  # Similar to Claude pricing
    #     "cost_note": "~$3.00/$15.00 per M tokens"
    # },
    # "gemini_2_5_flash_preview": {
    #     "model_id": "google/gemini-2.5-flash-preview-05-20",
    #     "display_name": "Dr. Gemini Flash Preview the 2.5th",
    #     "short_name": "gemini_2_5_flash_preview",
    #     "cost_tier": 1,  # $3.00/$15.00 per M tokens
    #     "cost_note": "$0.15/$0.60 per M tokens"
    # }
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
QUESTIONS_FILE = "../00_question_banks/final_questions.json"
RESULTS_DIR = "../02_test_attempts"

# Testing configuration
MAX_RETRIES = 3
REQUEST_TIMEOUT = 60
RATE_LIMIT_DELAY = 0.5  # Reduced for parallel processing
PARALLEL_WORKERS = 10  # Max concurrent requests per doctor 