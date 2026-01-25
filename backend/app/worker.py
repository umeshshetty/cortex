"""
Cortex - Background Worker
Consumes tasks from Redis queue and processes them asynchronously.
"""

import asyncio
import json
import redis.asyncio as redis
from app.core.config import settings
from app.services.memory_service import memory_service
from app.services.entity_extractor import entity_extractor
from app.services.graph_service import graph_service
from app.services.vector_service import vector_service
from app.core.database import init_db

# Connect to Redis
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
QUEUE_NAME = "cortex_memory_queue"

async def process_task(task_data: dict):
    """
    Process a single note entry task.
    1. Extract Entities (LLM)
    2. Save to Graph (Neo4j)
    3. Update Vector Index (Neo4j)
    """
    note_id = task_data.get("note_id")
    content = task_data.get("content")
    
    print(f"🤖 Worker: Processing Note {note_id}...")
    
    # 1. Extract Knowledge
    knowledge = await entity_extractor.extract_knowledge(content)
    if not knowledge:
        print(f"⚠️ Worker: No knowledge extracted for Note {note_id}")
        return

    # 2. Save to Graph (Cypher)
    # We construct a complex Cypher query to merge all entities and rels
    entities = knowledge.get("entities", [])
    relationships = knowledge.get("relationships", [])
    
    print(f"   -> Found {len(entities)} Entities, {len(relationships)} Relations")
    
    # Create Thought Node explicitly first (linked to Note ID in future potentially, 
    # but for now we create a Thought node representing this content)
    # Actually, we should match the existing Thought if we created one, or create one?
    # memory_service.add_note only adds to Postgres.
    # So we create a Thought node here.
    
    embedding = await vector_service.get_embedding(content)
    
    cypher = """
    // 1. Create Thought Node with Metadata
    CREATE (t:Thought {
        id: $note_id, 
        content: $content, 
        source: $source,
        timestamp: datetime($timestamp)
    })
    
    // 2. Set Vector Embedding (if available)
    FOREACH (ignoreMe IN CASE WHEN $embedding IS NOT NULL THEN [1] ELSE [] END |
        SET t.embedding = $embedding
    )
    
    // 3. Merge Entities
    WITH t
    UNWIND $entities AS e
    MERGE (n:Entity {name: e.name})
    ON CREATE SET n.type = e.type, n.description = e.description
    MERGE (t)-[:MENTIONS]->(n)
    
    // 4. Merge Relationships between Entities
    WITH t
    UNWIND $relationships AS r
    MATCH (a:Entity {name: r.from})
    MATCH (b:Entity {name: r.to})
    MERGE (a)-[rel:RELATIONSHIP {type: r.type}]->(b)
    """
    
    await graph_service.execute_query(cypher, {
        "note_id": str(note_id),
        "content": content,
        "source": task_data.get("source", "user"),
        "timestamp": task_data.get("timestamp"), # ISO string works with datetime()
        "embedding": embedding,
        "entities": entities,
        "relationships": relationships
    })
    
    print(f"✅ Worker: Note {note_id} processed successfully.")

async def worker_loop():
    """Main Worker Loop"""
    print("👷 Cortex Worker Starting...")
    
    # Initialize DBs
    # await init_db() # Postgres (might not be needed if we don't read from it directly yet)
    await graph_service.connect()
    
    while True:
        try:
            # BRPOP blocks until a generic task is available
            # returns tuple: (queue_name, data)
            result = await redis_client.brpop(QUEUE_NAME, timeout=5)
            
            if result:
                _, data_str = result
                task_data = json.loads(data_str)
                await process_task(task_data)
                
        except Exception as e:
            print(f"❌ Worker Error: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(worker_loop())
