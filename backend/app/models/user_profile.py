"""
Cortex - User Profile Schema
4-Level User Knowledge Model based on Master System Specification v5.6

Levels:
1. Biological & Logistical (The Hardware)
2. Strategic (The Software)
3. Social Dynamics (The Network)
4. Psychological Profile (The User Manual)
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import time, datetime
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class Chronotype(str, Enum):
    """User's natural energy rhythm."""
    LARK = "LARK"       # Morning person (peak 6AM-12PM)
    OWL = "OWL"         # Night person (peak 6PM-12AM)
    THIRD_BIRD = "THIRD_BIRD"  # Somewhere in between


class RelationshipTier(str, Enum):
    """Person importance tiers."""
    VIP = "VIP"             # Can bypass Do Not Disturb
    INNER_CIRCLE = "INNER_CIRCLE"  # Weekly review inclusion
    CORE = "CORE"           # Regular contacts
    PERIPHERAL = "PERIPHERAL"  # Logged but passive


class PoliticalArchetype(str, Enum):
    """Political role in user's network."""
    SPONSOR = "SPONSOR"     # High influence, positive sentiment
    BLOCKER = "BLOCKER"     # Historically delays/adds friction
    CONNECTOR = "CONNECTOR" # Bridges different social graphs
    UNKNOWN = "UNKNOWN"


class CognitiveDemand(str, Enum):
    """Task cognitive load."""
    HIGH = "HIGH"           # Deep work, creative thinking
    MEDIUM = "MEDIUM"       # Strategic meetings, planning
    LOW = "LOW"             # Admin, emails, routine


class CommunicationStyle(str, Enum):
    """User's preferred communication style."""
    DIRECT = "DIRECT"       # Bulleted, to the point
    CONVERSATIONAL = "CONVERSATIONAL"  # Soft, context-rich
    STRUCTURED = "STRUCTURED"  # Headings, formal


# =============================================================================
# Level 1: Biological & Logistical (The Hardware)
# =============================================================================

class TimeRange(BaseModel):
    """A time range within a day."""
    start: str = Field(..., description="Start time (HH:MM)")
    end: str = Field(..., description="End time (HH:MM)")
    

class EnergyZones(BaseModel):
    """User's energy zones throughout the day."""
    peak_zone: TimeRange = Field(
        default=TimeRange(start="08:00", end="11:00"),
        description="Reserved for HIGH cognitive load tasks"
    )
    trough_zone: TimeRange = Field(
        default=TimeRange(start="14:00", end="15:30"),
        description="Meetings, emails, low-energy tasks"
    )
    recovery_zone: TimeRange = Field(
        default=TimeRange(start="20:00", end="23:59"),
        description="No work notifications"
    )


class PhysicalContext(BaseModel):
    """Physical location contexts."""
    home_address: Optional[str] = None
    office_address: Optional[str] = None
    gym_location: Optional[str] = None
    third_place: Optional[str] = None  # Cafe, library, etc.


class BiologicalProfile(BaseModel):
    """Level 1: Biological & Logistical constraints."""
    chronotype: Chronotype = Chronotype.THIRD_BIRD
    energy_zones: EnergyZones = Field(default_factory=EnergyZones)
    physical_contexts: PhysicalContext = Field(default_factory=PhysicalContext)
    timezone: str = "UTC"
    work_start: str = "09:00"
    work_end: str = "18:00"
    preferred_meeting_duration: int = 30  # minutes


# =============================================================================
# Level 2: Strategic (The Software)
# =============================================================================

class NorthStarGoal(BaseModel):
    """A key objective for the quarter/year."""
    id: str
    title: str
    description: str = ""
    deadline: Optional[str] = None
    progress: float = 0.0  # 0-100
    active: bool = True


class AntiGoal(BaseModel):
    """Explicit constraint on what user refuses to do."""
    id: str
    description: str
    severity: str = "hard"  # hard = never, soft = avoid


class StrategicProfile(BaseModel):
    """Level 2: Strategic goals and constraints."""
    north_star_goals: List[NorthStarGoal] = Field(
        default_factory=list,
        description="1-3 non-negotiable objectives"
    )
    anti_goals: List[AntiGoal] = Field(
        default_factory=list,
        description="What the user refuses to do"
    )
    value_hierarchy: List[str] = Field(
        default=["Health", "Family", "Career", "Wealth"],
        description="Ordered list for conflict resolution"
    )
    focus_areas: List[str] = Field(
        default_factory=list,
        description="Current areas of attention"
    )


