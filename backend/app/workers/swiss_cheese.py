"""
Cortex - Swiss Cheese Schedule Optimization
Defragments the calendar to create Focus Blocks.

Algorithm:
1. Get all events for the day
2. Identify "Dead Time" (15-45 min gaps between meetings)
3. Suggest consolidation to create Deep Work blocks
"""

from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional

from app.workers.worker import celery_app


@celery_app.task(name="app.workers.swiss_cheese.optimize_schedule")
def optimize_schedule(user_id: str = None, target_date: str = None) -> Dict[str, Any]:
    """
    Analyze schedule and suggest optimizations.
    
    Args:
        user_id: Optional user ID
        target_date: ISO date string (defaults to tomorrow)
    
    Returns:
        Optimization suggestions
    """
    import asyncio
    return asyncio.run(_optimize_schedule_async(user_id, target_date))


async def _optimize_schedule_async(user_id: str = None, target_date: str = None) -> Dict[str, Any]:
    """Async implementation of schedule optimization."""
    
    if target_date:
        date = datetime.fromisoformat(target_date).date()
    else:
        date = datetime.now().date() + timedelta(days=1)  # Tomorrow
    
    results = {
        "date": str(date),
        "events_analyzed": 0,
        "fragmented_time_minutes": 0,
        "suggestions": []
    }
    
    # Get events for the day
    events = await get_calendar_events(user_id, date)
    results["events_analyzed"] = len(events)
    
    if len(events) < 2:
        return results
    
    # Sort by start time
    events = sorted(events, key=lambda e: e["start"])
    
    # Find gaps and fragmented time
    gaps = []
    for i in range(len(events) - 1):
        current_end = parse_time(events[i]["end"])
        next_start = parse_time(events[i + 1]["start"])
        
        gap_minutes = (next_start - current_end).total_seconds() / 60
        
        # "Dead Time" = 15-45 minute gaps (too short for Deep Work)
        if 15 < gap_minutes < 45:
            gaps.append({
                "after_event": events[i]["title"],
                "before_event": events[i + 1]["title"],
                "gap_minutes": int(gap_minutes),
                "start_time": str(current_end.time()),
                "end_time": str(next_start.time())
            })
    
    # Calculate total fragmented time
    total_fragmented = sum(g["gap_minutes"] for g in gaps)
    results["fragmented_time_minutes"] = total_fragmented
    
    # If we have significant fragmented time, suggest consolidation
    if total_fragmented >= 60:
        # Find the most moveable event
        moveable_events = [e for e in events if e.get("moveable", True)]
        
        if moveable_events and len(gaps) >= 2:
            suggestion = {
                "type": "CONSOLIDATION",
                "message": f"You have {total_fragmented} mins of fragmented time. "
                          f"Consider moving '{moveable_events[0]['title']}' to create a 2-hour Deep Work block.",
                "gaps_count": len(gaps),
                "potential_focus_block_minutes": total_fragmented,
                "action": {
                    "event_id": moveable_events[0].get("id"),
                    "suggested_slot": find_adjacent_slot(events, moveable_events[0])
                }
            }
            results["suggestions"].append(suggestion)
    
    # Check for back-to-back meetings (no buffer)
    back_to_back_count = 0
    for i in range(len(events) - 1):
        current_end = parse_time(events[i]["end"])
        next_start = parse_time(events[i + 1]["start"])
        
        gap_minutes = (next_start - current_end).total_seconds() / 60
        
        if gap_minutes < 5:  # Less than 5 min buffer
            back_to_back_count += 1
    
    if back_to_back_count >= 3:
        results["suggestions"].append({
            "type": "BUFFER_WARNING",
            "message": f"⚠️ You have {back_to_back_count} back-to-back meetings. "
                      f"Consider adding 5-10 min buffers for mental recovery.",
            "count": back_to_back_count
        })
    
    # Send suggestions as alerts if significant
    if results["suggestions"]:
        from app.services.alert_service import push_alert
        
        for suggestion in results["suggestions"]:
            await push_alert(
                user_id=user_id,
                alert_type="SCHEDULE_OPTIMIZATION",
                title="📅 Calendar Optimization Available",
                message=suggestion["message"],
                urgency="low",
                metadata=suggestion
            )
    
    return results


def parse_time(time_str: str) -> datetime:
    """Parse time string to datetime."""
    if "T" in time_str:
        return datetime.fromisoformat(time_str)
    return datetime.strptime(time_str, "%H:%M")


def find_adjacent_slot(events: List[Dict], target_event: Dict) -> Optional[str]:
    """Find an adjacent slot to consolidate meetings."""
    # Simple heuristic: suggest moving to end of day
    if events:
        last_event = events[-1]
        end_time = parse_time(last_event["end"])
        suggested = end_time + timedelta(minutes=15)
        return suggested.strftime("%H:%M")
    return None


async def get_calendar_events(user_id: str, date) -> List[Dict]:
    """
    Get calendar events for a specific date.
    For now, fetch from graph. Later integrate with Google Calendar.
    """
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    
    date_str = str(date)
    
    async with driver.session() as session:
        result = await session.run("""
            MATCH (e:Event)
            WHERE date(e.start) = date($date)
            RETURN e.id as id, e.title as title, 
                   e.start as start, e.end as end,
                   e.moveable as moveable
            ORDER BY e.start
        """, date=date_str)
        
        return await result.data()
