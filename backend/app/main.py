"""
Cortex - FastAPI Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.config import settings
from app.core.llm_tier import llm_client

app = FastAPI(
    title="Cortex API",
    description="Personal Cognitive Assistant - AI-powered second brain",
    version="2.0.0"
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

@app.post("/test/chat")
async def test_chat(request: ChatRequest):
    """Test LLM connection with Langfuse tracing."""
    response = await llm_client.chat(
        prompt=request.message,
        session_id="test-session-1"
    )
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

