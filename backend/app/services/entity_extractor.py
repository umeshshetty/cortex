"""
Cortex - Entity Extractor
Extracts Knowledge Graph Entities and Relationships from raw text.
"""

import json
from typing import Dict, Any, List, Optional
from app.core.llm_tier import llm_client

EXTRACTION_PROMPT = """You are a Knowledge Graph extraction engine.
Analyze the following text and extract:
1. Entities: Important concepts, people, places, projects, or technologies.
2. Relationships: How these entities relate to each other.

Return ONLY a valid JSON object with this schema:
{{
  "entities": [
    {{ "name": "Entity Name", "type": "Person|Topic|Project|Location|Other", "description": "Short blurb" }}
  ],
  "relationships": [
    {{ "from": "Entity Name A", "to": "Entity Name B", "type": "CONNECTED_TO|WORKS_ON|LOCATED_IN|RELATED_TO" }}
  ]
}}

Text to analyze:
{input}

JSON Output:"""

REFLECTION_PROMPT = """You are a Reflector Agent.
Your job is to look at a user's thought and generate 1-2 thoughtful questions that would help clarify or expand on the idea.
Do not ask generic questions. Be specific to the content.

User's Thought:
{input}

Return ONLY the questions as a JSON list of strings.
Example: ["Which specific project is this related to?", "Are there any deadlines associated with this?"]
JSON Output:"""

class EntityExtractor:
    async def extract_knowledge(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract entities and relationships from text.
        """
        prompt = EXTRACTION_PROMPT.format(input=text)
        
        response = await llm_client.chat(
            prompt=prompt,
            system_prompt="You are a precise JSON extractor. Return only valid JSON.",
            session_id="knowledge-extraction"
        )
        
        try:
            # Clean up response
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()
            
            data = json.loads(clean)
            return data
        except Exception as e:
            print(f"Entity Extraction Failed: {e}")
            return None

    async def generate_reflection(self, text: str) -> List[str]:
        """
        Generate clarifying questions based on the text.
        """
        prompt = REFLECTION_PROMPT.format(input=text)
        
        response = await llm_client.chat(
            prompt=prompt,
            system_prompt="You are a precise JSON extractor. Return only valid JSON.",
            session_id="reflection-generation"
        )
        
        try:
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            clean = clean.strip()
            
            questions = json.loads(clean)
            if isinstance(questions, list):
                return questions
            return []
        except Exception as e:
            print(f"Reflection Generation Failed: {e}")
            return []


entity_extractor = EntityExtractor()
