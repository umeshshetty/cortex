"""
Cortex - API Schemas
Pydantic models for API request/response validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Request Models
# =============================================================================

class ThoughtRequest(BaseModel):
    """Request model for processing a thought."""
    thought: str = Field(..., min_length=1, description="The thought/note to process")


class ReviewRequest(BaseModel):
    """Request for spaced repetition review."""
    thought_id: str
    quality: int = Field(..., ge=0, le=5, description="Recall quality (0-5)")


# =============================================================================
# Response Models
# =============================================================================

class EntityModel(BaseModel):
    """Entity extracted from a thought."""
    name: str
    type: str = "Unknown"
    description: str = ""


class CategoryModel(BaseModel):
    """Category classification."""
    name: str
    confidence: float = 1.0


class ThoughtResponse(BaseModel):
    """Response from thought processing."""
    thought_id: str
    response: str
    analysis: str = ""
    entities: List[EntityModel] = []
    categories: List[CategoryModel] = []
    summary: str = ""
    route: str = ""


class RouteClassification(BaseModel):
    """Intent classification result."""
    route: str
    input: str


# =============================================================================
# Graph Visualization
# =============================================================================

class GraphNode(BaseModel):
    """Node for graph visualization."""
    id: str
    type: str
    label: str
    data: dict = {}


class GraphEdge(BaseModel):
    """Edge for graph visualization."""
    source: str
    target: str
    type: str
    weight: float = 1.0


class GraphResponse(BaseModel):
    """Full graph data for visualization."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


# =============================================================================
# Brain Insights
# =============================================================================

class PersonProfile(BaseModel):
    """Synthesized person profile."""
    name: str
    role: str = ""
    relationship: str = ""
    topics: List[str] = []
    interaction_count: int = 0
    last_seen: Optional[str] = None


class ProjectProfile(BaseModel):
    """Synthesized project profile."""
    name: str
    status: str = "active"
    team: List[str] = []
    blockers: List[str] = []
    next_milestone: Optional[str] = None


class BrainStats(BaseModel):
    """Overall brain statistics."""
    thoughts: int = 0
    entities: int = 0
    categories: int = 0
    pending_actions: int = 0
    people: int = 0
    projects: int = 0


class SerendipityNudge(BaseModel):
    """A serendipity suggestion."""
    entity1: str
    entity2: str
    insight: str
    semantic_similarity: float = 0.0


# =============================================================================
# Health & Status
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    services: dict = {}


class ConsolidationResult(BaseModel):
    """Result from consolidation cycle."""
    merged_thoughts: int = 0
    updated_profiles: int = 0
    strengthened_connections: int = 0
    pruned_memories: int = 0
