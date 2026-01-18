"""
Cortex - Unified Memory Service
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal
from app.models.memory import Note
from app.services.graph_service import graph_service

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
            
            # FUTURE: Trigger GraphRAG indexing here (background task)
            
            return {
                "id": note.id,
                "content": note.content,
                "timestamp": note.created_at,
                "status": "saved"
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
        Semantic/Graph Search (Placeholder for full GraphRAG).
        """
        # For now, just a simple Cypher query example
        # In real GraphRAG, this would do vector search + traversal
        cypher = """
        MATCH (n:Entity)
        WHERE n.name CONTAINS $query
        RETURN n LIMIT 5
        """
        return await graph_service.execute_query(cypher, {"query": query})

memory_service = MemoryService()
