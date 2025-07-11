"""
AI Client for OpenRouter API communication
"""
import json
import time
import requests
from typing import Dict, Optional, Tuple
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MAX_RETRIES, REQUEST_TIMEOUT, RATE_LIMIT_DELAY


class AIClient:
    """Client for communicating with AI models through OpenRouter API"""
    
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/xerk-dot/medical-coding-ai",
            "X-Title": "Medical Coding AI Board"
        })
    
    def ask_question(self, model_id: str, system_prompt: str, question: str, choices: Dict[str, str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Ask a question to an AI model and get the response
        
        Args:
            model_id: The model identifier for OpenRouter
            system_prompt: System prompt based on question type
            question: The medical coding question
            choices: Dict with A, B, C, D choices
            
        Returns:
            Tuple of (selected_choice, reasoning, raw_response)
        """
        # Format the question with choices
        formatted_question = self._format_question(question, choices)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": formatted_question}
        ]
        
        # Set model-specific token limits and configurations
        if "gemini" in model_id.lower():
            max_tokens = 3000  # Gemini models need even more tokens for reasoning
        elif "o3" in model_id:
            max_tokens = 3000  # Reasoning models need even more tokens
        else:
            max_tokens = 2000  # Default for other models
        
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": 0.1,  # Low temperature for consistent medical coding
            "max_tokens": max_tokens,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "select_answer",
                        "description": "Select the correct answer choice (A, B, C, or D) for the medical coding question",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "choice": {
                                    "type": "string",
                                    "enum": ["A", "B", "C", "D"],
                                    "description": "The selected answer choice"
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "Brief explanation of why this choice is correct"
                                }
                            },
                            "required": ["choice", "reasoning"]
                        }
                    }
                }
            ],
            "tool_choice": {"type": "function", "function": {"name": "select_answer"}}
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Extract the tool call result
                if "choices" in result and len(result["choices"]) > 0:
                    choice = result["choices"][0]
                    if "message" in choice and "tool_calls" in choice["message"]:
                        tool_call = choice["message"]["tool_calls"][0]
                        if tool_call["type"] == "function":
                            function_args = json.loads(tool_call["function"]["arguments"])
                            selected_choice = function_args.get("choice")
                            reasoning = function_args.get("reasoning")
                            raw_response = json.dumps(result, indent=2)
                            
                            # Validate the choice
                            if selected_choice in ["A", "B", "C", "D"]:
                                return selected_choice, reasoning, raw_response
                            else:
                                print(f"Invalid choice returned: {selected_choice}")
                
                # Fallback parsing for different response formats
                if "choices" in result and len(result["choices"]) > 0:
                    # For Gemini models: check reasoning_details first (they often put the real answer here)
                    selected_choice, reasoning = self._parse_reasoning_details(result)
                    if selected_choice:
                        return selected_choice, reasoning, json.dumps(result, indent=2)
                    
                    # Try to parse from main content
                    content = result["choices"][0]["message"]["content"]
                    if content:
                        selected_choice, reasoning = self._parse_response(content)
                        if selected_choice:
                            return selected_choice, reasoning, json.dumps(result, indent=2)
                        
                        # Try to parse JSON from content (for models that return JSON instead of tool calls)
                        selected_choice, reasoning = self._parse_json_response(content)
                        if selected_choice:
                            return selected_choice, reasoning, json.dumps(result, indent=2)
                
                print(f"Unexpected response format from {model_id}")
                print(f"Response preview: {json.dumps(result, indent=2)[:500]}...")
                return None, None, json.dumps(result, indent=2)
                
            except requests.exceptions.RequestException as e:
                print(f"Request error for {model_id} (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RATE_LIMIT_DELAY * (attempt + 1))
                else:
                    return None, f"Request failed after {MAX_RETRIES} attempts: {e}", None
            
            except json.JSONDecodeError as e:
                print(f"JSON decode error for {model_id}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RATE_LIMIT_DELAY)
                else:
                    return None, f"JSON decode failed: {e}", None
            
            except Exception as e:
                print(f"Unexpected error for {model_id}: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RATE_LIMIT_DELAY)
                else:
                    return None, f"Unexpected error: {e}", None
        
        return None, "Failed after all retry attempts", None
    
    def _format_question(self, question: str, choices: Dict[str, str]) -> str:
        """Format the question with multiple choice options"""
        formatted = f"{question}\n\n"
        for choice_letter, choice_text in choices.items():
            formatted += f"{choice_letter}: {choice_text}\n"
        
        formatted += "\nPlease use the select_answer function to choose your answer (A, B, C, or D) and provide your reasoning."
        return formatted
    
    def _parse_response(self, content: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Fallback parser for responses that don't use tool calls
        Looks for A, B, C, or D at the beginning of the response
        """
        if not content:
            return None, None
        
        content = content.strip()
        
        # Look for choice at the beginning of the response
        for choice in ["A", "B", "C", "D"]:
            if content.startswith(choice + ":") or content.startswith(choice + ".") or content.startswith(choice + ")"):
                reasoning = content[2:].strip()
                return choice, reasoning
            elif content.startswith(choice + " "):
                reasoning = content[2:].strip()
                return choice, reasoning
        
        # Look for "Answer: X" pattern
        import re
        answer_match = re.search(r'Answer:\s*([ABCD])', content, re.IGNORECASE)
        if answer_match:
            choice = answer_match.group(1).upper()
            reasoning = content
            return choice, reasoning
        
        # Look for "The answer is X" pattern
        answer_match = re.search(r'(?:the\s+)?answer\s+is\s+([ABCD])', content, re.IGNORECASE)
        if answer_match:
            choice = answer_match.group(1).upper()
            reasoning = content
            return choice, reasoning
        
        # Look for "I choose X" or "I select X" pattern
        choice_match = re.search(r'I\s+(?:choose|select)\s+([ABCD])', content, re.IGNORECASE)
        if choice_match:
            choice = choice_match.group(1).upper()
            reasoning = content
            return choice, reasoning
        
        # Look for standalone letter followed by explanation
        letter_match = re.search(r'^([ABCD])\b', content, re.IGNORECASE)
        if letter_match:
            choice = letter_match.group(1).upper()
            reasoning = content
            return choice, reasoning
        
        # Look for any mention of a choice letter in the text
        for choice in ["A", "B", "C", "D"]:
            if f" {choice} " in content or f" {choice}." in content or f" {choice}:" in content:
                # Found a choice letter, assume it's the answer
                return choice, content
        
        # Look for just the letter at the start
        if len(content) > 0 and content[0].upper() in ["A", "B", "C", "D"]:
            choice = content[0].upper()
            reasoning = content[1:].strip()
            return choice, reasoning
        
        return None, content
    
    def _parse_json_response(self, content: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse JSON response from content (for models that return JSON instead of tool calls)
        """
        if not content:
            return None, None
        
        try:
            # Look for JSON blocks in the content
            import re
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            json_match = re.search(json_pattern, content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(1)
                parsed = json.loads(json_str)
                
                choice = parsed.get("choice")
                reasoning = parsed.get("reasoning")
                
                if choice and choice in ["A", "B", "C", "D"]:
                    return choice, reasoning
            
            # Try to parse the entire content as JSON
            try:
                parsed = json.loads(content)
                choice = parsed.get("choice")
                reasoning = parsed.get("reasoning")
                
                if choice and choice in ["A", "B", "C", "D"]:
                    return choice, reasoning
            except:
                pass
                
        except Exception as e:
            print(f"Error parsing JSON response: {e}")
        
        return None, None
    
    def _parse_reasoning_details(self, result: dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse reasoning_details from Gemini models that put the actual response there
        """
        try:
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0]["message"]
                
                # Check if there's reasoning_details (Gemini format)
                if "reasoning_details" in message:
                    for detail in message["reasoning_details"]:
                        if "data" in detail:
                            # Try to decode the data if it's encrypted/encoded
                            try:
                                # For Gemini, sometimes the reasoning is in plain text
                                reasoning_text = detail["data"]
                                if isinstance(reasoning_text, str):
                                    selected_choice, reasoning = self._parse_response(reasoning_text)
                                    if selected_choice:
                                        return selected_choice, reasoning
                            except:
                                pass
                
                # Check if there's a 'reasoning' field directly in the message
                if "reasoning" in message:
                    reasoning_text = message["reasoning"]
                    if isinstance(reasoning_text, str):
                        selected_choice, reasoning = self._parse_response(reasoning_text)
                        if selected_choice:
                            return selected_choice, reasoning
                
                # Check for function call arguments in a different format
                if "function_call" in message:
                    function_call = message["function_call"]
                    if "arguments" in function_call:
                        try:
                            args = json.loads(function_call["arguments"])
                            choice = args.get("choice")
                            reasoning = args.get("reasoning")
                            if choice and choice in ["A", "B", "C", "D"]:
                                return choice, reasoning
                        except:
                            pass
                
                # Last resort: check the entire message content recursively
                content = message.get("content", "")
                if content:
                    selected_choice, reasoning = self._parse_response(content)
                    if selected_choice:
                        return selected_choice, reasoning
                        
        except Exception as e:
            print(f"Error parsing reasoning details: {e}")
        
        return None, None