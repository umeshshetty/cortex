"""
Cortex - Graph Service
Neo4j Cypher helpers - all database interactions go through this layer.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.dependencies import get_neo4j


# =============================================================================
# Thought Operations
# =============================================================================

async def get_recent_thoughts(limit: int = 5) -> List[Dict]:
    """Get the most recent thoughts/logs."""
    driver = await get_neo4j()
    
    async with driver.session() as session:
        result = await session.run("""
            MATCH (t:Thought)
            OPTIONAL MATCH (t)-[:BELONGS_TO]->(c:Category)
            RETURN t, collect(c.name) as categories
            ORDER BY t.timestamp DESC
            LIMIT $limit
        """, limit=limit)
        
        thoughts = []
        records = await result.data()
        for r in records:
            t = dict(r['t'])
            t['categories'] = r['categories']
            thoughts.append(t)
        
        return serialize_neo4j_values(thoughts)


async def save_thought(
    content: str,
    summary: str,
    entities: List[Dict],
    categories: List[str],
    action_items: List[Dict]
) -> str:
    """
    Save a thought to Neo4j with its extracted knowledge.
    Returns the thought_id.
    """
    driver = await get_neo4j()
    thought_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    async with driver.session() as session:
        # Create the Thought node
        await session.run("""
            CREATE (t:Thought {
                id: $id,
                content: $content,
                summary: $summary,
                timestamp: $timestamp
            })
        """, id=thought_id, content=content, summary=summary, timestamp=timestamp)
        
        # Link to categories
        for category in categories:
            await session.run("""
                MERGE (c:Category {name: $name})
                WITH c
                MATCH (t:Thought {id: $thought_id})
                MERGE (t)-[:BELONGS_TO]->(c)
            """, name=category, thought_id=thought_id)
        
        # Create and link entities
        for entity in entities:
            await session.run("""
                MERGE (e:Entity {name: $name})
                ON CREATE SET e.type = $type, e.description = $desc
                ON MATCH SET e.description = COALESCE(e.description, '') + ' | ' + $desc
                WITH e
                MATCH (t:Thought {id: $thought_id})
                MERGE (t)-[:MENTIONS]->(e)
            """, name=entity.get("name"), type=entity.get("type", "Unknown"),
                desc=entity.get("description", ""), thought_id=thought_id)
        
        # Create action items
        for action in action_items:
            action_id = str(uuid.uuid4())
            await session.run("""
                CREATE (a:ActionItem {
                    id: $id,
                    task: $task,
                    urgency: $urgency,
                    deadline: $deadline,
                    status: 'pending',
                    created: $created
                })
                WITH a
                MATCH (t:Thought {id: $thought_id})
                MERGE (t)-[:IMPLIES]->(a)
            """, id=action_id, task=action.get("task"), urgency=action.get("urgency", "medium"),
                deadline=action.get("deadline", ""), created=timestamp, thought_id=thought_id)
    
    return thought_id


async def get_related_context(search_term: str, limit: int = 5) -> str:
    """
    Get context from graph by traversing entity relationships.
    """
    driver = await get_neo4j()
    
    async with driver.session() as session:
        # Simple keyword-based graph search (vector search would be via vector_service)
        result = await session.run("""
            MATCH (t:Thought)-[:MENTIONS]->(e:Entity)
            WHERE toLower(t.content) CONTAINS toLower($search_term)
               OR toLower(e.name) CONTAINS toLower($search_term)
            WITH t, collect(e.name) as entities
            ORDER BY t.timestamp DESC
            LIMIT $limit
            RETURN t.content as content, t.summary as summary, entities
        """, search_term=search_term, limit=limit)
        
        records = await result.data()
        
        if not records:
            return ""
        
        context_parts = []
        for r in records:
            context_parts.append(f"- {r['summary'] or r['content'][:100]} (entities: {', '.join(r['entities'])})")
        
        return "\n".join(context_parts)


async def get_thought_by_id(thought_id: str) -> Optional[Dict]:
    """Get a single thought by ID."""
    driver = await get_neo4j()
    
    async with driver.session() as session:
        result = await session.run("""
            MATCH (t:Thought {id: $id})
            OPTIONAL MATCH (t)-[:MENTIONS]->(e:Entity)
            OPTIONAL MATCH (t)-[:BELONGS_TO]->(c:Category)
            RETURN t, collect(DISTINCT e) as entities, collect(DISTINCT c.name) as categories
        """, id=thought_id)
        
        record = await result.single()
        if record:
            thought = dict(record["t"])
            thought["entities"] = [dict(e) for e in record["entities"] if e]
            thought["categories"] = record["categories"]
            return thought
        return None


# =============================================================================
# People Operations
# =============================================================================

async def get_all_people(limit: int = 50) -> List[Dict]:
    """Get all person profiles."""
    driver = await get_neo4j()
    
    async with driver.session() as session:
        result = await session.run("""
            MATCH (e:Entity {type: 'Person'})
            OPTIONAL MATCH (e)<-[:MENTIONS]-(t:Thought)
            WITH e, count(t) as mentions, max(t.timestamp) as last_seen
            ORDER BY mentions DESC
            LIMIT $limit
            RETURN e.name as name, e.description as description,
                   mentions, last_seen
        """, limit=limit)
        
        return await result.data()


async def get_person_profile(name: str) -> Optional[Dict]:
    """Get detailed profile for a person."""
    driver = await get_neo4j()
    
    async with driver.session() as session:
        result = await session.run("""
            MATCH (e:Entity {name: $name, type: 'Person'})
            OPTIONAL MATCH (e)<-[:MENTIONS]-(t:Thought)
            WITH e, collect(t) as thoughts
            OPTIONAL MATCH (e)-[:CONNECTED_TO]-(other:Entity)
            RETURN e.name as name, e.description as description,
                   size(thoughts) as interaction_count,
                   collect(DISTINCT other.name) as connections
        """, name=name)
        
        record = await result.single()
        return dict(record) if record else None


async def update_person_profile(name: str, updates: Dict) -> bool:
    """Update a person's profile."""
    driver = await get_neo4j()
    
    async with driver.session() as session:
        context = updates.get("context", "")
        await session.run("""
            MATCH (e:Entity {name: $name, type: 'Person'})
            SET e.description = COALESCE(e.description, '') + ' | ' + $context,
                e.updated = $timestamp
        """, name=name, context=context, timestamp=datetime.now().isoformat())
        
        return True


