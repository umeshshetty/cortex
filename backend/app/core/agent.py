"""
Cortex - Agent Config
Defines the LangGraph State and Tools.
"""

from typing import Annotated, Literal, TypedDict
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from app.core.config import settings
from app.services.memory_service import memory_service
from app.services.vector_service import vector_service

# 1. Define Tools
@tool
async def search_memory(query: str) -> str:
    """
    Search Cortex's Long-Term Memory (Graph + Vector).
    Use this to look up past notes, entities, or knowledge.
    """
    results = await memory_service.search_graph(query)
    if not results:
        return "No relevant memories found."
    
    # Format results for the LLM
    context_str = ""
    for i, mem in enumerate(results):
        content = mem.get("thought_content", "Unknown")
        entities = mem.get("related_entities", [])
        reflections = mem.get("reflections", [])
        
        context_str += f"Result {i+1}: {content}\n"
        if entities:
            context_str += f"  - Related: {', '.join(entities)}\n"
        if reflections:
            context_str += f"  - Auto-Reflections (Clarifying Questions): {', '.join(reflections)}\n"
        context_str += "\n"
    
    return context_str

@tool
async def summarize_project(project_name: str) -> str:
    """
    Summarize all thoughts and entities related to a specific Project.
    Useful when the user asks for a status report on "Project X".
    """
    from app.services.graph_service import graph_service
    
    cypher = """
    MATCH (e:Entity)<-[:MENTIONS]-(t:Thought)
    WHERE toLower(e.name) CONTAINS toLower($project)
    RETURN t.content AS note, t.timestamp AS time
    ORDER BY t.timestamp DESC
    LIMIT 20
    """
    results = await graph_service.execute_query(cypher, {"project": project_name})
    
    if not results:
        return f"No notes found for project '{project_name}'."
        
    summary = f"Summary for Project '{project_name}':\n"
    for r in results:
        summary += f"- {r['time']}: {r['note']}\n"
    
    return summary

@tool
async def daily_log() -> str:
    """
    Retrieve all thoughts created Today.
    Useful for generating a daily standup or snapshot.
    """
    from app.services.graph_service import graph_service
    
    cypher = """
    MATCH (t:Thought)
    WHERE date(t.timestamp) = date()
    RETURN t.content AS note, t.timestamp AS time
    ORDER BY t.timestamp DESC
    """
    results = await graph_service.execute_query(cypher)
    
    if not results:
        return "No thoughts recorded today."
        
    log = "Daily Log (Today):\n"
    for r in results:
        log += f"- {r['time']}: {r['note']}\n"
    
    return log

# 2. Define State
class AgentState(TypedDict):
    messages: Annotated[list, "The conversation history"]

# 3. Define Nodes
tools = [search_memory, summarize_project, daily_log]
llm = ChatOpenAI(model="gpt-4o", api_key=settings.OPENAI_API_KEY)
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: AgentState):
    """The Brain: Decides whether to call a tool or answer."""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """Conditional Edge: Check if the last message has tool calls."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "__end__"

# 4. Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue
)

workflow.add_edge("tools", "agent")

cortex_agent = workflow.compile()
