from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
from operator import add

# Define state
class State(TypedDict):
    messages: Annotated[list, add]

# Create subagents
research_agent = create_agent(
    model=FakeListChatModel(responses=["Research results: Found relevant information about AI history."]),
    tools=[],
    system_prompt="You are a research specialist. Find and summarize information."
)

writer_agent = create_agent(
    model=FakeListChatModel(responses=["Written content: Here's the drafted blog post about machine learning."]),
    tools=[],
    system_prompt="You are a writing specialist. Create and edit content."
)

# Registry of available sub-agents
SUBAGENTS = {
    "research": research_agent,
    "writer": writer_agent,
}

# Single dispatch tool for subagent invocation
@tool
def task(agent_name: str, description: str) -> str:
    """Launch an ephemeral subagent for a task.

    Available agents:
    - research: Research and fact-finding
    - writer: Content creation and editing
    """
    agent = SUBAGENTS[agent_name]
    result = agent.invoke({
        "messages": [
            {"role": "user", "content": description}
        ]
    })
    return result["messages"][-1].content

# Supervisor node that coordinates sub-agents
def supervisor(state: State) -> State:
    """Supervisor that decides which subagent to call."""
    messages = state["messages"]
    last_content = messages[-1].content.lower() if messages else ""
    
    # Simple routing logic (in production, the LLM decides via tool calling)
    if "research" in last_content:
        result = task.invoke({"agent_name": "research", "description": last_content})
        return {"messages": [AIMessage(content=f"Delegated to research agent: {result}")]}
    elif "write" in last_content or "blog" in last_content:
        result = task.invoke({"agent_name": "writer", "description": last_content})
        return {"messages": [AIMessage(content=f"Delegated to writer agent: {result}")]}
    else:
        return {"messages": [AIMessage(content="Hello! How can I help you today?")]}

# Create graph with LangGraph
graph = StateGraph(State)
graph.add_node("supervisor", supervisor)
graph.set_entry_point("supervisor")
graph.add_edge("supervisor", END)
app = graph.compile()

# Example usage
if __name__ == "__main__":
    # Test with a research request
    print("=" * 50)
    print("Test 1: Research request")
    print("=" * 50)
    result = app.invoke({"messages": [HumanMessage(content="Research the history of AI")]})
    for msg in result["messages"]:
        print(f"{msg.type}: {msg.content}")

    # Test with a writing request
    print("\n" + "=" * 50)
    print("Test 2: Writing request")
    print("=" * 50)
    result2 = app.invoke({"messages": [HumanMessage(content="Write a blog post about machine learning")]})
    for msg in result2["messages"]:
        print(f"{msg.type}: {msg.content}")

    # Test with a greeting
    print("\n" + "=" * 50)
    print("Test 3: Greeting")
    print("=" * 50)
    result3 = app.invoke({"messages": [HumanMessage(content="Hello")]})
    for msg in result3["messages"]:
        print(f"{msg.type}: {msg.content}")