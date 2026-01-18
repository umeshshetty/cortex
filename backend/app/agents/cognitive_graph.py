"""
Cortex - LangGraph Agent Orchestration
The "Frontal Lobe" - Cognitive pipeline using LangGraph StateGraph.

Implements the Sense-Think-Act loop from the specification:
1. SENSE: Ingestion, Sanitization, Classification
2. THINK: Context Assembly, Reasoning, Reflection
3. ACT: Execution, Consolidation
"""

from typing import TypedDict, Annotated, Literal, List, Dict, Any, Optional
from datetime import datetime
import json
import operator

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.core.config import settings
from app.core.llm_tier import llm_router, LLMTier
from app.core.pii_sanitizer import sanitize_for_cloud, deanonymize_response
from app.core.prompts import (
    ROUTER_SYSTEM_PROMPT, 
    ANALYST_EXTRACTION_PROMPT,
    ANALYST_RESPONSE_PROMPT,
    SIMPLE_RESPONSE_PROMPT,
    SOCIAL_RESPONSE_PROMPT,
    SCHEDULER_PROMPT,
    CORTEX_IDENTITY
)


# =============================================================================
# State Definition
# =============================================================================

class CortexState(TypedDict):
    """
    State that flows through the cognitive graph.
    
    Following the biological model:
    - input: Raw sensory input (user message)
    - sanitized_input: PII-scrubbed version
    - pii_mapping: Token -> original PII mapping
    - intent: Classified intent (THOUGHT, QUESTION, SCHEDULE, SOCIAL)
    - urgency: 1-10 urgency rating
    - entities: Extracted entities
    - context: Retrieved context from memory
    - reasoning: Agent's internal reasoning
    - response: Final response to user
    - needs_clarification: Whether to ask user for more info
    - clarification_request: The question to ask user
    - actions: List of actions to execute
    - thought_id: ID of saved thought (if any)
    """
    # Input
    input: str
    sanitized_input: str
    pii_mapping: Dict[str, str]
    
    # Classification
    intent: str
    urgency: int
    privacy_level: str
    entities: List[Dict]
    
    # Memory
    context: List[Dict]
    profile: Dict[str, Any]
    
    # Reasoning
    reasoning: str
    extraction: Dict
    
    # Output
    response: str
    needs_clarification: bool
    clarification_request: str
    actions: List[Dict]
    thought_id: str
    
    # Metadata
    route_path: List[str]  # Track which nodes were visited
    error: Optional[str]


# =============================================================================
# Node Functions (The "Neurons")
# =============================================================================

async def sanitize_input(state: CortexState) -> CortexState:
    """
    Node 1: SENSE - Sanitize PII before processing.
    The Privacy Airlock - protects sensitive data.
    """
    user_input = state["input"]
    sanitized, pii_mapping = sanitize_for_cloud(user_input)
    
    return {
        **state,
        "sanitized_input": sanitized,
        "pii_mapping": pii_mapping,
        "route_path": state.get("route_path", []) + ["sanitize"]
    }


async def classify_intent(state: CortexState) -> CortexState:
    """
    Node 2: SENSE - Classify intent using fast local LLM.
    The Router/Gateway - determines cognitive pathway.
    """
    user_input = state["sanitized_input"]
    
    # Use the tiered router for classification
    classification = await llm_router.classify_intent(user_input)
    
    return {
        **state,
        "intent": classification.get("intent", "QUERY"),
        "urgency": classification.get("urgency", 5),
        "privacy_level": classification.get("privacy_level", "public"),
        "entities": classification.get("entities", {}),
        "route_path": state.get("route_path", []) + ["classify"]
    }


async def retrieve_context(state: CortexState) -> CortexState:
    """
    Node 3: THINK - Retrieve relevant context from memory.
    The Hippocampus - retrieves relevant memories.
    """
    from app.services.vector_service import search_similar
    from app.services.graph_service import get_related_context, get_user_profile
    
    user_input = state["sanitized_input"]
    entities = state.get("entities", {})
    
    # Vector search for semantic similarity
    vector_results = await search_similar(user_input, limit=5)
    
    # Graph search for entity relationships
    graph_context = []
    for entity_type, entity_list in entities.items():
        if isinstance(entity_list, list):
            for entity_name in entity_list:
                ctx = await get_related_context(entity_name)
                if ctx:
                    graph_context.append({"entity": entity_name, "context": ctx})
    
    # Load User Profile (Context about the user via hardcoded ID for now)
    # In a real app, user_id would come from state/auth
    user_profile = await get_user_profile("user_123")
    
    return {
        **state,
        "context": vector_results + graph_context,
        "profile": user_profile or {},
        "route_path": state.get("route_path", []) + ["retrieve_context"]
    }


