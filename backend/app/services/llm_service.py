"""
Cortex - LLM Service
Centralized management for LLM clients (Ollama, Anthropic).
Routes tasks to the appropriate model tier.
"""

from typing import Optional, Literal
from langchain_ollama import ChatOllama
from langchain_anthropic import ChatAnthropic
from app.core.config import settings

ModelTier = Literal["fast", "smart"]

def get_llm(tier: ModelTier = "fast", temperature: float = 0):
    """
    Get an LLM client based on the requested tier.
    
    Args:
        tier: 'fast' (Ollama) or 'smart' (Claude)
        temperature: Creativity (0-1)
        
    Returns:
        A LangChain ChatModel instance
    """
    if tier == "smart":
        if not settings.ANTHROPIC_API_KEY:
            # Fallback to fast if no key
            print("WARNING: No ANTHROPIC_API_KEY found, falling back to Ollama.")
            return _get_ollama(temperature)
            
        return ChatAnthropic(
            model="claude-3-5-sonnet-latest",
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=temperature
        )
    
    return _get_ollama(temperature)

def _get_ollama(temperature: float):
    return ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=temperature
    )
