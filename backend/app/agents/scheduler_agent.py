"""
Cortex - Scheduler Agent (Advanced)
Calendar, reminders, and time-based task management.
ENFORCES CONTRAINTS via Anti-Goals.
"""

from datetime import datetime
from typing import Dict, Any, List
import json

from app.services.llm_service import get_llm
from app.services.graph_service import get_upcoming_events, create_reminder, get_neo4j

SCHEDULER_SYSTEM_PROMPT = """You are an Intelligent Scheduler.
Your goal is to parse user requests into structured scheduling actions using the current context.

Current Time: {current_time}

Constraints (Anti-Goals):
{constraints}

Rules:
1. If the request VIOLATES a constraint (e.g., meeting before 11am), your action must be "refuse".
2. If valid, extract the action and details.

Output JSON format:
{{
    "action": "create_event|create_reminder|check_calendar|reschedule|refuse",
    "title": "...",
    "datetime": "ISO format",
    "priority": "...",
    "refusal_reason": "Only if action is refuse"
}}
"""

async def get_user_constraints(user_id: str = "user_123") -> str:
    """Fetch active Anti-Goals from Neo4j."""
    driver = await get_neo4j()
    async with driver.session() as session:
        result = await session.run("""
            MATCH (u:UserProfile {user_id: $user_id})-[:HAS_ANTI_GOAL]->(ag:AntiGoal)
            RETURN ag.description as description
        """, user_id=user_id)
        
        constraints = [record["description"] for record in await result.data()]
        if not constraints:
            return "No specific time constraints."
        return "\n".join([f"- {c}" for c in constraints])


async def parse_schedule_request(user_input: str) -> Dict[str, Any]:
    """
    Parse a scheduling request using Claude for constraint checking.
    """
    # Use 'smart' tier (Claude) for reasoning about time/rules
    llm = get_llm(tier="smart", temperature=0)
    
    current_time = datetime.now().isoformat()
    constraints = await get_user_constraints()
    
    prompt = SCHEDULER_SYSTEM_PROMPT.format(
        current_time=current_time,
        constraints=constraints
    )
    
    try:
        response = await llm.ainvoke([
            ("system", prompt),
            ("human", user_input)
        ])
        
        content = response.content
        # Naive JSON extraction
        start = content.find('{')
        end = content.rfind('}') + 1
        return json.loads(content[start:end])
    except Exception as e:
        print(f"Scheduler Parse Error: {e}")
        return {"action": "check_calendar", "title": user_input}


async def handle_schedule_request(user_input: str) -> Dict[str, Any]:
    """
    Handle scheduling, reminder, and calendar requests.
    """
    # Step 1: Parse the request (Smart Parse)
    parsed = await parse_schedule_request(user_input)
    action = parsed.get("action", "check_calendar")
    
    upcoming = await get_upcoming_events(days=7)
    action_result = ""
    
    # Step 2: Handle Actions
    if action == "refuse":
        action_result = f"Request refused: {parsed.get('refusal_reason', 'Constraint violation')}."
    
    elif action == "create_reminder":
        await create_reminder(
            title=parsed.get("title", "Reminder"),
            datetime_str=parsed.get("datetime"),
            priority=parsed.get("priority", "medium"),
            description=parsed.get("description", "")
        )
        action_result = f"Created reminder: {parsed.get('title')}"
        
    elif action == "create_event":
        # Placeholder for real calendar
        action_result = f"Scheduled event: {parsed.get('title')} at {parsed.get('datetime')}"

    elif action == "check_calendar":
        if upcoming:
            action_result = "Upcoming:\n" + "\n".join([
                f"- {e['title']} at {e.get('datetime', 'TBD')}" for e in upcoming[:5]
            ])
        else:
            action_result = "No upcoming events."
    else:
        action_result = "Could not process scheduling request."

    # Step 3: Response Generation
    llm = get_llm(tier="smart", temperature=0.7)
    
    response = await llm.ainvoke([
        ("system", "You are a helpful assistant. Communicate the result of the scheduling action politely."),
        ("human", f"Action Result: {action_result}")
    ])
    
    return {
        "thought_id": "",
        "response": response.content,
        "analysis": action_result,
        "entities": [],
        "categories": ["Schedule"],
        "summary": parsed.get("title", "")
    }