async def analyst_node(state: CortexState) -> CortexState:
    """
    Node 4a: THINK - Process thoughts and extract knowledge.
    The Analyst Agent - handles THOUGHT and QUESTION intents.
    """
    from app.services.graph_service import save_thought
    from app.services.vector_service import add_embedding
    
    user_input = state["sanitized_input"]
    context = state.get("context", [])
    intent = state.get("intent", "THOUGHT")
    
    # Select appropriate tier based on privacy
    tier = LLMTier.PRIVATE if state.get("privacy_level") == "private" else LLMTier.LOGIC
    
    # Extract structured knowledge
    extraction_response = await llm_router.invoke(
        tier=tier,
        prompt=f"Thought: {user_input}\n\nExtraction (JSON):",
        system_prompt=ANALYST_EXTRACTION_PROMPT,
        sanitize_pii=False  # Already sanitized
    )
    
    # Parse extraction
    try:
        start = extraction_response.find('{')
        end = extraction_response.rfind('}') + 1
        extraction = json.loads(extraction_response[start:end]) if start != -1 else {}
    except json.JSONDecodeError:
        extraction = {"summary": user_input[:100], "entities": [], "categories": ["Archive"]}
    
    # Check if we need clarification
    needs_clarification = False
    clarification_request = ""
    
    if extraction.get("ambiguous"):
        needs_clarification = True
        clarification_request = extraction.get("clarification_question", "Could you provide more details?")
    
    # Save to graph if it's a thought (not a question)
    thought_id = ""
    if intent == "THOUGHT" and not needs_clarification:
        thought_id = await save_thought(
            content=user_input,
            summary=extraction.get("summary", ""),
            entities=extraction.get("entities", []),
            categories=extraction.get("categories", []),
            action_items=extraction.get("action_items", [])
        )
        # Add embedding
        await add_embedding(thought_id, user_input)
    
    # Generate response
    context_str = "\n".join([str(c) for c in context[:3]]) if context else "No prior context."
    
    # Format profile context
    profile = state.get("profile", {})
    profile_str = ""
    if profile:
        profile_str = f"""
User Profile:
- Name: {profile.get('name')}
- Goals: {[g.get('title') for g in profile.get('goals', [])]}
- Chronotype: {profile.get('chronotype')}
"""
    
    response = await llm_router.invoke(
        tier=LLMTier.EMPATHY if intent == "QUESTION" else tier,
        prompt=f"""User input: {user_input}

Extracted info:
- Summary: {extraction.get('summary', 'N/A')}
- Entities: {extraction.get('entities', [])}
- Categories: {extraction.get('categories', [])}

Related context: {context_str}
{profile_str}

{"Answer the user's question based on context/profile." if intent == "QUESTION" else "Acknowledge what you learned and note any connections."}""",
        system_prompt=ANALYST_RESPONSE_PROMPT
    )
    
    # De-anonymize response
    pii_mapping = state.get("pii_mapping", {})
    if pii_mapping:
        response = deanonymize_response(response, pii_mapping)
    
    return {
        **state,
        "extraction": extraction,
        "response": response,
        "thought_id": thought_id,
        "needs_clarification": needs_clarification,
        "clarification_request": clarification_request,
        "route_path": state.get("route_path", []) + ["analyst"]
    }


