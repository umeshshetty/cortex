# Cortex 🧠 (Clean Slate)

**Personal Cognitive Assistant** - A brain-like AI system.

> [!NOTE]
> This repository has been reset to a clean slate. It currently contains the **infrastructure backbone** only.

## 🏗 Architecture (Current State)

The system is stripped down to its core infrastructure, ready for a new implementation.

```
/cortex
├── /backend
│   ├── /app
│   │   ├── /core
│   │   │   ├── config.py        # Environment Config
│   │   │   └── llm_tier.py      # Basic LLM Client + Langfuse
│   │   └── main.py              # Minimal FastAPI Entry Point
│   ├── Dockerfile
│   └── requirements.txt
│
├── /database
│   └── schema.cypher            # Neo4j Schema (Preserved)
│
└── docker-compose.yml           # Core Infrastructure
```

## 🛠 Infrastructure Stack

| Component | Status | Access |
|-----------|--------|--------|
| **Backend** | Minimal (FastAPI) | `http://localhost:8000` |
| **Neo4j** | Running | `bolt://localhost:7687` (Browser: `:7474`) |
| **Redis** | Running | `localhost:6379` |
| **Langfuse** | Running | `http://localhost:3001` |

## 🚀 Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- OpenAI API Key (for LLM features)

### 2. Configuration
```bash
cp backend/.env.example backend/.env
# Edit backend/.env and add your API keys
```

### 3. Start System
```bash
docker-compose up -d --build
```

### 4. Verify
```bash
curl http://localhost:8000/health
# {"status":"healthy","version":"2.0.0"}
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/profile` | GET | Get user profile |
| `/api/profile` | POST | Create/Update profile |
| `/api/memory/note` | POST | Add raw note to TimeDB |
| `/api/memory/stream` | GET | Get recent notes |
| `/api/memory/graph` | GET | Search Knowledge Graph |
| `/test/chat` | POST | Test LLM connection |

## 📝 Next Steps

This is a living system. Current capabilities:
1.  **User Profile**: Anchor for all memories (Neo4j).
2.  **TimeDB**: Chronological raw note storage (Postgres).
3.  **GraphRAG**: Knowledge Graph backbone (Neo4j).

Future additions:
- Vector embeddings for semantic search
- LLM-powered entity extraction
- Frontend UI

