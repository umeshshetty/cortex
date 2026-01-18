"""
Cortex - Tiered LLM Router
Multi-model router based on task requirements.

Tiers:
- Reflex: Llama (Local) - Intent classification, fast responses
- Private: Mistral (Local) - Journaling, private data
- Logic: GPT-4o (Cloud) - Scheduling, complex queries
- Empathy: Claude (Cloud) - Social analysis, tone calibration
"""

from typing import Optional, Dict, Any, Literal, List
from enum import Enum
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks import BaseCallbackHandler

from app.core.config import settings
from app.core.pii_sanitizer import sanitize_for_cloud, deanonymize_response


# Optional Langfuse import
try:
    from langfuse.callback import CallbackHandler as LangfuseHandler
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    LangfuseHandler = None


class LLMTier(str, Enum):
    """Available LLM tiers."""
    REFLEX = "reflex"     # Local, fast, no privacy concern
    PRIVATE = "private"   # Local, privacy-critical data
    LOGIC = "logic"       # Cloud, complex reasoning
    EMPATHY = "empathy"   # Cloud, emotional intelligence


class TieredLLMRouter:
    """
    Hybrid Inference Stack - Routes requests to appropriate LLM tier.
    
    Tier Selection:
    - REFLEX: Intent classification, entity extraction (< 200ms)
    - PRIVATE: Journaling, private thoughts (never leaves localhost)
    - LOGIC: Scheduling, Cypher queries (strict syntax accuracy)
    - EMPATHY: Social analysis, sensitive advice (highest EQ)
    """
    
    def __init__(self):
        self._models: Dict[LLMTier, Any] = {}
        self._pii_mappings: Dict[str, Dict[str, str]] = {}
        self._langfuse_handler: Optional[BaseCallbackHandler] = None
        
        # Initialize Langfuse if configured
        if LANGFUSE_AVAILABLE and settings.LANGFUSE_PUBLIC_KEY:
            try:
                self._langfuse_handler = LangfuseHandler(
                    public_key=settings.LANGFUSE_PUBLIC_KEY,
                    secret_key=settings.LANGFUSE_SECRET_KEY,
                    host=settings.LANGFUSE_HOST
                )
                print("✅ Langfuse observability enabled")
            except Exception as e:
                print(f"⚠️ Langfuse init failed: {e}")
    
    def _get_callbacks(self) -> List[BaseCallbackHandler]:
        """Get callback handlers for LLM invocations."""
        if self._langfuse_handler:
            return [self._langfuse_handler]
        return []
    
    def _get_model(self, tier: LLMTier):
        """Lazy load models on first use."""
        if tier not in self._models:
            if tier == LLMTier.REFLEX:
                # Use configured model for fast local inference
                self._models[tier] = ChatOllama(
                    model=settings.OLLAMA_MODEL,  # Use configured model
                    base_url=settings.OLLAMA_BASE_URL,
                    temperature=0
                )
            elif tier == LLMTier.PRIVATE:
                # Larger local model for privacy-critical tasks
                self._models[tier] = ChatOllama(
                    model=settings.OLLAMA_MODEL,
                    base_url=settings.OLLAMA_BASE_URL,
                    temperature=0.7
                )
            elif tier == LLMTier.LOGIC:
                # GPT-4o for complex reasoning
                if settings.OPENAI_API_KEY:
                    self._models[tier] = ChatOpenAI(
                        model="gpt-4o",
                        api_key=settings.OPENAI_API_KEY,
                        temperature=0
                    )
                else:
                    # Fallback to local if no API key
                    self._models[tier] = self._get_model(LLMTier.PRIVATE)
            elif tier == LLMTier.EMPATHY:
                # Claude for emotional intelligence
                if settings.ANTHROPIC_API_KEY:
                    self._models[tier] = ChatAnthropic(
                        model="claude-3-5-sonnet-20241022",
                        api_key=settings.ANTHROPIC_API_KEY,
                        temperature=0.7
                    )
                else:
                    # Fallback to local if no API key
                    self._models[tier] = self._get_model(LLMTier.PRIVATE)
        
        return self._models[tier]
    
    async def invoke(
        self,
        tier: LLMTier,
        prompt: str,
        system_prompt: Optional[str] = None,
        sanitize_pii: bool = True,
        request_id: Optional[str] = None
    ) -> str:
        """
        Invoke the appropriate LLM tier.
        
        Args:
            tier: Which tier to use
            prompt: The user prompt
            system_prompt: Optional system message
            sanitize_pii: Whether to sanitize PII for cloud models
            request_id: Request ID for PII mapping tracking
            
        Returns:
            LLM response (de-anonymized if PII was sanitized)
        """
        model = self._get_model(tier)
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        
        # PII sanitization for cloud models
        pii_mapping = {}
        if sanitize_pii and tier in [LLMTier.LOGIC, LLMTier.EMPATHY]:
            sanitized_prompt, pii_mapping = sanitize_for_cloud(prompt)
            if request_id:
                self._pii_mappings[request_id] = pii_mapping
            messages.append(HumanMessage(content=sanitized_prompt))
        else:
            messages.append(HumanMessage(content=prompt))
        
        # Invoke model with callbacks for observability
        callbacks = self._get_callbacks()
        response = await model.ainvoke(messages, config={"callbacks": callbacks})
        result = response.content
        
        # De-anonymize response if needed
        if pii_mapping:
            result = deanonymize_response(result, pii_mapping)
        
        return result
    
    async def classify_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Fast intent classification using REFLEX tier.
        
        Returns:
            Dict with intent, urgency, entities
        """
        # Fast-path for obvious greetings (no need to call LLM)
        simple_greetings = [
            "hello", "hi", "hey", "good morning", "good afternoon", 
            "good evening", "howdy", "yo", "sup", "what's up", 
            "hola", "greetings", "hii", "heya", "hi there"
        ]
        input_lower = user_input.lower().strip()
        
        # Check if it's a simple greeting (possibly with punctuation)
        clean_input = input_lower.rstrip('!?.')
        if clean_input in simple_greetings or len(input_lower) <= 3:
            return {
                "intent": "SIMPLE",
                "urgency": 1,
                "entities": {},
                "privacy_level": "public"
            }
        
        system = """You are an intent classifier. Classify the user input.

