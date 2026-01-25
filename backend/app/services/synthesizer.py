"""
Cortex - Synthesizer Service
Orchestrates Retrieval Augmented Generation (RAG).
Connects the 'Memory' (Retriever) to the 'voice' (LLM).
"""

from langchain_core.messages import HumanMessage
from app.core.agent import cortex_agent

class SynthesizerService:
    
    async def synthesize_answer(self, query: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Agentic RAG:
        Delegates the query to the LangGraph Agent.
        The Agent will decide when/if to call `search_memory`.
        """
        print(f"🤖 Agent: Processing '{query}'...")
        
        # Invoke Agent
        inputs = {"messages": [HumanMessage(content=query)]}
        result = await cortex_agent.ainvoke(inputs)
        
        # Extract final answer
        final_message = result["messages"][-1]
        answer = final_message.content
        
        return {
            "query": query,
            "answer": answer,
            "mode": "agentic" # Signal to UI that this was an agent response
        }

synthesizer_service = SynthesizerService()
