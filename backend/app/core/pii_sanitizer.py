"""
Cortex - PII Sanitizer
Uses Advanced LLM (Claude) to detect and redact sensitive information.
"""

from typing import Tuple, Dict
from app.services.llm_service import get_llm

SANITIZER_SYSTEM_PROMPT = """You are a PII and Secret Sanitizer.
Your goal is to inspect the USER INPUT and redact any sensitive information such as:
- API Keys (AWS, Stripe, OpenAI, etc.)
- Passwords / Secrets
- Credit Card Numbers
- Social Security Numbers
- Private Addresses

Rules:
1. Replace the sensitive part with [REDACTED].
2. Return ONLY the sanitized string. Do not explain.
3. If no secrets are found, return the input exactly as is.

Example:
Input: "Here is my key sk-12345"
Output: "Here is my key [REDACTED]"
"""

async def sanitize_input(text: str) -> str:
    """
    Check text for secrets using Claude and redact them.
    """
    if not text or len(text) < 10:
        return text

    # Use 'smart' tier (Claude) for high-accuracy detection
    llm = get_llm(tier="smart", temperature=0)
    
    try:
        response = await llm.ainvoke([
            ("system", SANITIZER_SYSTEM_PROMPT),
            ("human", text)
        ])
        return response.content
    except Exception as e:
        print(f"Sanitizer Error: {e}")
        # Fail safe: return original but log error
        return text

def sanitize_for_cloud(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Sanitize text before sending to cloud LLMs (Synchronous for now).
    Returns (sanitized_text, reconstruction_mapping).
    
    TODO: Implement robust local PII detection (e.g., Presidio or local Llama).
    Currently a pass-through to unblock system startup.
    """
    return text, {}

def deanonymize_response(text: str, mapping: Dict[str, str]) -> str:
    """
    Restore real values in the response using the mapping.
    """
    if not mapping:
        return text
        
    for placeholder, original_value in mapping.items():
        text = text.replace(placeholder, original_value)
        
    return text
