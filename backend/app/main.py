"""
Cortex - FastAPI Entry Point
Personal Cognitive Assistant (PCA)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional, List

from app.dependencies import init_neo4j, init_redis, close_connections
from app.core.config import settings
from app.agents import router as agent_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    # Startup
    await init_neo4j()
    await init_redis()
    yield
    # Shutdown
    await close_connections()


app = FastAPI(
    title="Cortex API",
    description="Personal Cognitive Assistant - AI-powered second brain",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health & Status
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "services": {
            "neo4j": "connected",
            "redis": "connected"
        }
    }


# =============================================================================
# Morning Briefing
# =============================================================================

@app.get("/api/dashboard/briefing")
async def get_morning_briefing(user_id: Optional[str] = None):
    """
    Get the Morning Briefing - the active interface.
    Returns urgent risks, clarifications, and today's context.
    """
    from app.services.briefing import generate_morning_briefing
    return await generate_morning_briefing(user_id)


@app.get("/api/dashboard/command-center")
async def get_command_center_data(user_id: str = "user_123"):
    """
    Get aggregated data for the Command Center Dashboard.
    """
    from app.services.graph_service import (
        get_recent_thoughts, 
        get_active_projects,
        get_upcoming_events,
        get_all_people,
        get_brain_stats
    )
    
    # Run in parallel for performance
    import asyncio
    
    thoughts, projects, events, people, stats = await asyncio.gather(
        get_recent_thoughts(limit=10),
        get_active_projects(limit=5),
        get_upcoming_events(days=7),
        get_all_people(limit=5),
        get_brain_stats()
    )
    
    return {
        "user_id": user_id,
        "stats": stats,
        "recent_thoughts": thoughts,
        "active_projects": projects,
        "upcoming_events": events,
        "recent_people": people
    }


# =============================================================================
# Clarification Queue
# =============================================================================

class ClarificationResponse(BaseModel):
    clarification_id: str
    response: str


@app.post("/api/clarifications/resolve")
async def resolve_clarification(data: ClarificationResponse):
    """Resolve a pending clarification with user's choice."""
    from app.services.briefing import resolve_clarification
    success = await resolve_clarification(data.clarification_id, data.response)
    return {"success": success}


# =============================================================================
# Onboarding
# =============================================================================

class OnboardingStart(BaseModel):
    user_id: str


class OnboardingResponse(BaseModel):
    user_id: str
    question_id: str
    response: str


@app.post("/api/onboarding/start")
async def start_onboarding(data: OnboardingStart):
    """
    Start the Day 0 onboarding protocol.
    Returns the first interview question.
    """
    from app.agents.onboarding import onboarding_agent
    return await onboarding_agent.start_onboarding(data.user_id)


@app.post("/api/onboarding/respond")
async def respond_onboarding(data: OnboardingResponse):
    """
    Process a response during onboarding.
    Returns the next question or completion status.
    """
    from app.agents.onboarding import onboarding_agent
    return await onboarding_agent.process_response(
        data.user_id, 
        data.question_id, 
        data.response
    )


# =============================================================================
# User Profile
# =============================================================================

@app.get("/api/profile/{user_id}")
async def get_user_profile(user_id: str):
    """Get user's profile (the 4-level knowledge model)."""
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    async with driver.session() as session:
        result = await session.run("""
            MATCH (u:UserProfile {user_id: $user_id})
            OPTIONAL MATCH (u)-[:HAS_GOAL]->(g:Goal)
            RETURN u, collect(g) as goals
        """, user_id=user_id)
        
        record = await result.single()
        if not record:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile = dict(record["u"])
        profile["goals"] = [dict(g) for g in record["goals"]]
        return profile


# =============================================================================
# Alerts
# =============================================================================

@app.get("/api/alerts")
async def get_alerts(user_id: Optional[str] = None, limit: int = 10):
    """Get pending alerts."""
    from app.services.alert_service import get_pending_alerts
    return await get_pending_alerts(user_id, limit)


@app.post("/api/alerts/{alert_id}/dismiss")
async def dismiss_alert(alert_id: str):
    """Dismiss an alert."""
    from app.services.alert_service import dismiss_alert
    success = await dismiss_alert(alert_id)
    return {"success": success}


# Mount agent router
app.include_router(agent_router.router, prefix="/api", tags=["agents"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

