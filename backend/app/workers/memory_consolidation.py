"""
Cortex - Memory Consolidation Worker
The "Sleep Cycle" - runs nightly to organize and strengthen memories.

Tasks:
1. Identify redundant thoughts
2. Update entity profiles with new context
3. Strengthen important connections
4. Prune low-salience memories
5. Calculate spaced repetition schedules
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.workers.worker import celery_app


@celery_app.task(name="app.workers.memory_consolidation.consolidate")
def consolidate(user_id: str = None) -> Dict[str, Any]:
    """
    Run the nightly memory consolidation cycle.
    """
    import asyncio
    return asyncio.run(_consolidate_async(user_id))


async def _consolidate_async(user_id: str = None) -> Dict[str, Any]:
    """Async implementation of memory consolidation."""
    
    results = {
        "consolidated_at": datetime.now().isoformat(),
        "profiles_updated": 0,
        "connections_strengthened": 0,
        "redundant_merged": 0,
        "review_queue_updated": 0
    }
    
    # 1. Update entity profiles
    results["profiles_updated"] = await update_entity_profiles()
    
    # 2. Strengthen frequently co-occurring connections
    results["connections_strengthened"] = await strengthen_connections()
    
    # 3. Merge redundant thoughts
    results["redundant_merged"] = await merge_redundant_thoughts()
    
    # 4. Update spaced repetition queue
    results["review_queue_updated"] = await update_review_queue()
    
    # 5. Log consolidation metadata
    await log_consolidation(results)
    
    return results


async def update_entity_profiles() -> int:
    """
    Update Person and Project profiles based on recent interactions.
    """
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    count = 0
    
    async with driver.session() as session:
        # Update interaction counts and last seen
        result = await session.run("""
            MATCH (e:Entity)<-[:MENTIONS]-(t:Thought)
            WHERE t.timestamp > datetime() - duration('P7D')
            WITH e, count(t) as recent_mentions, max(t.timestamp) as last_seen
            SET e.recent_activity = recent_mentions,
                e.last_seen = last_seen,
                e.updated = datetime()
            RETURN count(e) as updated
        """)
        
        record = await result.single()
        count = record["updated"] if record else 0
    
    return count


async def strengthen_connections() -> int:
    """
    Strengthen connections between entities that frequently appear together.
    """
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    count = 0
    
    async with driver.session() as session:
        # Find entities that co-occur in the same thoughts
        result = await session.run("""
            MATCH (e1:Entity)<-[:MENTIONS]-(t:Thought)-[:MENTIONS]->(e2:Entity)
            WHERE e1 <> e2 AND id(e1) < id(e2)
            WITH e1, e2, count(t) as co_occurrences
            WHERE co_occurrences >= 3
            MERGE (e1)-[r:RELATED_TO]-(e2)
            SET r.strength = co_occurrences,
                r.updated = datetime()
            RETURN count(r) as strengthened
        """)
        
        record = await result.single()
        count = record["strengthened"] if record else 0
    
    return count


async def merge_redundant_thoughts() -> int:
    """
    Identify and mark redundant thoughts for potential merge.
    Uses embedding similarity to find near-duplicates.
    """
    from app.dependencies import get_neo4j
    from app.services.vector_service import find_similar_pairs
    
    driver = await get_neo4j()
    
    # Find highly similar thought pairs (>0.95 similarity)
    similar_pairs = await find_similar_pairs(threshold=0.95)
    
    count = 0
    async with driver.session() as session:
        for pair in similar_pairs[:10]:  # Limit to 10 merges per run
            # Mark as redundant, don't delete automatically
            await session.run("""
                MATCH (t1:Thought {id: $id1}), (t2:Thought {id: $id2})
                WHERE t1.timestamp < t2.timestamp
                SET t2.redundant_of = t1.id,
                    t2.marked_redundant = datetime()
            """, id1=pair["id1"], id2=pair["id2"])
            count += 1
    
    return count


async def update_review_queue() -> int:
    """
    Update spaced repetition queue for thoughts due review.
    Uses SM-2 algorithm timing.
    """
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    count = 0
    
    async with driver.session() as session:
        # Find high-salience thoughts that are due for review
        result = await session.run("""
            MATCH (t:Thought)
            WHERE t.salience_score >= 0.7
              AND (t.next_review IS NULL OR t.next_review <= datetime())
            SET t.in_review_queue = true
            RETURN count(t) as queued
        """)
        
        record = await result.single()
        count = record["queued"] if record else 0
    
    return count


async def log_consolidation(results: Dict) -> None:
    """Log consolidation results to graph."""
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    
    async with driver.session() as session:
        await session.run("""
            CREATE (c:ConsolidationLog {
                timestamp: datetime(),
                profiles_updated: $profiles,
                connections_strengthened: $connections,
                redundant_merged: $merged,
                review_queue_updated: $reviewed
            })
        """, 
            profiles=results["profiles_updated"],
            connections=results["connections_strengthened"],
            merged=results["redundant_merged"],
            reviewed=results["review_queue_updated"]
        )
