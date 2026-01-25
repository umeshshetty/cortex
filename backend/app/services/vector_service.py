"""
Cortex - Vector Service
Handles Embedding Generation and Vector Search operations.
"""

from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
from app.services.graph_service import graph_service

class VectorService:
    def __init__(self):
        # Initialize OpenAI Embeddings (384 dim for 'text-embedding-3-small' or similar)
        # Note: 'text-embedding-3-small' is 1536 dims by default. 
        # For cost/speed 'all-MiniLM-L6-v2' (384) is common in local setups, 
        # but since we are using OpenAI key, we'll default to OpenAI's standard.
        # Let's assume standard 'text-embedding-3-small' -> 1536 dimensions.
        if settings.OPENAI_API_KEY:
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.OPENAI_API_KEY
            )
        else:
            # Fallback or Local Mock (for dev without keys)
            self.embeddings = None
            print("⚠️ No OPENAI_API_KEY found. Vector operations will fail.")

    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        if not self.embeddings:
            return []
        
        # Helper to run sync LangChain method in async loop if needed, 
        # but OpenAIEmbeddings.embed_query is usually fast enough or we can use aembed_query
        return await self.embeddings.aembed_query(text)

    async def create_vector_index(self):
        """
        Create Vector Index in Neo4j if it doesn't exist.
        Targeting 'Thought' nodes with 'embedding' property.
        """
        # 1536 dimensions for text-embedding-3-small
        query = """
        CREATE VECTOR INDEX thought_embeddings IF NOT EXISTS
        FOR (t:Thought)
        ON (t.embedding)
        OPTIONS {indexConfig: {
         `vector.dimensions`: 1536,
         `vector.similarity_function`: 'cosine'
        }}
        """
        await graph_service.execute_query(query)

    async def search_similar_thoughts(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform Vector Search on Thought nodes.
        """
        embedding = await self.get_embedding(query_text)
        if not embedding:
            return []

        cypher = """
        CALL db.index.vector.queryNodes('thought_embeddings', $limit, $embedding)
        YIELD node AS thought, score
        RETURN thought, score
        """
        
        return await graph_service.execute_query(cypher, {
            "limit": limit,
            "embedding": embedding
        })

vector_service = VectorService()
