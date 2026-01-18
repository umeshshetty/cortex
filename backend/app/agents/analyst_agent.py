"""
Cortex - Analyst Agent
Knowledge extraction, RAG queries, and graph traversal.
"""

import json
from typing import Dict, Any, List
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.core.prompts import ANALYST_EXTRACTION_PROMPT, ANALYST_RESPONSE_PROMPT
from app.services.graph_service import save_thought, get_related_context
from app.services.vector_service import search_similar, add_embedding


async def extract_knowledge(thought: str) -> Dict[str, Any]:
    """
    Extract structured knowledge from a thought.
    Returns entities, categories, action items, etc.
    """
    llm = ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0
    )
    
    prompt = f"{ANALYST_EXTRACTION_PROMPT}\n\nThought: {thought}\n\nExtraction (JSON):"
    
    response = await llm.ainvoke(prompt)
    
    # Parse JSON response
    try:
        # Find JSON in response
        content = response.content
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end > start:
            extraction = json.loads(content[start:end])
        else:
            extraction = {
                "summary": thought[:100],
                "entities": [],
                "categories": ["Archive"],
                "action_items": [],
                "emotional_tone": "neutral"
            }
    except json.JSONDecodeError:
        extraction = {
            "summary": thought[:100],
            "entities": [],
            "categories": ["Archive"],
            "action_items": [],
            "emotional_tone": "neutral"
        }
    
    return extraction


async def process_thought(user_input: str) -> Dict[str, Any]:
    """
    Process a new thought - extract knowledge and store in graph.
    """
    # Step 1: Get context from existing knowledge
    context = await get_related_context(user_input)
    
    # Step 2: Extract structured knowledge
    extraction = await extract_knowledge(user_input)
    
    # Step 3: Save to graph
    thought_id = await save_thought(
        content=user_input,
        summary=extraction.get("summary", ""),
        entities=extraction.get("entities", []),
        categories=extraction.get("categories", []),
        action_items=extraction.get("action_items", [])
    )
    
    # Step 4: Add to vector store
    await add_embedding(thought_id, user_input)
    
    # Step 5: Generate response
    llm = ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.7
    )
    
    response_prompt = f"""I've stored your thought in the knowledge graph.

Extracted:
- Summary: {extraction.get('summary', 'N/A')}
- Entities: {', '.join([e['name'] for e in extraction.get('entities', [])])}
- Categories: {', '.join(extraction.get('categories', []))}
- Action Items: {len(extraction.get('action_items', []))} found

{f"Related context from your brain: {context}" if context else ""}

Briefly acknowledge what you learned and any connections you noticed."""
    
    response = await llm.ainvoke(response_prompt)
    
    return {
        "thought_id": thought_id,
        "response": response.content,
        "analysis": extraction.get("summary", ""),
        "entities": extraction.get("entities", []),
        "categories": extraction.get("categories", []),
        "summary": extraction.get("summary", "")
    }


async def answer_question(user_input: str) -> Dict[str, Any]:
    """
    Answer a question using RAG over the knowledge graph.
    """
    # Step 1: Semantic search for relevant thoughts
    similar_thoughts = await search_similar(user_input, limit=5)
    
    # Step 2: Graph traversal for connected entities
    graph_context = await get_related_context(user_input)
    
    # Step 3: Combine context
    combined_context = ""
    if similar_thoughts:
        combined_context += "From semantic search:\n"
        for t in similar_thoughts:
            combined_context += f"- {t['content'][:200]}...\n"
    
    if graph_context:
        combined_context += f"\nFrom knowledge graph:\n{graph_context}"
    
    # Step 4: Generate answer
    llm = ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.7
    )
    
    prompt = ANALYST_RESPONSE_PROMPT.format(context=combined_context or "No relevant context found.")
    full_prompt = f"{prompt}\n\nUser question: {user_input}\n\nResponse:"
    
    response = await llm.ainvoke(full_prompt)
    
    return {
        "thought_id": "",
        "response": response.content,
        "analysis": f"Retrieved {len(similar_thoughts)} similar thoughts",
        "entities": [],
        "categories": [],
        "summary": ""
    }
