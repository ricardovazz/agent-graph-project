"""Agent graph with Three-tool pattern for background jobs."""
from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from typing import Annotated, Optional, Literal
from typing_extensions import TypedDict
from operator import add
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import asyncio
import threading
import os
from langsmith.utils import ContextThreadPoolExecutor
from langchain_core.tracers.langchain import LangChainTracer
from langsmith import Client


# =============================================================================
# State
# =============================================================================

class State(TypedDict):
    messages: Annotated[list, add]


# =============================================================================
# Job Storage
# =============================================================================

JobStatus = Literal["pending", "running", "completed", "failed"]


@dataclass
class JobResult:
    """Stores the result of a background job."""
    job_id: str
    status: JobStatus
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


class JobStorage:
    """In-memory storage for tracking background jobs."""

    def __init__(self):
        self._jobs: dict[str, JobResult] = {}
        self._futures: dict[str, any] = {}
        self._executor: ContextThreadPoolExecutor = ContextThreadPoolExecutor(max_workers=10)

    def create_job(self, job_id: str) -> JobResult:
        job = JobResult(job_id=job_id, status="pending")
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> Optional[JobResult]:
        return self._jobs.get(job_id)

    def register_future(self, job_id: str, future: any) -> None:
        self._futures[job_id] = future

    def get_future(self, job_id: str) -> Optional[any]:
        return self._futures.get(job_id)

    def update_status(self, job_id: str, status: JobStatus,
                      result: Optional[str] = None,
                      error: Optional[str] = None) -> None:
        job = self._jobs.get(job_id)
        if job:
            job.status = status
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
            if status in ("completed", "failed"):
                job.completed_at = datetime.now()


job_storage = JobStorage()


# =============================================================================
# LangSmith Tracing Setup
# =============================================================================

# Initialize LangSmith tracer
_langsmith_client = Client() if os.environ.get("LANGSMITH_API_KEY") else None
_langchain_tracer = LangChainTracer(client=_langsmith_client) if _langsmith_client else None


def _get_callbacks():
    """Get callbacks for tracing if LangSmith is configured."""
    return [_langchain_tracer] if _langchain_tracer else []


# =============================================================================
# LLM Setup
# =============================================================================