async def create_connection(from_entity: str, to_entity: str, relationship_type: str, reason: str = "") -> bool:
    """Create a connection between two entities."""
    driver = await get_neo4j()
    
    async with driver.session() as session:
        await session.run("""
            MATCH (a:Entity {name: $from})
            MATCH (b:Entity {name: $to})
            MERGE (a)-[r:CONNECTED_TO]->(b)
            SET r.reason = $reason, r.created = $timestamp
        """, **{"from": from_entity}, to=to_entity, reason=reason, 
            timestamp=datetime.now().isoformat())
        
        return True


# =============================================================================
# Project Operations
# =============================================================================

async def get_active_projects(limit: int = 5) -> List[Dict]:
    """Get active projects and their status."""
    driver = await get_neo4j()
    
    async with driver.session() as session:
        result = await session.run("""
            MATCH (p:Entity {type: 'Project'})
            OPTIONAL MATCH (p)<-[:MENTIONS]-(t:Thought)
            WITH p, count(t) as updates, max(t.timestamp) as last_update
            // WHERE p.status = 'active' OR p.status IS NULL
            RETURN p.name as name, p.description as description, 
                   p.status as status, updates, last_update
            ORDER BY last_update DESC
            LIMIT $limit
        """, limit=limit)
        
        return await result.data()


# =============================================================================
# Schedule Operations
# =============================================================================

async def get_upcoming_events(days: int = 7) -> List[Dict]:
    """Get upcoming events/reminders."""
    driver = await get_neo4j()
    cutoff = (datetime.now() + timedelta(days=days)).isoformat()
    
    async with driver.session() as session:
        result = await session.run("""
            MATCH (r:Reminder)
            WHERE r.datetime <= $cutoff AND r.status = 'pending'
            RETURN r.id as id, r.title as title, r.datetime as datetime,
                   r.priority as priority
            ORDER BY r.datetime
            LIMIT 10
        """, cutoff=cutoff)
        
        return await result.data()