IMPORTANT: Simple greetings like "hello", "hi", "hey" should be classified as SIMPLE.
        
Output ONLY valid JSON:
{
    "intent": "SCHEDULING" | "TASK" | "QUERY" | "SOCIAL" | "JOURNAL" | "SIMPLE",
    "urgency": 1-10,
    "entities": {
        "persons": [],
        "times": [],
        "projects": []
    },
    "privacy_level": "public" | "private"
}"""
        
        response = await self.invoke(
            tier=LLMTier.REFLEX,
            prompt=user_input,
            system_prompt=system,
            sanitize_pii=False  # Local model, no sanitization needed
        )
        
        # Parse JSON response
        import json
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        
        # Default fallback
        return {
            "intent": "QUERY",
            "urgency": 5,
            "entities": {},
            "privacy_level": "public"
        }
    
    def select_tier(self, classification: Dict) -> LLMTier:
        """
        Select appropriate tier based on classification.
        """
        intent = classification.get("intent", "QUERY")
        privacy = classification.get("privacy_level", "public")
        
        # Privacy-sensitive content stays local
        if privacy == "private" or intent == "JOURNAL":
            return LLMTier.PRIVATE
        
        # Scheduling needs strict logic
        if intent == "SCHEDULING":
            return LLMTier.LOGIC
        
        # Social intent needs empathy
        if intent == "SOCIAL":
            return LLMTier.EMPATHY
        
        # Simple queries use fast tier
        if intent == "SIMPLE" or classification.get("urgency", 5) <= 3:
            return LLMTier.REFLEX
        
        # Default to logic for complex queries
        return LLMTier.LOGIC


# Singleton instance
llm_router = TieredLLMRouter()


async def smart_invoke(
    prompt: str,
    system_prompt: Optional[str] = None,
    force_tier: Optional[LLMTier] = None
) -> str:
    """
    Convenience function for smart LLM invocation.
    Automatically selects the best tier based on content.
    """
    if force_tier:
        return await llm_router.invoke(force_tier, prompt, system_prompt)
    
    # Classify first
    classification = await llm_router.classify_intent(prompt)
    tier = llm_router.select_tier(classification)
    
    return await llm_router.invoke(tier, prompt, system_prompt)
