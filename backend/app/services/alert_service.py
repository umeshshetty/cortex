"""
Cortex - Alert Service
Push notifications and alerts to users.
"""

from datetime import datetime
from typing import Dict, Any, Optional
import uuid


async def push_alert(
    user_id: Optional[str],
    alert_type: str,
    title: str,
    message: str,
    urgency: str = "medium",
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Push an alert to the user's notification queue.
    
    Args:
        user_id: Target user (None for global)
        alert_type: GHOST_DEPENDENCY | SCHEDULE_OPTIMIZATION | DEADLINE_RISK | etc.
        title: Alert headline
        message: Full alert message
        urgency: low | medium | high
        metadata: Additional data
    
    Returns:
        The created alert record
    """
    from app.dependencies import get_neo4j, get_redis
    
    alert_id = str(uuid.uuid4())
    
    alert = {
        "id": alert_id,
        "type": alert_type,
        "title": title,
        "message": message,
        "urgency": urgency,
        "metadata": metadata or {},
        "created_at": datetime.now().isoformat(),
        "read": False,
        "dismissed": False
    }
    
    # Store in Redis for fast access
    redis = await get_redis()
    queue_key = f"alerts:{user_id or 'global'}"
    
    await redis.lpush(queue_key, str(alert))
    await redis.ltrim(queue_key, 0, 99)  # Keep last 100 alerts
    
    # Also persist to graph for history
    driver = await get_neo4j()
    async with driver.session() as session:
        await session.run("""
            CREATE (a:Alert {
                id: $id,
                type: $type,
                title: $title,
                message: $message,
                urgency: $urgency,
                created_at: datetime($created_at),
                read: false,
                dismissed: false
            })
        """, 
            id=alert_id,
            type=alert_type,
            title=title,
            message=message,
            urgency=urgency,
            created_at=alert["created_at"]
        )
    
    return alert


async def get_pending_alerts(user_id: str, limit: int = 10) -> list:
    """Get unread alerts for a user."""
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    
    async with driver.session() as session:
        result = await session.run("""
            MATCH (a:Alert)
            WHERE a.dismissed = false
            RETURN a
            ORDER BY 
                CASE a.urgency WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
                a.created_at DESC
            LIMIT $limit
        """, limit=limit)
        
        return await result.data()


async def dismiss_alert(alert_id: str) -> bool:
    """Dismiss an alert."""
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    
    async with driver.session() as session:
        await session.run("""
            MATCH (a:Alert {id: $id})
            SET a.dismissed = true, a.dismissed_at = datetime()
        """, id=alert_id)
    
    return True
