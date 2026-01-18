"""
Cortex - Graph Schemas
Node and Edge type definitions for Neo4j.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# =============================================================================
# Enums
# =============================================================================

class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    PERSON = "Person"
    PROJECT = "Project"
    TOPIC = "Topic"
    TOOL = "Tool"
    LOCATION = "Location"
    EVENT = "Event"
    ORGANIZATION = "Organization"
    CONCEPT = "Concept"


class CategoryType(str, Enum):
    """PARA method categories."""
    PROJECT = "Project"
    AREA = "Area"
    RESOURCE = "Resource"
    ARCHIVE = "Archive"


class ActionUrgency(str, Enum):
    """Urgency levels for action items."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RelationshipType(str, Enum):
    """Types of relationships between nodes."""
    MENTIONS = "MENTIONS"
    BELONGS_TO = "BELONGS_TO"
    IMPLIES = "IMPLIES"
    CONNECTED_TO = "CONNECTED_TO"
    WORKS_ON = "WORKS_ON"
    REPORTS_TO = "REPORTS_TO"
    BLOCKS = "BLOCKS"
    SIMILAR_TO = "SIMILAR_TO"
    ATOMIZED_FROM = "ATOMIZED_FROM"
    HAS_SUBTASK = "HAS_SUBTASK"


# =============================================================================
# Node Schemas
# =============================================================================

class ThoughtNode(BaseModel):
    """Schema for Thought nodes."""
    id: str
    content: str
    summary: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None
    salience_score: float = 0.5
    
    # Spaced repetition fields
    review_count: int = 0
    ease_factor: float = 2.5
    interval_days: int = 1
    last_review: Optional[datetime] = None
    next_review: Optional[datetime] = None


class EntityNode(BaseModel):
    """Schema for Entity nodes."""
    name: str
    type: EntityType
    description: str = ""
    created: datetime = Field(default_factory=datetime.now)
    updated: Optional[datetime] = None
    
    # Profile fields (for Person/Project types)
    role: Optional[str] = None
    relationship: Optional[str] = None
    status: Optional[str] = None


class CategoryNode(BaseModel):
    """Schema for Category nodes."""
    name: str
    type: CategoryType = CategoryType.ARCHIVE
    description: str = ""


class ActionItemNode(BaseModel):
    """Schema for ActionItem nodes."""
    id: str
    task: str
    urgency: ActionUrgency = ActionUrgency.MEDIUM
    deadline: Optional[str] = None
    status: str = "pending"
    created: datetime = Field(default_factory=datetime.now)


class ReminderNode(BaseModel):
    """Schema for Reminder nodes."""
    id: str
    title: str
    datetime: Optional[str] = None
    priority: ActionUrgency = ActionUrgency.MEDIUM
    description: str = ""
    status: str = "pending"
    created: datetime = Field(default_factory=datetime.now)


# =============================================================================
# Edge Schemas
# =============================================================================

class EdgeBase(BaseModel):
    """Base schema for edges."""
    source: str
    target: str
    created: datetime = Field(default_factory=datetime.now)


class MentionsEdge(EdgeBase):
    """Thought -[:MENTIONS]-> Entity"""
    weight: float = 1.0


class BelongsToEdge(EdgeBase):
    """Thought -[:BELONGS_TO]-> Category"""
    confidence: float = 1.0


class ImpliesEdge(EdgeBase):
    """Thought -[:IMPLIES]-> ActionItem"""
    pass


class ConnectedToEdge(EdgeBase):
    """Entity -[:CONNECTED_TO]-> Entity"""
    reason: str = ""
    strength: float = 1.0


# =============================================================================
# Graph Schema Definition (for schema.cypher generation)
# =============================================================================

GRAPH_SCHEMA = """
// ============================================================================
// Cortex Knowledge Graph Schema
// ============================================================================

// --- Node Constraints ---
CREATE CONSTRAINT thought_id IF NOT EXISTS FOR (t:Thought) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE;
CREATE CONSTRAINT category_name IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT action_id IF NOT EXISTS FOR (a:ActionItem) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT reminder_id IF NOT EXISTS FOR (r:Reminder) REQUIRE r.id IS UNIQUE;

// --- Indexes ---
CREATE INDEX thought_timestamp IF NOT EXISTS FOR (t:Thought) ON (t.timestamp);
CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type);
CREATE INDEX action_status IF NOT EXISTS FOR (a:ActionItem) ON (a.status);
CREATE INDEX reminder_datetime IF NOT EXISTS FOR (r:Reminder) ON (r.datetime);

// --- Vector Index (Neo4j 5.11+) ---
CREATE VECTOR INDEX thought_embeddings IF NOT EXISTS
FOR (t:Thought)
ON (t.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 384,
        `vector.similarity_function`: 'cosine'
    }
};

// --- Relationship Schema (documented, not enforced) ---
// (:Thought)-[:MENTIONS]->(:Entity)
// (:Thought)-[:BELONGS_TO]->(:Category)
// (:Thought)-[:IMPLIES]->(:ActionItem)
// (:Thought)-[:ATOMIZED_FROM]->(:Thought)
// (:Entity)-[:CONNECTED_TO]->(:Entity)
// (:Entity)-[:WORKS_ON]->(:Entity {type: 'Project'})
// (:Task)-[:HAS_SUBTASK]->(:Task)
"""
