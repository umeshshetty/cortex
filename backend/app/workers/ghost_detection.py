"""
Cortex - Ghost Dependency Detection
Identifies tasks at risk because a key person is unresponsive.

Algorithm:
1. Fetch High Priority, Blocked Tasks
2. Check last interaction with the blocking person
3. If no contact in 3+ days -> GHOST DETECTED -> Alert User
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.workers.worker import celery_app
from app.services.graph_service import get_blocked_tasks, get_last_interaction
from app.services.alert_service import push_alert


@celery_app.task(name="app.workers.ghost_detection.detect_ghosts")
def detect_ghosts(user_id: str = None) -> Dict[str, Any]:
    """
    Run ghost dependency detection for all users (or specific user).
    
    Returns:
        Dict with ghost stats and alerts sent.
    """
    import asyncio
    return asyncio.run(_detect_ghosts_async(user_id))


async def _detect_ghosts_async(user_id: str = None) -> Dict[str, Any]:
    """Async implementation of ghost detection."""
    
    results = {
        "checked": 0,
        "ghosts_found": 0,
        "alerts_sent": []
    }
    
    # Fetch all blocked tasks
    blocked_tasks = await get_blocked_tasks(user_id)
    results["checked"] = len(blocked_tasks)
    
    # 3 days ago threshold
    ghost_threshold = datetime.now() - timedelta(days=3)
    
    for task in blocked_tasks:
        task_id = task.get("task_id")
        task_title = task.get("title", "Untitled")
        blocker_name = task.get("blocker_name")
        blocker_id = task.get("blocker_id")
        deadline = task.get("deadline")
        
        if not blocker_name:
            continue
        
        # Check last interaction with this person
        last_interaction = await get_last_interaction(blocker_id)
        
        # GHOST DETECTED
        if last_interaction is None or last_interaction < ghost_threshold:
            results["ghosts_found"] += 1
            
            days_silent = "never"
            if last_interaction:
                days_silent = f"{(datetime.now() - last_interaction).days} days"
            
            # Calculate urgency based on deadline proximity
            urgency = "medium"
            if deadline:
                deadline_dt = datetime.fromisoformat(deadline) if isinstance(deadline, str) else deadline
                if deadline_dt - datetime.now() < timedelta(hours=48):
                    urgency = "high"
            
            # Send alert
            alert = await push_alert(
                user_id=user_id,
                alert_type="GHOST_DEPENDENCY",
                title=f"⚠️ '{task_title}' blocked by {blocker_name}",
                message=f"No contact with {blocker_name} in {days_silent}. "
                        f"Consider following up to unblock this task.",
                urgency=urgency,
                metadata={
                    "task_id": task_id,
                    "blocker_id": blocker_id,
                    "blocker_name": blocker_name,
                    "days_silent": days_silent,
                    "deadline": deadline
                }
            )
            
            results["alerts_sent"].append(alert)
    
    return results


async def get_blocked_tasks(user_id: str = None) -> List[Dict]:
    """
    Fetch tasks that are blocked by people.
    
    MATCH (t:Task {status: 'BLOCKED'})<-[:BLOCKS]-(p:Person)
    RETURN t, p
    """
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    
    async with driver.session() as session:
        query = """
            MATCH (t:Task {status: 'BLOCKED'})<-[b:BLOCKS]-(p:Entity {type: 'Person'})
            WHERE t.priority >= 50 OR t.cognitive_demand = 'HIGH'
            RETURN t.id as task_id, t.title as title, t.deadline as deadline,
                   p.name as blocker_name, p.uid as blocker_id,
                   b.reason as block_reason
            ORDER BY t.deadline ASC
        """
        
        result = await session.run(query)
        return await result.data()


async def get_last_interaction(person_id: str) -> datetime | None:
    """
    Get the last interaction timestamp with a person.
    """
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    
    async with driver.session() as session:
        result = await session.run("""
            MATCH (t:Thought)-[:MENTIONS]->(p:Entity {uid: $person_id})
            RETURN max(t.timestamp) as last_seen
        """, person_id=person_id)
        
        record = await result.single()
        if record and record["last_seen"]:
            return datetime.fromisoformat(record["last_seen"])
        return None
