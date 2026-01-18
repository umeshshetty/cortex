"""
Cortex - Centralized Dependencies
Database connections (Neo4j, Redis) with dependency injection.
"""

from typing import Optional
from neo4j import AsyncGraphDatabase, AsyncDriver
from redis.asyncio import Redis
from app.core.config import settings


# Global connection instances
_neo4j_driver: Optional[AsyncDriver] = None
_redis_client: Optional[Redis] = None


# =============================================================================
# Neo4j Connection
# =============================================================================

async def init_neo4j() -> None:
    """Initialize Neo4j async driver."""
    global _neo4j_driver
    _neo4j_driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
    )
    # Verify connectivity
    async with _neo4j_driver.session() as session:
        await session.run("RETURN 1")
    print(f"✅ Neo4j connected: {settings.NEO4J_URI}")


async def get_neo4j() -> AsyncDriver:
    """Dependency injection for Neo4j driver."""
    if _neo4j_driver is None:
        raise RuntimeError("Neo4j not initialized. Call init_neo4j() first.")
    return _neo4j_driver


# =============================================================================
# Redis Connection (Working Memory)
# =============================================================================

async def init_redis() -> None:
    """Initialize Redis async client."""
    global _redis_client
    _redis_client = Redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    # Verify connectivity
    await _redis_client.ping()
    print(f"✅ Redis connected: {settings.REDIS_URL}")


async def get_redis() -> Redis:
    """Dependency injection for Redis client."""
    if _redis_client is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis_client


# =============================================================================
# Cleanup
# =============================================================================

async def close_connections() -> None:
    """Close all database connections."""
    global _neo4j_driver, _redis_client
    
    if _neo4j_driver:
        await _neo4j_driver.close()
        _neo4j_driver = None
        print("🔌 Neo4j connection closed")
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        print("🔌 Redis connection closed")
