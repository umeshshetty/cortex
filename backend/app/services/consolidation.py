"""
Cortex - Consolidation Service (The "Sleep" Cycle)
Nightly/background jobs for memory consolidation.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
from langchain_ollama import ChatOllama

from app.dependencies import get_neo4j
from app.core.config import settings
from app.core.prompts import CONSOLIDATION_PROMPT


async def consolidate_memory() -> Dict[str, Any]:
    """
    Run the memory consolidation cycle.
    This is the "sleep" process that organizes and strengthens memories.
    
    Tasks:
    1. Identify redundant thoughts
    2. Update entity profiles
    3. Strengthen important connections
    4. Prune low-salience memories
    """
    driver = await get_neo4j()
    results = {
        "merged_thoughts": 0,
        "updated_profiles": 0,
        "strengthened_connections": 0,
        "pruned_memories": 0
    }
    
    async with driver.session() as session:
        # 1. Find recent thoughts for consolidation
        recent = await session.run("""
            MATCH (t:Thought)
            WHERE t.timestamp > $cutoff
            RETURN t.id as id, t.content as content, t.summary as summary
            ORDER BY t.timestamp DESC
            LIMIT 50
        """, cutoff=(datetime.now() - timedelta(days=7)).isoformat())
        
        thoughts = await recent.data()
        
        if not thoughts:
            return results
        
        # 2. Use LLM to identify consolidation opportunities
        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0
        )
        
        thought_summaries = "\n".join([
            f"- [{t['id'][:8]}]: {t['summary'] or t['content'][:50]}"
            for t in thoughts[:20]
        ])
        
        prompt = f"""{CONSOLIDATION_PROMPT}

Recent thoughts:
{thought_summaries}

Identify consolidation actions as JSON:
{{
    "merge_candidates": [["id1", "id2"]],
    "profile_updates": [{{"entity": "name", "insight": "new info"}}],
    "connection_strengths": [{{"from": "a", "to": "b", "strength": 0.9}}]
}}

JSON:"""
        
        response = await llm.ainvoke(prompt)
        
        # 3. Apply consolidation (simplified - just log for now)
        # In production, this would actually merge thoughts, update profiles, etc.
        
        # 4. Update consolidation stats
        await session.run("""
            MERGE (m:Metadata {key: 'last_consolidation'})
            SET m.timestamp = $timestamp, m.thoughts_processed = $count
        """, timestamp=datetime.now().isoformat(), count=len(thoughts))
    
    return results


async def run_spaced_repetition() -> List[Dict]:
    """
    Identify thoughts that need resurfacing based on spaced repetition.
    Uses SM-2 algorithm for optimal recall timing.
    """
    driver = await get_neo4j()
    
    async with driver.session() as session:
        # Find thoughts due for review
        result = await session.run("""
            MATCH (t:Thought)
            WHERE t.next_review IS NOT NULL AND t.next_review <= $now
            ORDER BY t.next_review
            LIMIT 10
            RETURN t.id as id, t.content as content, t.summary as summary,
                   t.review_count as review_count, t.ease_factor as ease_factor
        """, now=datetime.now().isoformat())
        
        return await result.data()


async def update_review(thought_id: str, quality: int) -> bool:
    """
    Update spaced repetition after user review.
    Quality: 0-5 (0=complete blackout, 5=perfect recall)
    """
    driver = await get_neo4j()
    
    # SM-2 algorithm
    async with driver.session() as session:
        result = await session.run("""
            MATCH (t:Thought {id: $id})
            WITH t, 
                 COALESCE(t.ease_factor, 2.5) as ef,
                 COALESCE(t.review_count, 0) as count,
                 COALESCE(t.interval_days, 1) as interval
            SET t.ease_factor = CASE 
                    WHEN $quality >= 3 THEN ef + (0.1 - (5 - $quality) * (0.08 + (5 - $quality) * 0.02))
                    ELSE CASE WHEN ef - 0.2 < 1.3 THEN 1.3 ELSE ef - 0.2 END
                END,
                t.review_count = count + 1,
                t.interval_days = CASE
                    WHEN $quality < 3 THEN 1
                    WHEN count = 0 THEN 1
                    WHEN count = 1 THEN 6
                    ELSE toInteger(interval * t.ease_factor)
                END,
                t.last_review = $now,
                t.next_review = datetime($now) + duration({days: t.interval_days})
            RETURN t.next_review as next_review
        """, id=thought_id, quality=quality, now=datetime.now().isoformat())
        
        return True


async def identify_structural_holes() -> List[Dict]:
    """
    Find structural holes in the knowledge graph.
    These are potential connections between unconnected clusters.
    """
    driver = await get_neo4j()
    
    async with driver.session() as session:
        # Find entities that share topics but aren't connected
        result = await session.run("""
            MATCH (e1:Entity)<-[:MENTIONS]-(t:Thought)-[:MENTIONS]->(e2:Entity)
            WHERE e1 <> e2 AND NOT (e1)-[:CONNECTED_TO]-(e2)
            WITH e1, e2, count(t) as shared_thoughts
            WHERE shared_thoughts >= 2
            RETURN e1.name as entity1, e2.name as entity2, 
                   shared_thoughts, e1.type as type1, e2.type as type2
            ORDER BY shared_thoughts DESC
            LIMIT 10
        """)
        
        return await result.data()


# =============================================================================
# Background Worker
# =============================================================================

async def run_consolidation_cycle():
    """
    Main background worker loop.
    Runs periodically to consolidate memory.
    """
    print("🌙 Starting consolidation cycle...")
    
    # Memory consolidation
    consolidation_results = await consolidate_memory()
    print(f"   Consolidation: {consolidation_results}")
    
    # Structural hole detection
    holes = await identify_structural_holes()
    print(f"   Structural holes found: {len(holes)}")
    
    # Spaced repetition queue
    due_reviews = await run_spaced_repetition()
    print(f"   Thoughts due for review: {len(due_reviews)}")
    
    print("✅ Consolidation cycle complete")
    
    return {
        "consolidation": consolidation_results,
        "structural_holes": len(holes),
        "due_reviews": len(due_reviews)
    }