async def scheduler_node(state: CortexState) -> CortexState:
    """
    Node 4b: THINK - Handle scheduling and calendar tasks.
    The Scheduler Agent - handles SCHEDULE intent.
    """
    from datetime import datetime
    
    user_input = state["sanitized_input"]
    entities = state.get("entities", {})
    
    # Get current time for context
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Determine what's missing
    has_time = bool(entities.get('times', []))
    has_people = bool(entities.get('persons', []))
    
    system_prompt = """You help schedule meetings. MAX 10 WORDS.

When info is missing, ask ONE short question. Examples:
- "Sure, when and with who?"
- "Got it. What time?"
- "Meeting at 5pm - who's joining?"
- "With Sarah at 3pm. I'll add it."

NEVER say things like:
- "When scheduling a meeting, would you like..."
- "Based on the provided information..."
- "To confirm..."

Just be direct. Like texting a friend."""
    
    # Use Logic tier (falls back to local if no API key)
    
    # Format profile context
    profile = state.get("profile", {})
    profile_context = ""
    if profile:
        # Extract anti-goals
        anti_goals = [g.get('description') for g in profile.get('strategic', {}).get('anti_goals', [])]
        
        profile_context = f"""
User Constraints:
- Work Hours: {profile.get('biological', {}).get('work_start', '09:00')} - {profile.get('biological', {}).get('work_end', '17:00')}
- Chronotype: {profile.get('biological', {}).get('chronotype', 'N/A')}
- Rules: {"; ".join(anti_goals)}
"""

    response = await llm_router.invoke(
        tier=LLMTier.LOGIC,
        prompt=f"""User: {user_input}

Time mentioned: {entities.get('times', ['none'])}
People mentioned: {entities.get('persons', ['none'])}
Current time: {current_time}
{profile_context}

Respond briefly. If something's missing, just ask for it.""",
        system_prompt=system_prompt
    )
    
    # Check if clarification needed
    needs_clarification = "?" in response
    
    pii_mapping = state.get("pii_mapping", {})
    if pii_mapping:
        response = deanonymize_response(response, pii_mapping)
    
    return {
        **state,
        "response": response,
        "needs_clarification": needs_clarification,
        "clarification_request": response if needs_clarification else "",
        "route_path": state.get("route_path", []) + ["scheduler"]
    }


async def social_node(state: CortexState) -> CortexState:
    """
    Node 4c: THINK - Handle social and relationship queries.
    The Social Agent - handles SOCIAL intent.
    """
    user_input = state["sanitized_input"]
    entities = state.get("entities", {})
    context = state.get("context", [])
    
    # Use Empathy tier for social (needs emotional intelligence) but be BRIEF
    response = await llm_router.invoke(
        tier=LLMTier.EMPATHY,
        prompt=f"""User said: {user_input}

People: {entities.get('persons', [])}
Context: {context[:2] if context else 'None'}

Respond briefly (2-3 sentences max). Be helpful, not philosophical.""",
        system_prompt=SOCIAL_RESPONSE_PROMPT
    )
    
    pii_mapping = state.get("pii_mapping", {})
    if pii_mapping:
        response = deanonymize_response(response, pii_mapping)
    
    return {
        **state,
        "response": response,
        "route_path": state.get("route_path", []) + ["social"]
    }


async def simple_response_node(state: CortexState) -> CortexState:
    """
    Node 4d: Fast path for simple greetings/queries.
    Uses REFLEX tier for speed, keeps it brief.
    """
    user_input = state["sanitized_input"]
    
    # Use local model for quick, brief response
    response = await llm_router.invoke(
        tier=LLMTier.REFLEX,
        prompt=f"User says: {user_input}\n\nRespond in 1-2 sentences max.",
        system_prompt=SIMPLE_RESPONSE_PROMPT
    )
    
    return {
        **state,
        "response": response,
        "route_path": state.get("route_path", []) + ["simple"]
    }


async def clarification_node(state: CortexState) -> CortexState:
    """
    Node 5: Human-in-the-loop - Request clarification.
    Creates a clarification request for the user.
    """
    from app.services.briefing import create_clarification
    
    clarification_id = await create_clarification(
        clarification_type="AMBIGUITY",
        description=state.get("clarification_request", "Could you provide more details?"),
        context=state.get("input", "")
    )
    
    return {
        **state,
        "response": state.get("clarification_request", "I need a bit more information. Could you clarify?"),
        "route_path": state.get("route_path", []) + ["clarification"]
    }


async def consolidate_node(state: CortexState) -> CortexState:
    """
    Node 6: ACT - Consolidate memory and execute actions.
    The final step - updates memory and returns response.
    """
    # Log the interaction for future consolidation
    # (The actual consolidation happens in background workers)
    
    return {
        **state,
        "route_path": state.get("route_path", []) + ["consolidate"]
    }


