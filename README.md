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
- OpenAI API Key

### 2. Configuration
Create a `.env` file in `backend/`:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and add your keys:
```ini
OPENAI_API_KEY=sk-...
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
```

### 3. Start System
```bash
docker-compose up -d --build
```

### 4. Verify
Check system health:
```bash
curl http://localhost:8000/health
# {"status":"healthy","version":"2.0.0"}
```

Test LLM connection (requires API Key):
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"message": "Hello"}' \
  http://localhost:8000/test/chat
```

## 📝 Next Steps

This is a blank canvas. To build the new Cortex:
1.  **Frontend**: Initialize a new frontend project in `/frontend`.
2.  **Agents**: Add new agent logic to `backend/app/agents`.
3.  **Memory**: Implement graph/vector storage logic.
