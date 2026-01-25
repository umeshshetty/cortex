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
        context_str += f"Result {i+1}: {content} (Related: {', '.join(entities)})\n"
    
    return context_str

# 2. Define State
class AgentState(TypedDict):
    messages: Annotated[list, "The conversation history"]

# 3. Define Nodes
tools = [search_memory]
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
