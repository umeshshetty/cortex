"""
Cortex - Onboarding Agent
Day 0 Protocol - Progressive context injection through conversation.

Phases:
1. Digital Handshake (OAuth connections)
2. North Star Interview (Strategic questions)
3. Shadow Mode (Calibration)
4. Living Profile (Background form filling)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from app.models.user_profile import (
    UserProfile, BiologicalProfile, StrategicProfile, 
    SocialProfile, PsychologicalProfile,
    Chronotype, NorthStarGoal, AntiGoal, PersonRelationship,
    RelationshipTier, CommunicationStyle
)
from app.core.llm_tier import llm_router, LLMTier


# The 5 Strategic Questions for Day 0
STRATEGIC_QUESTIONS = [
    {
        "id": "vip_hierarchy",
        "question": "Who are the 3 people whose emails I should never miss?",
        "populates": "social.vip_contacts",
        "follow_up": "What's your relationship with {name}? (e.g., Manager, Spouse, Co-founder)"
    },
    {
        "id": "north_star",
        "question": "If this year is a huge success, what is the one thing you will have finished?",
        "populates": "strategic.north_star_goals",
        "follow_up": "What's blocking you from achieving this right now?"
    },
    {
        "id": "friction",
        "question": "What is the most annoying part of your typical week?",
        "populates": "strategic.anti_goals",
        "follow_up": "Should I actively prevent this or just warn you?"
    },
    {
        "id": "rhythm",
        "question": "When are you completely useless at work? (e.g., '3PM slump', 'before coffee')",
        "populates": "biological.chronotype",
        "follow_up": "And when do you do your best thinking?"
    },
    {
        "id": "values",
        "question": "If a high-paying client calls during dinner with family, do you take it?",
        "populates": "strategic.value_hierarchy",
        "follow_up": "So you'd prioritize {value1} over {value2}?"
    }
]


class OnboardingAgent:
    """
    Day 0 Protocol Agent.
    
    Guides user through onboarding via conversational interview
    while building their profile in the background.
    """
    
    def __init__(self):
        self.current_question_idx = 0
        self.collected_data: Dict[str, Any] = {}
        self.profile: Optional[UserProfile] = None
    
    async def start_onboarding(self, user_id: str) -> Dict[str, Any]:
        """
        Start the onboarding process.
        
        Returns:
            Initial greeting and first question
        """
        # Create base profile
        self.profile = UserProfile(user_id=user_id)
        self.profile.calibration_mode = True
        
        greeting = await self._generate_greeting()
        first_question = STRATEGIC_QUESTIONS[0]["question"]
        
        return {
            "phase": "interview",
            "question_id": STRATEGIC_QUESTIONS[0]["id"],
            "message": f"{greeting}\n\n{first_question}",
            "progress": 0,
            "total_questions": len(STRATEGIC_QUESTIONS)
        }
    
    async def process_response(
        self, 
        user_id: str, 
        question_id: str, 
        response: str
    ) -> Dict[str, Any]:
        """
        Process user's response to an onboarding question.
        
        Returns:
            Next question or completion status
        """
        # Find current question
        current_q = next(
            (q for q in STRATEGIC_QUESTIONS if q["id"] == question_id),
            None
        )
        
        if not current_q:
            return {"error": "Unknown question"}
        
        # Extract structured data from response
        extracted = await self._extract_from_response(
            question_id=question_id,
            response=response,
            populates=current_q["populates"]
        )
        
        self.collected_data[question_id] = extracted
        
        # Update profile
        await self._update_profile(current_q["populates"], extracted)
        
        # Move to next question
        current_idx = STRATEGIC_QUESTIONS.index(current_q)
        next_idx = current_idx + 1
        
        if next_idx >= len(STRATEGIC_QUESTIONS):
            # Onboarding complete
            return await self._complete_onboarding(user_id)
        
        next_q = STRATEGIC_QUESTIONS[next_idx]
        
        # Generate transition + next question
        transition = await self._generate_transition(extracted)
        
        return {
            "phase": "interview",
            "question_id": next_q["id"],
            "message": f"{transition}\n\n{next_q['question']}",
            "progress": next_idx,
            "total_questions": len(STRATEGIC_QUESTIONS),
            "extracted": extracted
        }
    
    async def _extract_from_response(
        self, 
        question_id: str, 
        response: str,
        populates: str
    ) -> Dict[str, Any]:
        """Extract structured data from user's natural language response."""
        
        system_prompt = f"""You are extracting structured data from a user's response.
Question ID: {question_id}
Target field: {populates}

Extract the relevant information as JSON. Be structured but preserve user's language."""
        
        prompt = f"User's response: {response}\n\nExtract as JSON:"
        
        result = await llm_router.invoke(
            tier=LLMTier.REFLEX,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        import json
        try:
            start = result.find('{')
            end = result.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(result[start:end])
        except json.JSONDecodeError:
            pass
        
        return {"raw_response": response}
    
    async def _update_profile(self, field_path: str, data: Dict) -> None:
        """Update the user profile based on extracted data."""
        if not self.profile:
            return
        
        parts = field_path.split(".")
        
        if parts[0] == "social":
            if "vip_contacts" in field_path:
                names = data.get("names", data.get("people", []))
                if isinstance(names, str):
                    names = [n.strip() for n in names.split(",")]
                self.profile.social.vip_contacts = names
        
        elif parts[0] == "strategic":
            if "north_star_goals" in field_path:
                goal = NorthStarGoal(
                    id="ns_1",
                    title=data.get("goal", data.get("raw_response", "")),
                    description=data.get("description", ""),
                    deadline=data.get("deadline")
                )
                self.profile.strategic.north_star_goals = [goal]
            
            elif "anti_goals" in field_path:
                anti = AntiGoal(
                    id="ag_1",
                    description=data.get("friction", data.get("raw_response", "")),
                    severity="hard" if data.get("prevent", False) else "soft"
                )
                self.profile.strategic.anti_goals = [anti]
            
            elif "value_hierarchy" in field_path:
                values = data.get("values", data.get("priorities", []))
                if values:
                    self.profile.strategic.value_hierarchy = values
        
        elif parts[0] == "biological":
            if "chronotype" in field_path:
                peak = data.get("peak_time", "").lower()
                if "morning" in peak or "early" in peak:
                    self.profile.biological.chronotype = Chronotype.LARK
                elif "night" in peak or "evening" in peak or "late" in peak:
                    self.profile.biological.chronotype = Chronotype.OWL
        
        self.profile.updated_at = datetime.now().isoformat()
    
    async def _generate_greeting(self) -> str:
        """Generate personalized greeting."""
        return """👋 Welcome to Cortex!

I'm going to ask you 5 quick questions to understand how I can best help you. 
These will help me learn your priorities, relationships, and work style.

Think of this as teaching me to be your personal Chief of Staff."""
    
    async def _generate_transition(self, extracted: Dict) -> str:
        """Generate a natural transition between questions."""
        if not extracted:
            return "Got it."
        
        # Use LLM for natural transition
        prompt = f"User just shared: {extracted}. Generate a brief, warm acknowledgment (1 sentence)."
        
        response = await llm_router.invoke(
            tier=LLMTier.REFLEX,
            prompt=prompt,
            system_prompt="You are a friendly assistant. Be brief and warm."
        )
        
        return response.strip()
    
    async def _complete_onboarding(self, user_id: str) -> Dict[str, Any]:
        """Complete onboarding and save profile."""
        if self.profile:
            self.profile.onboarding_complete = True
            self.profile.calibration_mode = True  # Still in shadow mode
            self.profile.profile_confidence = 0.3  # Initial confidence
            
            # Save to graph
            await save_user_profile(self.profile)
        
        return {
            "phase": "complete",
            "message": """✅ Onboarding complete!

I'm now entering **Shadow Mode** for the next 24-48 hours. I'll observe your patterns and generate draft suggestions without acting on them.

At the end of Shadow Mode, I'll show you what I've learned and you can fine-tune my understanding.

In the meantime, just use me normally - drop thoughts, ask questions, and I'll learn from how you work.""",
            "profile_summary": self._summarize_profile(),
            "next_steps": [
                "I'll be in Shadow Mode for 24-48 hours",
                "Use /settings to view and edit your profile anytime",
                "Just start chatting - I'll learn as we go!"
            ]
        }
    
    def _summarize_profile(self) -> Dict[str, Any]:
        """Generate a summary of the collected profile."""
        if not self.profile:
            return {}
        
        return {
            "chronotype": self.profile.biological.chronotype.value,
            "vips": self.profile.social.vip_contacts,
            "north_star": self.profile.strategic.north_star_goals[0].title if self.profile.strategic.north_star_goals else None,
            "anti_goals": [a.description for a in self.profile.strategic.anti_goals],
            "values": self.profile.strategic.value_hierarchy[:3]
        }


async def save_user_profile(profile: UserProfile) -> bool:
    """Save user profile to Neo4j."""
    from app.dependencies import get_neo4j
    
    driver = await get_neo4j()
    
    async with driver.session() as session:
        await session.run("""
            MERGE (u:UserProfile {user_id: $user_id})
            SET u.name = $name,
                u.chronotype = $chronotype,
                u.timezone = $timezone,
                u.work_start = $work_start,
                u.work_end = $work_end,
                u.vip_contacts = $vip_contacts,
                u.value_hierarchy = $value_hierarchy,
                u.communication_style = $comm_style,
                u.onboarding_complete = $onboarding_complete,
                u.calibration_mode = $calibration_mode,
                u.profile_confidence = $confidence,
                u.updated_at = datetime()
        """,
            user_id=profile.user_id,
            name=profile.name,
            chronotype=profile.biological.chronotype.value,
            timezone=profile.biological.timezone,
            work_start=profile.biological.work_start,
            work_end=profile.biological.work_end,
            vip_contacts=profile.social.vip_contacts,
            value_hierarchy=profile.strategic.value_hierarchy,
            comm_style=profile.psychological.communication_style.value,
            onboarding_complete=profile.onboarding_complete,
            calibration_mode=profile.calibration_mode,
            confidence=profile.profile_confidence
        )
        
        # Save North Star Goals
        for goal in profile.strategic.north_star_goals:
            await session.run("""
                MERGE (g:Goal {id: $id})
                SET g.title = $title, g.description = $desc, g.deadline = $deadline
                WITH g
                MATCH (u:UserProfile {user_id: $user_id})
                MERGE (u)-[:HAS_GOAL]->(g)
            """, 
                id=goal.id, title=goal.title, 
                desc=goal.description, deadline=goal.deadline,
                user_id=profile.user_id
            )

        # Save Anti-Goals
        for anti in profile.strategic.anti_goals:
            await session.run("""
                MERGE (a:AntiGoal {id: $id})
                SET a.description = $desc, a.severity = $severity
                WITH a
                MATCH (u:UserProfile {user_id: $user_id})
                MERGE (u)-[:HAS_ANTI_GOAL]->(a)
            """, 
                id=anti.id, desc=anti.description, 
                severity=anti.severity,
                user_id=profile.user_id
            )
    
    return True


# Singleton instance
onboarding_agent = OnboardingAgent()
