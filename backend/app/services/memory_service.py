"""
Cortex - Unified Memory Service
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal
from app.models.memory import Note
from app.services.graph_service import graph_service
import json
import redis.asyncio as redis
from app.core.config import settings
from app.services.vector_service import vector_service

QUEUE_NAME = "cortex_memory_queue"


class MemoryService:
    
    async def add_note(self, content: str, source: str = "user") -> Dict[str, Any]:
        """
        Add a raw note to TimeDB (Episodic Memory).
        """
        async with AsyncSessionLocal() as session:
            note = Note(content=content, source=source)
            session.add(note)
            await session.commit()
            await session.refresh(note)
            
            # Trigger Background Worker
            try:
                redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                task = {
                    "note_id": note.id, 
                    "content": note.content,
                    "source": note.source,
                    "timestamp": note.created_at.isoformat()
                }
                await redis_client.lpush(QUEUE_NAME, json.dumps(task))
                await redis_client.aclose() # Close connection (or use pool)
            except Exception as e:
                print(f"⚠️ Failed to queue background task: {e}")

            return {
                "id": note.id,
                "content": note.content,
                "timestamp": note.created_at,
                "status": "saved_and_queued"
            }

    async def get_recent_notes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve recent notes from TimeDB.
        """
        async with AsyncSessionLocal() as session:
            query = select(Note).order_by(Note.created_at.desc()).limit(limit)
            result = await session.execute(query)
            notes = result.scalars().all()
            
            return [
                {
                    "id": n.id,
                    "content": n.content,
                    "timestamp": n.created_at,
                    "source": n.source
                } 
                for n in notes
            ]

    async def search_graph(self, query: str) -> List[Dict[str, Any]]:
        """
        Semantic/Graph Search (GraphRAG).
        1. Vector Search for relevant 'Thoughts'
        2. Graph Traversal to find connected Entities
        """
        # 1. Get Vector Results (Semantic Match)
        # "BGP Issues" -> matches Thought("Network outage in NY...")
        embedding = await vector_service.get_embedding(query)
        if not embedding:
             # Fallback to Text Search if no embedding available
             cypher = """
             MATCH (n:Entity)
             WHERE n.name CONTAINS $query
             RETURN n AS node, 1.0 AS score LIMIT 5
             """
             return await graph_service.execute_query(cypher, {"query": query})

        # 2. Hybrid GraphRAG Query
        # Find Thoughts similar to query, then grab the Entities they talk about.
        cypher = """
        CALL db.index.vector.queryNodes('thought_embeddings', 5, $embedding)
        YIELD node AS thought, score
        
        // Traverse to find context
        MATCH (thought)-[:MENTIONS]->(entity:Entity)
        OPTIONAL MATCH (thought)-[:TRIGGERED_REFLECTION]->(reflection:Reflection)
        
        // Return aggregated result
        RETURN 
            thought.content AS thought_content,
            score AS similarity,
            collect(DISTINCT entity.name) AS related_entities,
            collect(DISTINCT reflection.content) AS reflections
        """
        return await graph_service.execute_query(cypher, {"embedding": embedding})

memory_service = MemoryService()
