"""
Cortex - Profile Service
Manages the User Identity in the Graph.
"""

from typing import Optional, Dict, Any
from app.services.graph_service import graph_service
from app.models.user import UserProfileCreate, UserProfileUpdate

class ProfileService:
    
    async def get_profile(self, user_id: str = "default_user") -> Optional[Dict[str, Any]]:
        """
        Get the user profile node.
        """
        query = """
        MATCH (u:User {id: $user_id})
        RETURN u
        """
        records = await graph_service.execute_query(query, {"user_id": user_id})
        if records:
            return self._serialize(records[0].get("u"))
        return None

    async def upsert_profile(self, profile: UserProfileCreate, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Create or update the user profile.
        """
        query = """
        MERGE (u:User {id: $user_id})
        ON CREATE SET 
            u.created_at = datetime(),
            u.updated_at = datetime(),
            u.name = $name,
            u.role = $role,
            u.bio = $bio,
            u.traits = $traits
        ON MATCH SET 
            u.updated_at = datetime(),
            u.name = $name,
            u.role = $role,
            u.bio = $bio,
            u.traits = $traits
        RETURN u
        """
        params = {
            "user_id": user_id,
            "name": profile.name,
            "role": profile.role,
            "bio": profile.bio,
            "traits": profile.traits
        }
        
        records = await graph_service.execute_query(query, params)
        if records:
            return self._serialize(records[0].get("u"))
        return None

    def _serialize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Neo4j types to Python native types."""
        if not data:
            return data
        
        # Convert DateTime to ISO string
        if "created_at" in data and hasattr(data["created_at"], "isoformat"):
            data["created_at"] = data["created_at"].isoformat()
        if "updated_at" in data and hasattr(data["updated_at"], "isoformat"):
            data["updated_at"] = data["updated_at"].isoformat()
            
        return data

profile_service = ProfileService()
