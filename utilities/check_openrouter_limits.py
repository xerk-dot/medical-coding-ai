#!/usr/bin/env python3
"""
Check OpenRouter API key limits and usage
"""

import os
import requests
import json
from datetime import datetime
import dotenv

dotenv.load_dotenv()

def check_openrouter_limits():
    """Check OpenRouter API key limits and usage"""
    
    # Get API key from environment
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY environment variable not set")
        return
    
    try:
        # Make request to OpenRouter auth endpoint
        response = requests.get(
            'https://openrouter.ai/api/v1/auth/key',
            headers={
                'Authorization': f'Bearer {api_key}',
            }
        )
        
        if response.status_code == 200:
            data = response.json()['data']
            
            print("🔑 OpenRouter API Key Status")
            print("=" * 40)
            print(f"Label: {data.get('label', 'N/A')}")
            print(f"Usage: ${data.get('usage', 0):.4f}")
            
            limit = data.get('limit')
            if limit is not None:
                print(f"Limit: ${limit:.4f}")
                remaining = limit - data.get('usage', 0)
                print(f"Remaining: ${remaining:.4f}")
                
                if remaining < 1.0:
                    print("⚠️  WARNING: Less than $1.00 remaining!")
                elif remaining < 5.0:
                    print("⚠️  WARNING: Less than $5.00 remaining!")
                else:
                    print("✅ Credits look good")
            else:
                print("Limit: Unlimited")
            
            print(f"Free Tier: {'Yes' if data.get('is_free_tier', False) else 'No'}")
            
            # Rate limit info (if available)
            if 'rate_limit' in data:
                print(f"Rate Limit: {data['rate_limit']}")
            
        else:
            print(f"❌ Error checking API key: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_openrouter_limits()