"""
Cortex - Core LLM Client
Basic wrapper for LLMs with Langfuse observability.
"""

from typing import Optional, List, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks import BaseCallbackHandler

from app.core.config import settings

# Optional Langfuse import
try:
    from langfuse.callback import CallbackHandler as LangfuseHandler
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    LangfuseHandler = None


class LLMClient:
    """
    Basic LLM Client with Langfuse observability.
    """
    
    def __init__(self):
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
    
    def _get_callbacks(self, session_id: Optional[str] = None) -> List[BaseCallbackHandler]:
        """
        Get callback handlers for LLM invocations.
        """
        if session_id and LANGFUSE_AVAILABLE and settings.LANGFUSE_PUBLIC_KEY:
            try:
                # Create a fresh handler for this session
                return [LangfuseHandler(
                    public_key=settings.LANGFUSE_PUBLIC_KEY,
                    secret_key=settings.LANGFUSE_SECRET_KEY,
                    host=settings.LANGFUSE_HOST,
                    session_id=session_id
                )]
            except Exception as e:
                print(f"⚠️ Failed to create scoped Langfuse handler: {e}")
                
        # Fallback to global handler
        if self._langfuse_handler:
            return [self._langfuse_handler]
        return []

    async def chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        session_id: Optional[str] = None,
        model_name: str = "gpt-4o"
    ) -> str:
        """
        Simple chat invocation.
        """
        try:
            if not settings.OPENAI_API_KEY:
                 return "⚠️ OpenAI API Key not configured."

            llm = ChatOpenAI(
                model=model_name,
                api_key=settings.OPENAI_API_KEY,
                temperature=0.7
            )
            
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))
            
            callbacks = self._get_callbacks(session_id=session_id)
            response = await llm.ainvoke(messages, config={"callbacks": callbacks})
            
            return response.content
            
        except Exception as e:
            print(f"LLM Error: {e}")
            return f"Error interacting with LLM: {str(e)}"

# Singleton
llm_client = LLMClient()
