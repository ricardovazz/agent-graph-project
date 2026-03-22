from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Any
from operator import add
import os

# Define state
class State(TypedDict):
    messages: Annotated[list, add]


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


# Create subagents
research_agent = create_agent(
    model=get_llm(),
    tools=[],
    system_prompt="You are a research specialist. Find and summarize information."
)

writer_agent = create_agent(
    model=get_llm(),
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


# Example: Async tool that directly invokes a subagent (no dispatcher)
@tool
async def async_research(query: str) -> str:
    """Async research tool that directly calls the research subagent.

    Use this for non-blocking research queries.
    """
    result = await research_agent.ainvoke({
        "messages": [
            {"role": "user", "content": query}
        ]
    })
    return result["messages"][-1].content


def create_supervisor_agent():
    """Create supervisor agent that uses tool calling to delegate to subagents."""
    supervisor_agent = create_agent(
        model=get_llm(),
        tools=[task, async_research],
        system_prompt=(
            "You are a supervisor coordinating specialized sub-agents to complete tasks. "
            "Available sub-agents:\n"
            "- research: Research and fact-finding tasks\n"
            "- writer: Content creation and editing tasks\n\n"
            "Tools available:\n"
            "- 'task': Delegate to a sub-agent by name (research or writer)\n"
            "- 'async_research': Non-blocking research for queries\n\n"
            "Use the appropriate tool for the task. After receiving results, "
            "synthesize them into a coherent response. "
            "For simple greetings or questions that don't require specialization, respond directly."
        ),
    )
    return supervisor_agent


supervisor_agent = create_supervisor_agent()


async def supervisor(state: State) -> State:
    """Supervisor node that coordinates sub-agents."""
    response = await supervisor_agent.ainvoke({"messages": state["messages"]})
    return {"messages": [response["messages"][-1]]}

# Create graph with LangGraph
graph = StateGraph(State)
graph.add_node("supervisor", supervisor)
graph.set_entry_point("supervisor")
graph.add_edge("supervisor", END)
app = graph.compile()

if __name__ == "__main__":
    import asyncio
    from langchain_core.messages import HumanMessage
    result = asyncio.run(app.ainvoke({"messages": [HumanMessage(content="Research the history of AI")]}))
    for msg in result["messages"]:
        print(f"{msg.type}: {msg.content}")