# =============================================================================
# Level 3: Social Dynamics (The Network)
# =============================================================================

class PersonRelationship(BaseModel):
    """Relationship metadata for a person."""
    name: str
    tier: RelationshipTier = RelationshipTier.PERIPHERAL
    archetype: PoliticalArchetype = PoliticalArchetype.UNKNOWN
    role: str = ""  # "Manager", "Peer", "Client"
    relationship: str = ""  # "Direct Report", "Spouse"
    linked_goals: List[str] = Field(default_factory=list)  # Goal IDs
    communication_preference: Optional[str] = None
    notes: str = ""


class SocialProfile(BaseModel):
    """Level 3: Social dynamics and network."""
    vip_contacts: List[str] = Field(
        default_factory=list,
        description="People who can bypass DND"
    )
    key_relationships: List[PersonRelationship] = Field(
        default_factory=list,
        description="Important relationship metadata"
    )
    sponsors: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    connectors: List[str] = Field(default_factory=list)


# =============================================================================
# Level 4: Psychological Profile (The User Manual)
# =============================================================================

class PsychologicalProfile(BaseModel):
    """Level 4: Communication and mental preferences."""
    communication_style: CommunicationStyle = CommunicationStyle.DIRECT
    feedback_style: str = "direct"  # "direct" | "sandwich" | "gentle"
    stress_triggers: List[str] = Field(
        default_factory=list,
        description="Patterns that cause anxiety"
    )
    stress_response: str = ""  # How system should respond to stress
    learning_style: str = "text"  # "visual" | "text" | "audio" | "hands-on"
    decision_style: str = "analytical"  # "analytical" | "intuitive" | "deliberate"
    max_back_to_back_meetings: int = 3
    preferred_break_duration: int = 15  # minutes


# =============================================================================
# Complete User Profile
# =============================================================================

class UserProfile(BaseModel):
    """
    Complete 4-Level User Knowledge Model.
    
    This is the "User's Manual" that Cortex uses to personalize all interactions.
    """
    user_id: str
    name: str = ""
    email: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None
    onboarding_complete: bool = False
    
    # The 4 Levels
    biological: BiologicalProfile = Field(default_factory=BiologicalProfile)
    strategic: StrategicProfile = Field(default_factory=StrategicProfile)
    social: SocialProfile = Field(default_factory=SocialProfile)
    psychological: PsychologicalProfile = Field(default_factory=PsychologicalProfile)
    
    # Metadata
    calibration_mode: bool = True  # Shadow mode for first 24-48h
    last_calibration: Optional[str] = None
    profile_confidence: float = 0.0  # 0-1, how confident we are in the profile
    
    def get_optimal_task_slot(self, cognitive_demand: CognitiveDemand) -> Optional[str]:
        """Get optimal time slot for a task based on energy zones."""
        if cognitive_demand == CognitiveDemand.HIGH:
            return self.biological.energy_zones.peak_zone.start
        elif cognitive_demand == CognitiveDemand.LOW:
            return self.biological.energy_zones.trough_zone.start
        return None
    
    def is_vip(self, person_name: str) -> bool:
        """Check if a person is VIP tier."""
        return person_name.lower() in [v.lower() for v in self.social.vip_contacts]
    
    def check_value_conflict(self, option_a: str, option_b: str) -> str:
        """Resolve conflict using value hierarchy."""
        values = [v.lower() for v in self.strategic.value_hierarchy]
        a_idx = next((i for i, v in enumerate(values) if option_a.lower() in v), len(values))
        b_idx = next((i for i, v in enumerate(values) if option_b.lower() in v), len(values))
        return option_a if a_idx <= b_idx else option_b


# =============================================================================
# Graph Schema Extension
# =============================================================================

USER_PROFILE_CYPHER = """
// User Profile Node
CREATE CONSTRAINT user_profile_id IF NOT EXISTS
FOR (u:UserProfile) REQUIRE u.user_id IS UNIQUE;

// User Profile relationships
// (:UserProfile)-[:HAS_GOAL]->(:Goal)
// (:UserProfile)-[:HAS_ANTI_GOAL]->(:AntiGoal)
// (:UserProfile)-[:VIP_CONTACT]->(:Entity {type: 'Person'})
// (:UserProfile)-[:BLOCKS_WITH {reason}]->(:Entity {type: 'Person'})
"""
