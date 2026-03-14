from langgraph.graph import StateGraph, END
from langchain.agents import create_agent
from langchain_core.language_models.fake import FakeListLLM
from langchain_core.tools import tool
from langchain_core.prompts import SystemMessagePromptTemplate
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from operator import add

# Define state
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add]

# Mock LLM for demo (replace with real model like OpenAI)
llm = FakeListLLM(responses=["delegate", "handle"])

# Define a simple tool
@tool
def example_tool(query: str) -> str:
    """A simple example tool that echoes the query."""
    return f"Echo: {query}"

# System prompts
orchestrator_prompt = (
    "You are the orchestrator agent. Your job is to decide if the task should be handled by the worker agent. "
    "If the user message contains 'task', respond with 'delegate'. Otherwise, respond with 'handle'."
)

worker_prompt = (
    "You are the worker agent. You have access to tools. "
    "Use them to complete tasks efficiently. Always provide helpful responses."
)

# Create the orchestrator agent
orchestrator_agent = create_agent(
    model=llm,
    tools=[],  # No tools for orchestrator, it just decides
    system_prompt=orchestrator_prompt
)

# Create the worker agent
worker_agent = create_agent(
    model=FakeListLLM(responses=["I am the worker agent. Task completed using tools."]),
    tools=[],  # No tools for demo
    system_prompt=worker_prompt
)
def orchestrator(state: State):
    # Call the orchestrator agent
    response = orchestrator_agent.invoke({"messages": state["messages"]})
    last_response = response["messages"][-1].content.lower()
    if "delegate" in last_response:
        return {"messages": [AIMessage(content="Delegating to worker agent.")]}
    else:
        return {"messages": [AIMessage(content="I can handle this directly as orchestrator.")]}  # This won't be reached in routing, but for completeness

# Worker function
def worker(state: State):
    # Call the agent
    response = worker_agent.invoke({"messages": state["messages"]})
    return {"messages": [AIMessage(content=response["messages"][-1].content)]}

# Create graph
graph = StateGraph(State)

# Add nodes
graph.add_node("orchestrator", orchestrator)
graph.add_node("worker", worker)

# Add edges
graph.add_conditional_edges(
    "orchestrator",
    lambda state: "worker" if "task" in state["messages"][0].content.lower() else END
)
graph.add_edge("worker", END)

# Set entry
graph.set_entry_point("orchestrator")

# Compile
app = graph.compile()

# Example usage
if __name__ == "__main__":
    # Test with a task
    result = app.invoke({"messages": [HumanMessage(content="Handle this task")]})
    print("Final messages:")
    for msg in result["messages"]:
        print(f"{msg.type}: {msg.content}")

    # Test without task
    result2 = app.invoke({"messages": [HumanMessage(content="Hello")]})
    print("\nFinal messages:")
    for msg in result2["messages"]:
        print(f"{msg.type}: {msg.content}")