async def create_reminder(
    title: str,
    datetime_str: Optional[str],
    priority: str = "medium",
    description: str = ""
) -> str:
    """Create a new reminder."""
    driver = await get_neo4j()
    reminder_id = str(uuid.uuid4())
    
    async with driver.session() as session:
        await session.run("""
            CREATE (r:Reminder {
                id: $id,
                title: $title,
                datetime: $datetime,
                priority: $priority,
                description: $description,
                status: 'pending',
                created: $created
            })
        """, id=reminder_id, title=title, datetime=datetime_str or "",
            priority=priority, description=description,
            created=datetime.now().isoformat())
    
    return reminder_id


# =============================================================================
# Statistics
# =============================================================================

async def get_brain_stats() -> Dict[str, Any]:
    """Get overall brain statistics."""
    driver = await get_neo4j()
    
    async with driver.session() as session:
        result = await session.run("""
            MATCH (t:Thought) WITH count(t) as thoughts
            MATCH (e:Entity) WITH thoughts, count(e) as entities
            MATCH (c:Category) WITH thoughts, entities, count(c) as categories
            MATCH (a:ActionItem {status: 'pending'}) 
            RETURN thoughts, entities, categories, count(a) as pending_actions
        """)
        
        record = await result.single()
        return dict(record) if record else {
            "thoughts": 0, "entities": 0, "categories": 0, "pending_actions": 0
        }


async def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get the active user profile."""
    driver = await get_neo4j()
    
    async with driver.session() as session:
        result = await session.run("""
            MATCH (u:UserProfile {user_id: $user_id})
            OPTIONAL MATCH (u)-[:HAS_GOAL]->(g:Goal)
            OPTIONAL MATCH (u)-[:HAS_ANTI_GOAL]->(a:AntiGoal)
            RETURN u, collect(DISTINCT g) as goals, collect(DISTINCT a) as anti_goals
        """, user_id=user_id)
        
        record = await result.single()
        if not record:
            return None
            
        profile = dict(record["u"])
        
        # Deserialize JSON fields if needed, or just return as dict
        # In Neo4j arrays are stored natively, but check format
        
        # Add goals and anti-goals
        profile["goals"] = [dict(g) for g in record["goals"]]
        
        # Reconstruct strategic profile structure roughly for the dict
        if "strategic" not in profile:
            profile["strategic"] = {}
            
        # We need to structure this so the Pydantic model can load it, 
        # OR just ensure the Dict has the fields the prompt needs.
        # The prompt accesses profile.get('strategic', {}).get('anti_goals', [])
        
        profile_anti_goals = [dict(a) for a in record["anti_goals"]]
        
        # If strategic is flattened in 'u', we might need to be careful. 
        # But here we just want to ensure the specific path used in cognitive_graph works.
        # cognitive_graph accesses: profile.get('strategic', {}).get('anti_goals', [])
        
        # Let's ensure 'strategic' dictionary exists and has 'anti_goals'
        # 'u' (UserProfile) properties like 'value_hierarchy' might be there.
        # We should create a clean 'strategic' dict if we want to be safe, creating a composite.
        
        strategic = {
            "north_star_goals": profile["goals"],
            "anti_goals": profile_anti_goals,
            "value_hierarchy": profile.get("value_hierarchy", [])
            # Add other strategic fields if needed
        }
        profile["strategic"] = strategic
        
        return serialize_neo4j_values(profile)


def serialize_neo4j_values(data: Any) -> Any:
    """Recursively convert Neo4j types to JSON-serializable formats."""
    from neo4j.time import DateTime, Date, Time
    
    if isinstance(data, dict):
        return {k: serialize_neo4j_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_neo4j_values(item) for item in data]
    elif isinstance(data, (DateTime, Date, Time, datetime)):
        return data.isoformat()
    return data
