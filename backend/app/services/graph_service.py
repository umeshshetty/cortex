"""
Cortex - Graph Service (Neo4j)
"""

from typing import Optional, Dict, Any, List
from neo4j import AsyncGraphDatabase, AsyncDriver

from app.core.config import settings

class GraphService:
    _driver: Optional[AsyncDriver] = None

    @classmethod
    async def connect(cls):
        """Initialize Neo4j driver."""
        if not cls._driver:
            cls._driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            
    @classmethod
    async def close(cls):
        """Close Neo4j driver."""
        if cls._driver:
            await cls._driver.close()
            cls._driver = None

    @classmethod
    async def get_driver(cls) -> AsyncDriver:
        if not cls._driver:
            await cls.connect()
        return cls._driver
    
    @classmethod
    async def execute_query(cls, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute Cypher query and return list of records."""
        if parameters is None:
            parameters = {}
            
        driver = await cls.get_driver()
        async with driver.session() as session:
            result = await session.run(query, parameters)
            records = [record.data() async for record in result]
            return records

graph_service = GraphService()
