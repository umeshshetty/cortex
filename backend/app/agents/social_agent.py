"""
Cortex - Social Agent
People, relationships, and connection suggestions.
"""

import json
from typing import Dict, Any, List
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.core.prompts import SOCIAL_GRAPH_PROMPT
from app.services.graph_service import (
    get_person_profile,
    update_person_profile,
    get_all_people,
    create_connection
)


async def analyze_social_context(thought: str, existing_people: List[Dict]) -> Dict[str, Any]:
    """
    Analyze thought for people mentions and relationship updates.
    """
    llm = ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0
    )
    
    people_context = "\n".join([
        f"- {p['name']}: {p.get('role', 'Unknown')} ({p.get('relationship', 'Unknown')})"
        for p in existing_people[:10]  # Limit to top 10
    ])
    
    prompt = f"""{SOCIAL_GRAPH_PROMPT}

Known people:
{people_context or "No existing contacts"}

New thought: {thought}

Analysis (JSON):"""
    
    response = await llm.ainvoke(prompt)
    
    try:
        content = response.content
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end > start:
            analysis = json.loads(content[start:end])
        else:
            analysis = {"people_mentioned": [], "connection_suggestions": [], "profile_updates": []}
    except json.JSONDecodeError:
        analysis = {"people_mentioned": [], "connection_suggestions": [], "profile_updates": []}
    
    return analysis


async def handle_social_request(user_input: str) -> Dict[str, Any]:
    """
    Handle social/relationship focused requests.
    """
    # Step 1: Get existing people from graph
    existing_people = await get_all_people()
    
    # Step 2: Analyze for social context
    analysis = await analyze_social_context(user_input, existing_people)
    
    # Step 3: Apply profile updates
    for update in analysis.get("profile_updates", []):
        await update_person_profile(
            name=update.get("name"),
            updates={"context": update.get("update")}
        )
    
    # Step 4: Create new connections
    for suggestion in analysis.get("connection_suggestions", []):
        await create_connection(
            from_entity=suggestion.get("from"),
            to_entity=suggestion.get("to"),
            relationship_type="CONNECTED_TO",
            reason=suggestion.get("reason", "")
        )
    
    # Step 5: Generate response
    llm = ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.7
    )
    
    people_mentioned = analysis.get("people_mentioned", [])
    connections = analysis.get("connection_suggestions", [])
    
    response_prompt = f"""Social analysis complete.

People mentioned: {len(people_mentioned)}
{chr(10).join([f"- {p['name']}: {p.get('role', '')} ({p.get('context', '')})" for p in people_mentioned[:5]])}

Connection suggestions: {len(connections)}
{chr(10).join([f"- Connect {c['from']} with {c['to']}: {c.get('reason', '')}" for c in connections[:3]])}

Provide a brief, helpful summary of the social insights."""
    
    response = await llm.ainvoke(response_prompt)
    
    return {
        "thought_id": "",
        "response": response.content,
        "analysis": f"Found {len(people_mentioned)} people, {len(connections)} connection suggestions",
        "entities": [{"name": p["name"], "type": "Person"} for p in people_mentioned],
        "categories": ["Social"],
        "summary": ""
    }


async def get_person_insights(name: str) -> Dict[str, Any]:
    """
    Get comprehensive insights about a person.
    """
    profile = await get_person_profile(name)
    
    if not profile:
        return {"error": f"No profile found for {name}"}
    
    return {
        "name": profile.get("name"),
        "role": profile.get("role", "Unknown"),
        "relationship": profile.get("relationship", "Unknown"),
        "topics": profile.get("topics", []),
        "last_interaction": profile.get("last_interaction"),
        "interaction_count": profile.get("interaction_count", 0)
    }
