# Cortex 🧠

**Personal Cognitive Assistant** - A brain-like AI system that serves as a true extension of the human mind.

## Architecture

```
/cortex
├── /backend
│   ├── /app
│   │   ├── main.py              # FastAPI Entry Point
│   │   ├── dependencies.py      # DB Connections (Neo4j, Redis)
│   │   ├── /agents              # The "Cognitive Modules"
│   │   │   ├── router.py        # Intent Classification (Gateway)
│   │   │   ├── analyst_agent.py # RAG & Graph Query Logic
│   │   │   ├── social_agent.py  # People & Relationship Logic
│   │   │   └── scheduler_agent.py # Calendar & Reminders
│   │   ├── /core
│   │   │   ├── config.py        # Env variables
│   │   │   └── prompts.py       # Centralized System Prompts
│   │   ├── /services
│   │   │   ├── graph_service.py # Neo4j Cypher Helpers
│   │   │   ├── vector_service.py # Embedding Generation
│   │   │   └── consolidation.py # The "Sleep" Cycle
│   │   └── /models
│   │       ├── api_schemas.py   # Pydantic Models for API
│   │       └── graph_schemas.py # Node/Edge Definitions
│   ├── Dockerfile
│   └── requirements.txt
│
├── /frontend                    # React/TypeScript (Vite)
│   ├── /src
│   │   ├── /components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ClarificationQueue.tsx
│   │   │   └── GraphVisualizer.tsx
│   │   ├── /hooks
│   │   │   └── useAgent.ts
│   │   └── /api
│   │       └── client.ts
│   └── package.json
│
├── /database
│   └── schema.cypher            # Neo4j Schema
│
└── docker-compose.yml           # Orchestration
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend   | FastAPI (Async) |
| LLM       | Ollama (llama3.3:70b) |
| Graph DB  | Neo4j 5.x (with Vector Index) |
| Cache     | Redis (Working Memory) |
| Frontend  | React + TypeScript + Vite |
| Orchestration | LangGraph |

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### Option 2: Local Development

```bash
# 1. Start Neo4j
docker run -d --name cortex-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/cortex123 \
  neo4j:5.15-community

# 2. Start Redis
docker run -d --name cortex-redis -p 6379:6379 redis:7-alpine

# 3. Start Ollama
ollama serve

# 4. Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# 5. Frontend
cd frontend
npm install
npm run dev
```

### Access

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/think` | POST | Process a thought |
| `/api/classify` | GET | Debug intent classification |
| `/api/brain/stats` | GET | Brain statistics |
| `/api/brain/search` | GET | Semantic search |
| `/api/brain/people` | GET | Person profiles |
| `/api/graph` | GET | Knowledge graph data |
| `/health` | GET | Health check |

## Core Concepts

### Biological Analogues

- **Perception** (Gateway): `router.py` - Intent classification
- **Memory** (Hippocampus): Neo4j + Vector Index - Hybrid memory
- **Cognition** (Frontal Lobe): LangGraph agents - Reasoning
- **Action** (Motor Cortex): Task execution

### The Double Loop

Every task is analyzed for its contribution to personal growth (Skills & Goals).

### Neurosymbolic Memory

- **Vector Search**: Semantic similarity ("things like X")
- **Graph Search**: Relationship traversal (A→B→C)

## License

MIT
