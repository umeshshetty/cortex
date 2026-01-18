// ============================================================================
// Cortex Knowledge Graph Schema
// Personal Cognitive Assistant Database Schema for Neo4j
// ============================================================================

// ============================================================================
// CONSTRAINTS - Ensure data integrity
// ============================================================================

CREATE CONSTRAINT thought_id IF NOT EXISTS 
FOR (t:Thought) REQUIRE t.id IS UNIQUE;

CREATE CONSTRAINT entity_name IF NOT EXISTS 
FOR (e:Entity) REQUIRE e.name IS UNIQUE;

CREATE CONSTRAINT category_name IF NOT EXISTS 
FOR (c:Category) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT action_id IF NOT EXISTS 
FOR (a:ActionItem) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT reminder_id IF NOT EXISTS 
FOR (r:Reminder) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT task_id IF NOT EXISTS 
FOR (t:Task) REQUIRE t.id IS UNIQUE;

// ============================================================================
// INDEXES - Speed up queries
// ============================================================================

CREATE INDEX thought_timestamp IF NOT EXISTS 
FOR (t:Thought) ON (t.timestamp);

CREATE INDEX entity_type IF NOT EXISTS 
FOR (e:Entity) ON (e.type);

CREATE INDEX action_status IF NOT EXISTS 
FOR (a:ActionItem) ON (a.status);

CREATE INDEX action_urgency IF NOT EXISTS 
FOR (a:ActionItem) ON (a.urgency);

CREATE INDEX reminder_datetime IF NOT EXISTS 
FOR (r:Reminder) ON (r.datetime);

CREATE INDEX reminder_status IF NOT EXISTS 
FOR (r:Reminder) ON (r.status);

CREATE INDEX thought_next_review IF NOT EXISTS 
FOR (t:Thought) ON (t.next_review);

// ============================================================================
// VECTOR INDEX - Semantic search (Neo4j 5.11+)
// ============================================================================

CREATE VECTOR INDEX thought_embeddings IF NOT EXISTS
FOR (t:Thought)
ON (t.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 384,
        `vector.similarity_function`: 'cosine'
    }
};

// ============================================================================
// FULLTEXT INDEX - Text search
// ============================================================================

CREATE FULLTEXT INDEX thought_content IF NOT EXISTS
FOR (t:Thought)
ON EACH [t.content, t.summary];

CREATE FULLTEXT INDEX entity_search IF NOT EXISTS
FOR (e:Entity)
ON EACH [e.name, e.description];

// ============================================================================
// RELATIONSHIP PATTERNS (Documented, not enforced)
// ============================================================================

// Core Knowledge Flow:
// (:Thought)-[:MENTIONS]->(:Entity)
// (:Thought)-[:BELONGS_TO]->(:Category)
// (:Thought)-[:IMPLIES]->(:ActionItem)

// Atomization:
// (:Thought)-[:ATOMIZED_FROM]->(:Thought)

// Entity Connections:
// (:Entity)-[:CONNECTED_TO]->(:Entity)
// (:Entity)-[:WORKS_ON]->(:Entity {type: 'Project'})
// (:Entity {type: 'Person'})-[:REPORTS_TO]->(:Entity {type: 'Person'})

// Task Hierarchy:
// (:Task)-[:HAS_SUBTASK]->(:Task)
// (:Task)-[:BLOCKS]->(:Task)

// Serendipity:
// (:Entity)-[:SIMILAR_TO {score: float}]->(:Entity)

// ============================================================================
// SAMPLE DATA (Optional - for testing)
// ============================================================================

// Create default categories (PARA method)
MERGE (p:Category {name: 'Project'})
SET p.description = 'Active projects with deadlines';

MERGE (a:Category {name: 'Area'})
SET a.description = 'Ongoing responsibilities';

MERGE (r:Category {name: 'Resource'})
SET r.description = 'Reference material and learning';

MERGE (ar:Category {name: 'Archive'})
SET ar.description = 'Completed or inactive items';
