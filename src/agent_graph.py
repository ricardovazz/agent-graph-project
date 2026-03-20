from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Any
from operator import add
import os

# Define state
class State(TypedDict):
    messages: Annotated[list, add]


# Single dispatch tool for subagent invocation
@tool
def task(agent_name: str, description: str) -> str:
    """Launch an ephemeral subagent for a task.

    Available agents:
    - research: Research and fact-finding
    - writer: Content creation and editing
    """
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        model="qwen/qwen3.5-9b",
        temperature=0,
        default_headers={
            "HTTP-Referer": "https://agent-graph-project.local",
            "X-OpenRouter-Title": "Agent Graph Project",
        }
    )
    agent = create_agent(
        model=llm,
        tools=[],
        system_prompt=f"You are a {agent_name} specialist. {('Research and find relevant information.' if agent_name == 'research' else 'Create and edit content.')}"
    )
    result = agent.invoke({
        "messages": [
            {"role": "user", "content": description}
        ]
    })
    return result["messages"][-1].content


# Production: Use OpenRouter API with tool calling support
def get_llm():
    """Get LLM for production using OpenRouter."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is required")
    from langchain_openai import ChatOpenAI
    # OpenRouter uses OpenAI-compatible API
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
        model="qwen/qwen3.5-9b",
        temperature=0,
        default_headers={
            "HTTP-Referer": "https://agent-graph-project.local",
            "X-OpenRouter-Title": "Agent Graph Project",
        }
    )


def create_supervisor_agent():
    """Create supervisor agent that uses tool calling to delegate to subagents."""
    llm = get_llm()
    supervisor_agent = create_agent(
        model=llm,
        tools=[task],
        system_prompt=(
            "You are a supervisor coordinating specialized sub-agents to complete tasks. "
            "Available sub-agents:\n"
            "- research: Research and fact-finding tasks\n"
            "- writer: Content creation and editing tasks\n\n"
            "Use the 'task' tool to delegate work to the appropriate sub-agent. "
            "Always provide the agent_name and a clear description of what needs to be done. "
            "After receiving results from sub-agents, synthesize them into a coherent response. "
            "For simple greetings or questions that don't require specialization, respond directly."
        ),
    )
    return supervisor_agent


supervisor_agent = create_supervisor_agent()


def supervisor(state: State) -> State:
    """Supervisor node that coordinates sub-agents."""
    response = supervisor_agent.invoke({"messages": state["messages"]})
    return {"messages": [response["messages"][-1]]}

# Create graph with LangGraph
graph = StateGraph(State)
graph.add_node("supervisor", supervisor)
graph.set_entry_point("supervisor")
graph.add_edge("supervisor", END)
app = graph.compile()