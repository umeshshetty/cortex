import { useState } from 'react';
import { MermaidDiagram } from './MermaidDiagram';
import './Architecture.css';

type Tab = 'philosophy' | 'infrastructure' | 'backend' | 'data' | 'frontend' | 'algorithms' | 'roadmap';

export function Architecture() {
    const [activeTab, setActiveTab] = useState<Tab>('philosophy');

    const renderPhilosophy = () => (
        <div className="arch-section animate-fade-in">
            <h2>1. The Cognitive Architecture</h2>
            <p className="arch-subtitle">Philosophy & Design Patterns</p>

            <div className="arch-card">
                <h3>Neuro-Symbolic AI</h3>
                <p>
                    Cortex implements a <strong>Neuro-Symbolic Architecture</strong>. This bridges the gap between two opposing paradigms of AI:
                </p>
                <ul style={{ marginLeft: '1.5rem', marginTop: '0.5rem', color: '#cbd5e1' }}>
                    <li><strong>Symbolic AI (Neo4j):</strong> Handles explicit, structured logic. It is deterministic and queryable. "A implies B".</li>
                    <li><strong>Connectionist AI (LLMs):</strong> Handles implicit, fuzzy, and creative tasks. "Summarize this paragraph".</li>
                </ul>
            </div>

            <div className="arch-card">
                <h3>The "Sleep Processing" Metaphor</h3>
                <p>
                    The system mimics biological brains with two distinct phases:
                </p>
                <div className="info-grid" style={{ marginTop: '1rem' }}>
                    <div className="info-item">
                        <span className="info-label">Wakefulness (Synchronous)</span>
                        <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                            User captures thoughts. Optimized for <strong>Write Speed (O(1))</strong>.
                            No heavy processing. Dumps to Write-Ahead Log (Postgres).
                        </p>
                    </div>
                    <div className="info-item">
                        <span className="info-label">Sleep (Asynchronous)</span>
                        <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                            Background workers "dream". They pull from the log, use LLMs to extract entities,
                            and weave them into the Long-Term Memory (Graph).
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )

    const renderInfrastructure = () => (
        <div className="arch-section animate-fade-in">
            <h2>2. Infrastructure Kernel</h2>
            <p className="arch-subtitle">Docker Service Mesh & Network Topology</p>

            <div className="arch-card">
                <h3>Network Isolation Strategy (Zero Trust)</h3>
                <p>
                    <strong>Network Name:</strong> <code>cortex-network</code> (Bridge Driver)<br />
                    <strong>Security Principle:</strong> The databases (Neo4j, Postgres, Redis) are completely invisible to the host machine's public interface.
                    Only the Frontend (:3000) and API Gateway (:8000) allow ingress.
                </p>
            </div>

            <div className="arch-diagram-container">
                <MermaidDiagram chart={`
                graph TB
                    subgraph "Host Machine"
                        Browser[Web Browser]
                    end
                    
                    subgraph "Docker Network: cortex-network"
                        FE[frontend :3000]
                        BE[backend :8000]
                        DB_Graph[neo4j :7687]
                        DB_Time[memory-db :5432]
                        Redis[redis :6379]
                    end
                    
                    Browser -->|Public Access| FE
                    Browser -->|Public Access| BE
                    FE -->|Internal DNS| BE
                    BE -->|Internal DNS| DB_Graph
                    BE -->|Internal DNS| DB_Time
                    BE -->|Internal DNS| Redis
                `} />
            </div>

            <div className="arch-card">
                <h3>Service Matrix</h3>
                <div style={{ marginTop: '1rem', overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                        <thead>
                            <tr style={{ background: 'rgba(255,255,255,0.05)', textAlign: 'left' }}>
                                <th style={{ padding: '0.5rem' }}>Service</th>
                                <th style={{ padding: '0.5rem' }}>Internal DNS</th>
                                <th style={{ padding: '0.5rem' }}>Port</th>
                                <th style={{ padding: '0.5rem' }}>Health Check Strategy</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style={{ padding: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>Backend</td>
                                <td style={{ padding: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}><code>backend</code></td>
                                <td style={{ padding: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>8000</td>
                                <td style={{ padding: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>HTTP 200 on /health</td>
                            </tr>
                            <tr>
                                <td style={{ padding: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>Neo4j</td>
                                <td style={{ padding: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}><code>neo4j</code></td>
                                <td style={{ padding: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>7687</td>
                                <td style={{ padding: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>Bolt Handshake</td>
                            </tr>
                            <tr>
                                <td style={{ padding: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>Postgres</td>
                                <td style={{ padding: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}><code>memory-db</code></td>
                                <td style={{ padding: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>5432</td>
                                <td style={{ padding: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>pg_isready</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );

    const renderBackend = () => (
        <div className="arch-section animate-fade-in">
            <h2>3. Backend Cortex</h2>
            <p className="arch-subtitle">FastAPI Internals & Lifecycle</p>

            <div className="arch-card">
                <h3>3.1 Application Lifecycle (`main.py`)</h3>
                <p>
                    We use the <code>lifespan</code> context manager (Python 3.11+) for robust resource management.
                </p>
                <code style={{ display: 'block', marginTop: '1rem', whiteSpace: 'pre' }}>
                    {`@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()  # Postgres Create Tables
    await graph_service.connect() # Neo4j Pool
    yield
    # Shutdown
    await graph_service.close() # Drain Pools`}
                </code>
            </div>

            <div className="arch-card">
                <h3>3.2 Connection Management (Singletons)</h3>
                <p>
                    Database connections are expensive (~50ms handshake). We use <strong>Singletons</strong> to maintain persistent connection pools.
                </p>
                <div className="info-grid">
                    <div className="info-item">
                        <span className="info-label">GraphService</span>
                        <div style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
                            Maintains one <code>AsyncDriver</code> instance.
                            Uses `async with session` for per-request isolation.
                            Explicitly consumes streams to avoid "Session Expired".
                        </div>
                    </div>
                    <div className="info-item">
                        <span className="info-label">LLMClient</span>
                        <div style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
                            Global instance.
                            <strong>Observability:</strong> Injects `LangfuseHandler` automatically.
                            Supports <strong>Session Scoping</strong> for multi-turn chat memory.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderData = () => (
        <div className="arch-section animate-fade-in">
            <h2>4. Data Synapse</h2>
            <p className="arch-subtitle">Polyglot Persistence Details</p>

            <div className="arch-card">
                <h3>4.1 Semantic Memory (Neo4j)</h3>
                <p>
                    The Knowledge Graph uses a <strong>Labeled Property Graph</strong> model.
                    It supports <strong>Vector Search</strong> via the `thought_embeddings` index (384-dimensions, Cosine Similarity).
                </p>
                <div className="arch-diagram-container" style={{ margin: '1rem 0' }}>
                    <MermaidDiagram chart={`
                    erDiagram
                        User ||--o{ Thought : HAD_THOUGHT
                        Thought ||--o{ Entity : MENTIONS
                        Thought ||--o{ Category : BELONGS_TO
                        Entity }|--|{ Entity : CONNECTED_TO
                        
                        User {
                            string id
                            string name
                            string[] traits
                        }
                        Thought {
                            uuid id
                            string content
                            float[] embedding
                        }
                    `} />
                </div>
            </div>

            <div className="arch-card">
                <h3>4.2 Episodic Memory (Postgres)</h3>
                <p>
                    The <code>notes</code> table is an <strong>Immutable Write-Ahead Log</strong>.
                    It is optimized for high-throughput writes ($O(1)$) and Time-Range reads ($O(\log N)$ via B-Tree Index).
                </p>
            </div>
        </div>
    );

    const renderFrontend = () => (
        <div className="arch-section animate-fade-in">
            <h2>5. The Interface</h2>
            <p className="arch-subtitle">React 19 + TypeScript Component Patterns</p>

            <div className="arch-card">
                <h3>5.1 The "Lifted Signal" Pattern</h3>
                <p>
                    Instead of Redux, we coordinate sibling components (`NoteInput` and `MemoryStream`)
                    via a lightweight integer signal in the parent.
                </p>
                <div className="arch-diagram-container">
                    <MermaidDiagram chart={`
                sequenceDiagram
                    participant Input as NoteInput
                    participant App as App (Parent)
                    participant Stream as MemoryStream
                    
                    Input->>App: onNoteAdded()
                    App->>App: setRefreshTrigger(n + 1)
                    App-->>Stream: Re-render with new Trigger
                    Stream->>Stream: useEffect([trigger])
                    Stream->>API: GET /stream
                `} />
                </div>
            </div>

            <div className="arch-card">
                <h3>5.2 "Smart-Dumb" Component Separation</h3>
                <div className="info-grid">
                    <div className="info-item">
                        <span className="info-label">Smart (Container)</span>
                        <div style={{ fontSize: '0.85rem', color: '#cbd5e1', marginTop: '0.5rem' }}>
                            Examples: <code>App.tsx</code>, <code>MemoryStream.tsx</code><br />
                            Responsibility: Data Fetching, State, Side Effects.
                        </div>
                    </div>
                    <div className="info-item">
                        <span className="info-label">Dumb (Presentational)</span>
                        <div style={{ fontSize: '0.85rem', color: '#cbd5e1', marginTop: '0.5rem' }}>
                            Examples: <code>MermaidDiagram.tsx</code>, <code>ProfileCard.tsx</code> (Mostly)<br />
                            Responsibility: Rendering UI based on Props. Pure functions.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderAlgorithms = () => (
        <div className="arch-section animate-fade-in">
            <h2>6. Critical Algorithms</h2>
            <p className="arch-subtitle">Core Logic & Processes</p>

            <div className="arch-card">
                <h3>6.1 Profile Extraction Pipeline (LLM)</h3>
                <p>
                    Located in <code>app/services/profile_extractor.py</code>. This process converts unstructured natural language into structured graph nodes.
                </p>
                <div className="arch-diagram-container">
                    <MermaidDiagram chart={`
                    graph TD
                        Raw["I'm a Python dev"]"] --> Prompt[Construct System Prompt]
                        Prompt --> LLM{GPT-4o}
                        LLM -->|JSON| Output["{role: 'Python Dev'}"]
                        Output --> Cypher[MERGE (u:User ...)]
                        Cypher -->|Idempotent Write| DB[(Neo4j)]
                    `} />
                </div>

                <h4 style={{ marginTop: '1.5rem', marginBottom: '0.5rem' }}>Implementation Details</h4>
                <div className="info-grid">
                    <div className="info-item">
                        <span className="info-label">Prompt Engineering</span>
                        <p style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
                            We enforce <strong>JSON Mode</strong> in the system prompt to guarantee valid parsing.
                        </p>
                    </div>
                    <div className="info-item">
                        <span className="info-label">Idempotency</span>
                        <p style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
                            We use <code>MERGE</code> queries. Rerunning the same input does <strong>not</strong> create duplicate nodes.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderRoadmap = () => (
        <div className="arch-section animate-fade-in">
            <h2>7. Future Scalability Roadmap</h2>
            <p className="arch-subtitle">Scaling from 1 User to 1 Million</p>

            <div className="arch-card">
                <h3>7.1 Database Sharding Strategy (Target: 1TB+)</h3>
                <p>
                    When the <strong>Episodic Memory (Postgres)</strong> grows beyond 1TB, we will implement <strong>Time-Based Partitioning</strong>.
                </p>
                <div className="info-grid" style={{ marginTop: '1rem' }}>
                    <div className="info-item">
                        <span className="info-label">Partition Key</span>
                        <span className="info-value">created_at</span>
                    </div>
                    <div className="info-item">
                        <span className="info-label">Implementation</span>
                        <span className="info-value">pg_partman</span>
                    </div>
                </div>
            </div>

            <div className="arch-card">
                <h3>7.2 Asynchronous Processing</h3>
                <p>
                    Currently, <code>POST /api/memory</code> is synchronous for simplicity.
                    <strong>Phase 2</strong> introduces a true <strong>Task Queue</strong>.
                </p>
                <div className="arch-diagram-container">
                    <MermaidDiagram chart={`
                    sequenceDiagram
                        participant API
                        participant Redis
                        participant Worker
                        
                        API->>Redis: LPUSH memory_queue task
                        API-->>User: 202 Accepted
                        
                        loop Every 100ms
                            Worker->>Redis: BRPOP memory_queue
                            Worker->>Worker: Process (LLM)
                        end
                    `} />
                </div>
            </div>
            <div className="arch-card">
                <h3>7.3 Vector Store Migration</h3>
                <p>
                    If Neo4j Vector Index latency degrades (&gt;500ms) at 100M+ nodes, we will migrate vector storage to a dedicated engine
                    (Qdrant/Pinecone), keeping Neo4j strictly for the Metadata Graph.
                </p>
            </div>
        </div>
    );

    return (
        <div className="architecture-container">
            {/* Sidebar */}
            <nav className="arch-sidebar glass-card">
                <div className={`arch-nav-item ${activeTab === 'philosophy' ? 'active' : ''}`} onClick={() => setActiveTab('philosophy')}>
                    <span>🧠</span> Philosophy
                </div>
                <div className={`arch-nav-item ${activeTab === 'infrastructure' ? 'active' : ''}`} onClick={() => setActiveTab('infrastructure')}>
                    <span>🏗️</span> Infrastructure
                </div>
                <div className={`arch-nav-item ${activeTab === 'backend' ? 'active' : ''}`} onClick={() => setActiveTab('backend')}>
                    <span>⚙️</span> Backend Core
                </div>
                <div className={`arch-nav-item ${activeTab === 'data' ? 'active' : ''}`} onClick={() => setActiveTab('data')}>
                    <span>💾</span> Data Synapse
                </div>
                <div className={`arch-nav-item ${activeTab === 'frontend' ? 'active' : ''}`} onClick={() => setActiveTab('frontend')}>
                    <span>🎨</span> Interface
                </div>
                <div className={`arch-nav-item ${activeTab === 'algorithms' ? 'active' : ''}`} onClick={() => setActiveTab('algorithms')}>
                    <span>📐</span> Algorithms
                </div>
                <div className={`arch-nav-item ${activeTab === 'roadmap' ? 'active' : ''}`} onClick={() => setActiveTab('roadmap')}>
                    <span>🚀</span> Roadmap
                </div>
            </nav>

            {/* Content Content - Reuses glass styles from main app */}
            <main className="arch-content glass-card">
                {activeTab === 'philosophy' && renderPhilosophy()}
                {activeTab === 'infrastructure' && renderInfrastructure()}
                {activeTab === 'backend' && renderBackend()}
                {activeTab === 'data' && renderData()}
                {activeTab === 'frontend' && renderFrontend()}
                {activeTab === 'algorithms' && renderAlgorithms()}
                {activeTab === 'roadmap' && renderRoadmap()}
            </main>
        </div>
    );
}
