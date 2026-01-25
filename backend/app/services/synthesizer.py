"""
Cortex - Synthesizer Service
Orchestrates Retrieval Augmented Generation (RAG).
Connects the 'Memory' (Retriever) to the 'voice' (LLM).
"""

from langchain_core.messages import HumanMessage, SystemMessage
from app.core.agent import cortex_agent
import re

COT_SYSTEM_PROMPT = """You are Cortex.
You must exhibit "Chain of Thought" reasoning.
Before answering, you MUST start with an <internal_monologue> section where you:
1. Analyze the user's intent.
2. Review the retrieved memory context (if any).
3. Plan your response.

Format your response exactly like this:
<internal_monologue>
[Your reasoning here]
</internal_monologue>
[Your final helpful answer to the user]
"""

class SynthesizerService:
    
    async def synthesize_answer(self, query: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Agentic RAG:
        Delegates the query to the LangGraph Agent.
        The Agent will decide when/if to call `search_memory`.
        """
        print(f"🤖 Agent: Processing '{query}'...")
        
        # Invoke Agent with System Prompt
        inputs = {"messages": [
            SystemMessage(content=COT_SYSTEM_PROMPT),
            HumanMessage(content=query)
        ]}
        result = await cortex_agent.ainvoke(inputs)
        
        # Extract final answer
        final_message = result["messages"][-1]
        raw_content = final_message.content
        
        # Parse CoT
        reasoning = ""
        answer = raw_content
        match = re.search(r"<internal_monologue>(.*?)</internal_monologue>", raw_content, re.DOTALL)
        if match:
            reasoning = match.group(1).strip()
            answer = raw_content.replace(match.group(0), "").strip()
        
        
        # Persist Conversation (Async)
        try:
            from app.services.graph_service import graph_service
            import uuid
            
            user_msg_id = str(uuid.uuid4())
            ai_msg_id = str(uuid.uuid4())
            
            cypher = """
            MERGE (s:Session {id: $session_id})
            
            CREATE (u:Message {id: $user_id, role: 'user', content: $query, timestamp: datetime()})
            CREATE (a:Message {id: $ai_id, role: 'assistant', content: $answer, reasoning: $reasoning, timestamp: datetime()})
            
            MERGE (s)-[:HAS_MESSAGE]->(u)
            MERGE (s)-[:HAS_MESSAGE]->(a)
            MERGE (u)-[:NEXT_MESSAGE]->(a)
            """
            await graph_service.execute_query(cypher, {
                "session_id": session_id,
                "user_id": user_msg_id,
                "ai_id": ai_msg_id,
                "query": query,
                "answer": answer,
                "reasoning": reasoning
            })
        except Exception as e:
            print(f"⚠️ Failed to save chat history: {e}")
            
        return {
            "query": query,
            "answer": answer,
            "reasoning": reasoning,
            "mode": "agentic" 
        }

synthesizer_service = SynthesizerService()