# =============================================================================
# Routing Functions (Conditional Edges)
# =============================================================================

def route_by_intent(state: CortexState) -> str:
    """Route to appropriate agent based on classified intent."""
    intent = state.get("intent", "THOUGHT")
    
    if intent == "SIMPLE":
        return "simple"
    elif intent == "SCHEDULE" or intent == "SCHEDULING":
        return "scheduler"
    elif intent == "SOCIAL":
        return "social"
    else:  # THOUGHT, QUESTION, QUERY, JOURNAL
        return "analyst"


def route_after_agent(state: CortexState) -> str:
    """Route after agent processing - check if clarification needed."""
    if state.get("needs_clarification"):
        return "clarify"
    return "consolidate"


# =============================================================================
# Graph Construction
# =============================================================================

def create_cortex_graph() -> StateGraph:
    """
    Create the Cortex cognitive graph.
    
    Flow:
    input -> sanitize -> classify -> [analyst|scheduler|social|simple]
                                            |
                                      [clarify or consolidate]
                                            |
                                           END
    """
    # Create the graph
    graph = StateGraph(CortexState)
    
    # Add nodes (neurons)
    graph.add_node("sanitize", sanitize_input)
    graph.add_node("classify", classify_intent)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("analyst", analyst_node)
    graph.add_node("scheduler", scheduler_node)
    graph.add_node("social", social_node)
    graph.add_node("simple", simple_response_node)
    graph.add_node("clarify", clarification_node)
    graph.add_node("consolidate", consolidate_node)
    
    # Define edges (synapses)
    
    # Entry point
    graph.set_entry_point("sanitize")
    
    # Sanitize -> Classify
    graph.add_edge("sanitize", "classify")
    
    # Classify -> Retrieve Context (for all except simple)
    graph.add_conditional_edges(
        "classify",
        lambda s: "simple" if s.get("intent") == "SIMPLE" else "retrieve_context",
        {
            "simple": "simple",
            "retrieve_context": "retrieve_context"
        }
    )
    
    # Retrieve Context -> Route by Intent
    graph.add_conditional_edges(
        "retrieve_context",
        route_by_intent,
        {
            "analyst": "analyst",
            "scheduler": "scheduler",
            "social": "social",
            "simple": "simple"
        }
    )
    
    # Agent nodes -> Check for clarification
    graph.add_conditional_edges("analyst", route_after_agent, {
        "clarify": "clarify",
        "consolidate": "consolidate"
    })
    graph.add_conditional_edges("scheduler", route_after_agent, {
        "clarify": "clarify",
        "consolidate": "consolidate"
    })
    graph.add_edge("social", "consolidate")
    graph.add_edge("simple", "consolidate")
    
    # Clarify -> END (user needs to respond)
    graph.add_edge("clarify", END)
    
    # Consolidate -> END
    graph.add_edge("consolidate", END)
    
    return graph


# =============================================================================
# Graph Instance & Runner
# =============================================================================

# Create memory saver for conversation persistence
memory = MemorySaver()

# Compile the graph
cortex_graph = create_cortex_graph().compile(checkpointer=memory)


async def run_cortex(
    user_input: str,
    thread_id: str = "default"
) -> Dict[str, Any]:
    """
    Run the Cortex cognitive pipeline.
    
    Args:
        user_input: The user's message
        thread_id: Conversation thread ID for persistence
        
    Returns:
        Final state with response
    """
    # Initialize state
    initial_state: CortexState = {
        "input": user_input,
        "sanitized_input": "",
        "pii_mapping": {},
        "intent": "",
        "urgency": 5,
        "privacy_level": "public",
        "entities": [],
        "context": [],
        "user_profile": None,
        "reasoning": "",
        "extraction": {},
        "response": "",
        "needs_clarification": False,
        "clarification_request": "",
        "actions": [],
        "thought_id": "",
        "route_path": [],
        "error": None
    }
    
    # Run the graph
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        final_state = await cortex_graph.ainvoke(initial_state, config)
        return final_state
    except Exception as e:
        return {
            **initial_state,
            "response": f"I encountered an error: {str(e)}",
            "error": str(e)
        }
