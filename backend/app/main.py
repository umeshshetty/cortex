"""
Cortex - FastAPI Entry Point
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import List

from app.core.config import settings
from app.core.llm_tier import llm_client
from app.core.database import init_db
from app.services.graph_service import graph_service
from app.services.memory_service import memory_service
from app.services.vector_service import vector_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    print("🚀 Cortex starting up...")
    await init_db()  # Initialize TimeDB (Postgres Tables)
    await graph_service.connect() # Initialize GraphDB (Neo4j)
    await vector_service.create_vector_index() # Initialize Vector Index
    yield
    # Shutdown
    print("😴 Cortex shutting down...")
    await graph_service.close()

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

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}

class ChatRequest(BaseModel):
    message: str

class NoteRequest(BaseModel):
    content: str
    source: str = "user"

@app.post("/test/chat")
async def test_chat(request: ChatRequest):
    """Test LLM connection with Langfuse tracing."""
    response = await llm_client.chat(
        prompt=request.message,
        session_id="test-session-1"
    )
    return {"response": response}

# =============================================================================
# Memory Endpoints
# =============================================================================

@app.post("/api/memory/note")
async def add_note(request: NoteRequest):
    """Add a raw note to TimeDB."""
    return await memory_service.add_note(request.content, request.source)

@app.get("/api/memory/stream")
async def get_stream(limit: int = 10):
    """Get recent notes from TimeDB."""
    return await memory_service.get_recent_notes(limit)

@app.get("/api/memory/graph")
async def search_graph(query: str):
    """Search Knowledge Graph."""
    return await memory_service.search_graph(query)

# =============================================================================
# Profile Endpoints
# =============================================================================

from app.models.user import UserProfileCreate, UserProfileResponse
from app.services.profile_service import profile_service

@app.get("/api/profile", response_model=UserProfileResponse)
async def get_profile():
    """Get the current user profile."""
    profile = await profile_service.get_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@app.post("/api/profile", response_model=UserProfileResponse)
async def upsert_profile(profile: UserProfileCreate):
    """Create or update user profile."""
    result = await profile_service.upsert_profile(profile)
    return result

# =============================================================================
# LLM-Powered Profile Extraction
# =============================================================================

from app.services.profile_extractor import profile_extractor

class ExtractProfileRequest(BaseModel):
    description: str  # Natural language description of the user

@app.post("/api/profile/extract")
async def extract_profile(request: ExtractProfileRequest):
    """
    Extract profile from natural language using LLM.
    
    Example: "I'm Alex, a backend developer who loves Python and hiking"
    → Extracts: {name: "Alex", role: "Backend Developer", traits: ["Python", "hiking"]}
    → Saves to Neo4j
    """
    result = await profile_extractor.extract_and_save(request.description)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

