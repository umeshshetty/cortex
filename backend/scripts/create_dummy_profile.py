import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.models.user_profile import (
    UserProfile, NorthStarGoal, AntiGoal, Chronotype, CommunicationStyle
)
from app.agents.onboarding import save_user_profile
from app.dependencies import init_neo4j, close_connections

async def create_dummy_data():
    print("🚀 Creating Dummy User Profile: Alex Mercer")
    
    # Initialize DB
    await init_neo4j()
    
    try:
        # 1. Create Base Profile
        profile = UserProfile(user_id="user_123")
        profile.name = "Alex Mercer"
        profile.onboarding_complete = True
        profile.calibration_mode = False
        profile.profile_confidence = 0.9
        
        # 2. Biological (Chronotype)
        profile.biological.chronotype = Chronotype.OWL
        profile.biological.timezone = "America/New_York"
        profile.biological.work_start = "10:00"
        profile.biological.work_end = "19:00"
        
        # 3. Social (VIPs)
        profile.social.vip_contacts = ["Sarah (CEO)", "James (Product)", "Emma (Lead Eng)"]
        
        # 4. Strategic (Goals)
        ns_goal = NorthStarGoal(
            id="ns_api_mig",
            title="Launch API Migration by Q3",
            description="Migrate legacy monolith to microservices",
            deadline="2026-09-30"
        )
        profile.strategic.north_star_goals = [ns_goal]
        
        anti_goal = AntiGoal(
            id="ag_no_mornings",
            description="No meetings before 11am",
            severity="hard"
        )
        profile.strategic.anti_goals = [anti_goal]
        
        profile.strategic.value_hierarchy = ["Speed over perfection", "Async over synchronous"]
        
        # 5. Psychological
        profile.psychological.communication_style = CommunicationStyle.DIRECT
        
        print("💾 Saving to Neo4j...")
        await save_user_profile(profile)
        print("✅ Data successfully ingested!")
        print(f"User: {profile.name} (ID: {profile.user_id})")
        print(f"Goal: {ns_goal.title}")
        print(f"Chronotype: {profile.biological.chronotype.value}")
        
    except Exception as e:
        print(f"❌ Error saving data: {e}")
    finally:
        await close_connections()

if __name__ == "__main__":
    asyncio.run(create_dummy_data())