def get_llm():
    """Get LLM for production using OpenRouter."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is required")
    from langchain_openai import ChatOpenAI
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


# =============================================================================
# Subagents
# =============================================================================

def _create_agent_with_tracing(system_prompt: str):
    """Create an agent with LangSmith tracing support."""
    agent = create_agent(
        model=get_llm(),
        tools=[],
        system_prompt=system_prompt
    )
    return agent


research_agent = _create_agent_with_tracing(
    "You are a research specialist. Find and summarize information."
)

writer_agent = _create_agent_with_tracing(
    "You are a writing specialist. Create and edit content."
)

SUBAGENTS = {
    "research": research_agent,
    "writer": writer_agent,
}


# =============================================================================
# Three-Tool Pattern
# =============================================================================

@tool
def start_job(agent_name: str, description: str) -> str:
    """Start a background job and return a job ID.

    Args:
        agent_name: Name of the subagent to use ('research' or 'writer')
        description: Detailed description of what the job should accomplish
    """
    if agent_name not in SUBAGENTS:
        return f"Unknown agent: {agent_name}. Available: {list(SUBAGENTS.keys())}"

    job_id = f"job_{uuid.uuid4().hex[:8]}"
    job_storage.create_job(job_id)
    job_storage.update_status(job_id, "running")

    # Capture callbacks for LangSmith tracing
    callbacks = _get_callbacks()

    def run_job():
        try:
            agent = SUBAGENTS[agent_name]
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Pass callbacks to sub-agent for proper tracing
                result = loop.run_until_complete(agent.ainvoke(
                    {"messages": [{"role": "user", "content": description}]},
                    config={"callbacks": callbacks} if callbacks else {}
                ))
                job_storage.update_status(
                    job_id, "completed",
                    result=result["messages"][-1].content
                )
            finally:
                loop.close()
        except Exception as e:
            job_storage.update_status(job_id, "failed", error=str(e))

    # Submit to ContextThreadPoolExecutor for proper LangSmith context propagation
    future = job_storage._executor.submit(run_job)
    job_storage.register_future(job_id, future)

    return f"Job started: {job_id}. Use check_status to monitor progress."


@tool
def check_status(job_id: str) -> str:
    """Check the status of a background job.

    Args:
        job_id: The job ID returned from start_job
    """
    job = job_storage.get_job(job_id)
    if not job:
        return f"Job not found: {job_id}"

    future = job_storage.get_future(job_id)
    if future and future.done() and job.status == "running":
        if future.exception():
            job_storage.update_status(job_id, "failed", error=str(future.exception()))
        else:
            job_storage.update_status(job_id, "completed", result="Result available")
        job = job_storage.get_job(job_id)

    status_info = f"Job {job_id}: {job.status}"
    if job.status == "completed":
        status_info += f" (finished at {job.completed_at})"
    elif job.status == "failed":
        status_info += f" - Error: {job.error}"

    return status_info


@tool
def get_result(job_id: str) -> str:
    """Get the result of a completed background job.
    
    Args:
        job_id: The job ID returned from start_job
    """
    job = job_storage.get_job(job_id)
    if not job:
        return f"Job not found: {job_id}"
    
    if job.status == "pending":
        return f"Job {job_id} is still pending."
    elif job.status == "running":
        return f"Job {job_id} is still running."
    elif job.status == "failed":
        return f"Job {job_id} failed: {job.error}"
    else:
        return f"Result for {job_id}:\n{job.result}"


# =============================================================================
# Supervisor Agent
# =============================================================================

supervisor_agent = create_agent(
    model=get_llm(),
    tools=[start_job, check_status, get_result],
    system_prompt=(
        "You are a supervisor coordinating specialized sub-agents via background jobs.\n\n"
        "Available sub-agents:\n"
        "- research: Research and fact-finding tasks\n"
        "- writer: Content creation and editing tasks\n\n"
        "Tools (Three-tool pattern):\n"
        "1. start_job(agent_name, description) - Start a background job, returns job ID\n"
        "2. check_status(job_id) - Returns status: pending/running/completed/failed\n"
        "3. get_result(job_id) - Retrieves the completed result\n\n"
        "Workflow:\n"
        "1. User requests a task → Call start_job with appropriate agent\n"
        "2. User asks for status → Call check_status\n"
        "3. User wants result → Call get_result (after job is completed)\n\n"
        "For simple greetings or questions, respond directly without using tools."
    ),
)


async def supervisor(state: State) -> State:
    """Supervisor node that coordinates sub-agents."""
    callbacks = _get_callbacks()
    config = {"callbacks": callbacks} if callbacks else {}
    response = await supervisor_agent.ainvoke({"messages": state["messages"]}, config=config)
    return {"messages": [response["messages"][-1]]}


# =============================================================================
# Graph
# =============================================================================

graph = StateGraph(State)
graph.add_node("supervisor", supervisor)
graph.set_entry_point("supervisor")
graph.add_edge("supervisor", END)
app = graph.compile()


# =============================================================================
# Thread Management (LangSmith)
# =============================================================================

def get_thread_config(thread_id: Optional[str] = None) -> dict:
    """
    Get config dict with thread_id for LangSmith tracing.
    
    Args:
        thread_id: Optional thread ID for grouping related runs in LangSmith.
                   If not provided, each run is independent.
    
    Returns:
        Config dict to pass to ainvoke/invoke for thread-aware tracing.
    
    Example:
        config = get_thread_config("my-thread-id")
        result = await app.ainvoke({"messages": [...]}, config=config)
    """
    config = {}
    
    # Add callbacks if LangSmith is configured
    callbacks = _get_callbacks()
    if callbacks:
        config["callbacks"] = callbacks
    
    # Add thread_id for grouping related runs
    if thread_id:
        config["configurable"] = {"thread_id": thread_id}
    
    return config


def create_thread_id() -> str:
    """Generate a unique thread ID for grouping related runs."""
    return f"thread_{uuid.uuid4().hex[:12]}"


if __name__ == "__main__":
    import asyncio
    from langchain_core.messages import HumanMessage
    
    result = asyncio.run(app.ainvoke({
        "messages": [HumanMessage(content="Start a background job to research the history of AI")]
    }))
    for msg in result["messages"]:
        print(f"{msg.type}: {msg.content}")
