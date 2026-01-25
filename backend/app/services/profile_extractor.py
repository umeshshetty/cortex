"""
Cortex - Profile Extractor
Uses LLM to extract structured profile data from natural language.
"""

import json
from typing import Optional, Dict, Any
from app.core.llm_tier import llm_client
from app.services.profile_service import profile_service

EXTRACTION_PROMPT = """You are a profile data extractor. Given the user's natural language description, extract structured profile information.

Return ONLY a valid JSON object with these fields (omit any that aren't mentioned):
- name: string (the person's name)
- role: string (their job title or professional role)
- bio: string (a brief description of them, 1-2 sentences)
- traits: list of strings (personality traits, interests, skills)

If any field is not clearly mentioned, omit it from the JSON.

User's description:
{input}

JSON Output:"""


class ProfileExtractor:
    """Extracts structured profile data from natural language using LLM."""
    
    async def extract_and_save(self, raw_input: str, user_id: str = "default_user") -> Dict[str, Any]:
        """
        Takes natural language input, extracts profile data via LLM, and saves to graph.
        
        Args:
            raw_input: Natural language description of the user
            user_id: The user ID to save the profile under
            
        Returns:
            The saved profile data
        """
        # Step 1: Extract structured data using LLM
        extraction_result = await self._extract(raw_input)
        
        if not extraction_result:
            return {"error": "Could not extract profile data from input"}
        
        # Step 2: Save to graph via ProfileService
        from app.models.user import UserProfileCreate
        
        profile_data = UserProfileCreate(
            name=extraction_result.get("name", "User"),
            role=extraction_result.get("role"),
            bio=extraction_result.get("bio"),
            traits=extraction_result.get("traits", [])
        )
        
        saved = await profile_service.upsert_profile(profile_data, user_id)
        
        return {
            "extracted": extraction_result,
            "saved": saved,
            "status": "success"
        }
    
    async def _extract(self, raw_input: str) -> Optional[Dict[str, Any]]:
        """Use LLM to extract structured data."""
        prompt = EXTRACTION_PROMPT.format(input=raw_input)
        
        response = await llm_client.chat(
            prompt=prompt,
            system_prompt="You are a precise JSON extractor. Return only valid JSON, no markdown.",
            session_id="profile-extraction"
        )
        
        # Parse JSON from response
        try:
            # Clean up response (remove markdown code blocks if present)
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()
            
            return json.loads(clean)
        except json.JSONDecodeError as e:
            print(f"Failed to parse LLM response as JSON: {e}")
            print(f"Response was: {response}")
            return None


profile_extractor = ProfileExtractor()
