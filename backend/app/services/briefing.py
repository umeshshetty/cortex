"""
Cortex - Morning Briefing Service
Generates the daily briefing dashboard with risks, clarifications, and context.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.services.alert_service import get_pending_alerts
from app.services.graph_service import get_brain_stats


async def generate_morning_briefing(user_id: str = None) -> Dict[str, Any]:
    """
    Generate the Morning Briefing for a user.
    
    Returns:
        Dict containing:
        - urgent_risks: High-priority alerts
        - clarification_queue: Pending decisions
        - todays_context: Meeting/task context
        - stats: Brain statistics
    """
    briefing = {
        "generated_at": datetime.now().isoformat(),
        "user_id": user_id,
        "urgent_risks": [],
        "clarification_queue": [],
        "todays_context": [],
        "todays_meetings": [],
        "action_items_due": [],
        "stats": {}
    }
    
    # 1. Get urgent risks (high priority alerts)
    alerts = await get_pending_alerts(user_id, limit=10)
    briefing["urgent_risks"] = [
        {
            "id": a.get("a", {}).get("id"),
            "type": a.get("a", {}).get("type"),
            "title": a.get("a", {}).get("title"),
            "message": a.get("a", {}).get("message"),
            "urgency": a.get("a", {}).get("urgency")
        }
        for a in alerts
        if a.get("a", {}).get("urgency") == "high"
    ]
    
    # 2. Get clarification queue (conflicts, ambiguities)
    briefing["clarification_queue"] = await get_pending_clarifications(user_id)
    
    # 3. Get today's context (meetings with relevant info)
    briefing["todays_meetings"] = await get_todays_meetings(user_id)
    briefing["todays_context"] = await enrich_meeting_context(
        briefing["todays_meetings"],
        user_id
    )
    
    # 4. Get action items due today/tomorrow
    briefing["action_items_due"] = await get_due_action_items(user_id)
    
    # 5. Get brain stats
    briefing["stats"] = await get_brain_stats()
    
    return briefing


async def get_pending_clarifications(user_id: str = None) -> List[Dict]:
    """
    Get pending clarification requests.
    These are ambiguities that need user input.
    """
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    
    async with driver.session() as session:
        result = await session.run("""
            MATCH (c:Clarification)
            WHERE c.resolved = false
            RETURN c.id as id, c.type as type, c.description as description,
                   c.options as options, c.context as context, c.created_at as created_at
            ORDER BY c.created_at DESC
            LIMIT 10
        """)
        
        data = await result.data()
        
        return [
            {
                "id": d["id"],
                "type": d["type"],  # CONFLICT, AMBIGUITY, MISSING_INFO
                "description": d["description"],
                "options": d.get("options", []),
                "context": d.get("context", "")
            }
            for d in data
        ]


async def get_todays_meetings(user_id: str = None) -> List[Dict]:
    """Get meetings scheduled for today."""
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    today = datetime.now().date().isoformat()
    
    async with driver.session() as session:
        result = await session.run("""
            MATCH (e:Event)
            WHERE date(e.start) = date($today)
            OPTIONAL MATCH (e)-[:WITH]->(p:Entity {type: 'Person'})
            RETURN e.id as id, e.title as title, e.start as start, e.end as end,
                   e.location as location, collect(p.name) as attendees
            ORDER BY e.start
        """, today=today)
        
        return await result.data()


async def enrich_meeting_context(meetings: List[Dict], user_id: str = None) -> List[Dict]:
    """
    Enrich meetings with relevant context about attendees.
    "You're meeting Mike today. Remember: He's a key stakeholder for your promotion."
    """
    from app.dependencies import get_neo4j
    
    if not meetings:
        return []
    
    driver = await get_neo4j()
    enriched = []
    
    for meeting in meetings:
        attendees = meeting.get("attendees", [])
        context_items = []
        
        for attendee in attendees:
            if not attendee:
                continue
                
            async with driver.session() as session:
                # Get person context
                result = await session.run("""
                    MATCH (p:Entity {name: $name, type: 'Person'})
                    OPTIONAL MATCH (p)-[:LINKED_TO]->(g:Goal)
                    OPTIONAL MATCH (t:Thought)-[:MENTIONS]->(p)
                    WITH p, collect(DISTINCT g.title) as goals, 
                         count(t) as interaction_count,
                         max(t.timestamp) as last_interaction
                    RETURN p.name as name, p.role as role,
                           p.relationship as relationship,
                           goals, interaction_count, last_interaction
                """, name=attendee)
                
                person_data = await result.single()
                
                if person_data:
                    context = {
                        "person": attendee,
                        "role": person_data.get("role", ""),
                        "relationship": person_data.get("relationship", ""),
                        "linked_goals": person_data.get("goals", []),
                        "interactions": person_data.get("interaction_count", 0)
                    }
                    
                    # Generate context message
                    if context["linked_goals"]:
                        context["message"] = f"{attendee} is connected to your goal: {context['linked_goals'][0]}"
                    elif context["role"]:
                        context["message"] = f"{attendee} is your {context['role']}"
                    
                    context_items.append(context)
        
        if context_items:
            enriched.append({
                "meeting": meeting["title"],
                "time": meeting.get("start"),
                "context": context_items
            })
    
    return enriched


async def get_due_action_items(user_id: str = None) -> List[Dict]:
    """Get action items due today or tomorrow."""
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    tomorrow = (datetime.now() + timedelta(days=1)).isoformat()
    
    async with driver.session() as session:
        result = await session.run("""
            MATCH (a:ActionItem {status: 'pending'})
            WHERE a.deadline <= $tomorrow
            RETURN a.id as id, a.task as task, a.urgency as urgency,
                   a.deadline as deadline
            ORDER BY a.deadline
            LIMIT 10
        """, tomorrow=tomorrow)
        
        return await result.data()


async def create_clarification(
    clarification_type: str,
    description: str,
    options: List[str] = None,
    context: str = ""
) -> str:
    """Create a new clarification request for user input."""
    from app.dependencies import get_neo4j
    import uuid
    
    driver = await get_neo4j()
    clarification_id = str(uuid.uuid4())
    
    async with driver.session() as session:
        await session.run("""
            CREATE (c:Clarification {
                id: $id,
                type: $type,
                description: $description,
                options: $options,
                context: $context,
                resolved: false,
                created_at: datetime()
            })
        """, 
            id=clarification_id,
            type=clarification_type,
            description=description,
            options=options or [],
            context=context
        )
    
    return clarification_id


async def resolve_clarification(clarification_id: str, response: str) -> bool:
    """Resolve a clarification with user's choice."""
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    
    async with driver.session() as session:
        await session.run("""
            MATCH (c:Clarification {id: $id})
            SET c.resolved = true,
                c.response = $response,
                c.resolved_at = datetime()
        """, id=clarification_id, response=response)
    
    return True
