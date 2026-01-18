"""
Cortex - Router Agent (The Gateway)
Now uses LangGraph for agent orchestration.
"""

from fastapi import APIRouter
from typing import Optional

from app.models.api_schemas import ThoughtRequest, ThoughtResponse, RouteClassification
from app.agents.cognitive_graph import run_cortex


router = APIRouter()


@router.post("/think", response_model=ThoughtResponse)
async def think(request: ThoughtRequest, thread_id: Optional[str] = None):
    """
    Main entry point - process user input through the LangGraph cognitive pipeline.
    
    Uses the Sense-Think-Act loop:
    1. SENSE: Sanitize PII, Classify Intent
    2. THINK: Retrieve Context, Process with Agent
    3. ACT: Consolidate memory, Return response
    """
    user_input = request.thought.strip()
    
    # Use provided thread_id or default
    conversation_thread = thread_id or "default"
    
    # Run through the LangGraph pipeline
    result = await run_cortex(user_input, thread_id=conversation_thread)
    
    # Extract raw data
    raw_entities = result.get("extraction", {}).get("entities", {})
    raw_categories = result.get("extraction", {}).get("categories", [])
    
    # Transform entities (Dict -> List[EntityModel])
    formatted_entities = []
    
    # Handle dictionary format {type: [names]}
    if isinstance(raw_entities, dict):
        for entity_type, names in raw_entities.items():
            if isinstance(names, list):
                for name in names:
                    formatted_entities.append({
                        "name": str(name),
                        "type": str(entity_type).capitalize(), # e.g. "Persons"
                        "description": ""
                    })
    # Handle list format (if simple list of strings)
    elif isinstance(raw_entities, list):
        for entity in raw_entities:
            if isinstance(entity, str):
                formatted_entities.append({"name": entity, "type": "Unknown"})
            elif isinstance(entity, dict):
                formatted_entities.append(entity)
                
    # Transform categories (List[str] -> List[CategoryModel])
    formatted_categories = []
    for cat in raw_categories:
        if isinstance(cat, str):
            formatted_categories.append({"name": cat, "confidence": 1.0})
        elif isinstance(cat, dict):
            formatted_categories.append(cat)

    # Format response
    return ThoughtResponse(
        thought_id=result.get("thought_id", ""),
        response=result.get("response", "I couldn't process that."),
        analysis=result.get("reasoning", ""),
        entities=formatted_entities,
        categories=formatted_categories,
        summary=result.get("extraction", {}).get("summary", ""),
        route=result.get("intent", "THOUGHT")
    )


@router.get("/classify")
async def classify_debug(input: str):
    """Debug endpoint - classify intent without full processing."""
    from app.core.llm_tier import llm_router
    
    classification = await llm_router.classify_intent(input)
    return RouteClassification(
        route=classification.get("intent", "THOUGHT"),
        input=input
    )


@router.get("/brain/stats")
async def brain_stats():
    """Get brain statistics for the dashboard."""
    from app.services.graph_service import get_brain_stats
    return await get_brain_stats()


@router.get("/brain/search")
async def brain_search(q: str):
    """Semantic search across thoughts."""
    from app.services.vector_service import search_similar
    results = await search_similar(q, limit=10)
    return {"query": q, "results": results}


@router.get("/graph")
async def get_graph_data():
    """Get knowledge graph data for visualization."""
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    nodes = []
    edges = []
    
    async with driver.session() as session:
        # Get all nodes (limited)
        result = await session.run("""
            MATCH (n)
            WHERE n:Thought OR n:Entity OR n:Category
            RETURN id(n) as id, labels(n)[0] as type, 
                   coalesce(n.name, n.summary, n.title, 'Node') as label
            LIMIT 100
        """)
        nodes = [{"id": str(r["id"]), "type": r["type"], "label": r["label"]} 
                 for r in await result.data()]
        
        # Get relationships
        result = await session.run("""
            MATCH (a)-[r]->(b)
            WHERE (a:Thought OR a:Entity) AND (b:Thought OR b:Entity OR b:Category)
            RETURN id(a) as source, id(b) as target, type(r) as type
            LIMIT 200
        """)
        edges = [{"source": str(r["source"]), "target": str(r["target"]), "type": r["type"]} 
                 for r in await result.data()]
    
    return {"nodes": nodes, "edges": edges}


@router.get("/graph/route-path")
async def get_last_route_path():
    """Debug endpoint - see which nodes were visited in the last request."""
    return {"message": "Route path tracking available via thread_id"}
