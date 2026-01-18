"""
Cortex - Vector Service
Embedding generation and semantic search.
Uses Neo4j Vector Index when available, gracefully degrades when not.
"""

from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

from app.dependencies import get_neo4j
from app.core.config import settings


# Initialize embedding model (cached at module level)
_embedding_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """Get or initialize the embedding model."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _embedding_model


def generate_embedding(text: str) -> List[float]:
    """Generate embedding vector for text."""
    model = get_embedding_model()
    embedding = model.encode(text)
    return embedding.tolist()


# =============================================================================
# Vector Index Operations
# =============================================================================

async def add_embedding(thought_id: str, content: str) -> bool:
    """
    Add embedding to a thought node for vector search.
    Uses Neo4j's native vector index.
    """
    driver = await get_neo4j()
    embedding = generate_embedding(content)
    
    async with driver.session() as session:
        await session.run("""
            MATCH (t:Thought {id: $thought_id})
            SET t.embedding = $embedding
        """, thought_id=thought_id, embedding=embedding)
    
    return True


async def search_similar(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search for semantically similar thoughts using vector similarity.
    Gracefully returns empty list if vector index doesn't exist.
    """
    driver = await get_neo4j()
    query_embedding = generate_embedding(query)
    
    async with driver.session() as session:
        try:
            # Use Neo4j vector similarity search
            result = await session.run("""
                CALL db.index.vector.queryNodes('thought_embeddings', $limit, $embedding)
                YIELD node, score
                RETURN node.id as id, node.content as content, 
                       node.summary as summary, score
                ORDER BY score DESC
            """, limit=limit, embedding=query_embedding)
            
            return await result.data()
        except Exception as e:
            # Vector index may not exist yet, return empty list
            # Thoughts will still be processed, just without semantic context
            return []


async def find_distant_but_similar(
    focus_embedding: List[float],
    exclude_ids: List[str],
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Find thoughts that are semantically similar but graph-distant.
    Used by the Serendipity Engine.
    """
    driver = await get_neo4j()
    
    async with driver.session() as session:
        try:
            result = await session.run("""
                CALL db.index.vector.queryNodes('thought_embeddings', $limit, $embedding)
                YIELD node, score
                WHERE NOT node.id IN $exclude_ids
                RETURN node.id as id, node.content as content, 
                       node.summary as summary, score as semantic_score
            """, embedding=focus_embedding, exclude_ids=exclude_ids, limit=limit)
            
            return await result.data()
        except Exception:
            return []


async def find_similar_pairs(threshold: float = 0.95) -> List[Dict[str, str]]:
    """
    Find highly similar thought pairs (for deduplication).
    Note: This is computationally expensive, only run during consolidation.
    """
    # Without GDS library, we can't easily find pairs
    # Return empty list - consolidation will skip this step
    return []


# =============================================================================
# Index Management
# =============================================================================

async def ensure_vector_index() -> bool:
    """
    Ensure the vector index exists on Thought nodes.
    Run this on startup.
    """
    driver = await get_neo4j()
    
    async with driver.session() as session:
        try:
            await session.run("""
                CREATE VECTOR INDEX thought_embeddings IF NOT EXISTS
                FOR (t:Thought)
                ON (t.embedding)
                OPTIONS {
                    indexConfig: {
                        `vector.dimensions`: 384,
                        `vector.similarity_function`: 'cosine'
                    }
                }
            """)
            print("✅ Vector index 'thought_embeddings' ready")
            return True
        except Exception as e:
            print(f"⚠️ Vector index creation failed (may require Neo4j 5.11+): {e}")
            return False
