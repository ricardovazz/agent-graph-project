from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Any, Optional, Literal
from operator import add
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import asyncio
import threading
import os

# Define state
class State(TypedDict):
    messages: Annotated[list, add]


# Job status enum
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
        self._threads: dict[str, threading.Thread] = {}
    
    def create_job(self, job_id: str) -> JobResult:
        """Create a new job with pending status."""
        job = JobResult(job_id=job_id, status="pending")
        self._jobs[job_id] = job
        return job
    
    def get_job(self, job_id: str) -> Optional[JobResult]:
        """Retrieve a job by ID."""
        return self._jobs.get(job_id)
    
    def register_thread(self, job_id: str, thread: threading.Thread) -> None:
        """Register a thread for a job."""
        self._threads[job_id] = thread
    
    def get_thread(self, job_id: str) -> Optional[threading.Thread]:
        """Get the thread for a job."""
        return self._threads.get(job_id)
    
    def update_status(self, job_id: str, status: JobStatus, 
                      result: Optional[str] = None, 
                      error: Optional[str] = None) -> None:
        """Update job status and optionally set result/error."""
        job = self._jobs.get(job_id)
        if job:
            job.status = status
            if result is not None:
                job.result = result
            if error is not None:
                job.error = error
            if status in ("completed", "failed"):
                job.completed_at = datetime.now()
    
    def list_jobs(self) -> list[JobResult]:
        """List all jobs."""
        return list(self._jobs.values())


# Global job storage instance
job_storage = JobStorage()


# =============================================================================
# Three-Tool Pattern for Async Background Jobs
# =============================================================================

@tool
def start_job(agent_name: str, description: str) -> str:
    """Start a background job and return a job ID.
    
    Use this for long-running tasks that shouldn't block the conversation.
    
    Args:
        agent_name: Name of the subagent to use ('research' or 'writer')
        description: Detailed description of what the job should accomplish
    
    Returns:
        Job ID string to track the task
    """
    # Validate agent exists
    if agent_name not in SUBAGENTS:
        return f"Unknown agent: {agent_name}. Available agents: {list(SUBAGENTS.keys())}"
    
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    job_storage.create_job(job_id)
    
    # Update to running status
    job_storage.update_status(job_id, "running")
    
    # Run job in background thread
    def run_job():
        try:
            agent = SUBAGENTS[agent_name]
            # Create new event loop for the thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(agent.ainvoke({
                    "messages": [{"role": "user", "content": description}]
                }))
                job_storage.update_status(
                    job_id, 
                    "completed", 
                    result=result["messages"][-1].content
                )
            finally:
                loop.close()
        except Exception as e:
            job_storage.update_status(job_id, "failed", error=str(e))
    
    # Start background thread
    thread = threading.Thread(target=run_job, daemon=True, name=f"job_{job_id}")
    job_storage.register_thread(job_id, thread)
    thread.start()

    return f"Job started: {job_id}. Use check_status with this ID to monitor progress."


@tool
def check_status(job_id: str) -> str:
    """Check the status of a background job.
    
    Args:
        job_id: The job ID returned from start_job
    
    Returns:
        Current status: pending, running, completed, or failed
    """
    job = job_storage.get_job(job_id)
    if not job:
        return f"Job not found: {job_id}"
    
    # Check if the background thread is still alive
    thread = job_storage.get_thread(job_id)
    if thread and not thread.is_alive() and job.status == "running":
        # Thread finished but status wasn't updated - mark as failed
        job_storage.update_status(job_id, "failed", error="Thread terminated unexpectedly")
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
    
    Returns:
        The job result if completed, or current status if not
    """
    job = job_storage.get_job(job_id)
    if not job:
        return f"Job not found: {job_id}"
    
    if job.status == "pending":
        return f"Job {job_id} is still pending. Use check_status to monitor."
    elif job.status == "running":
        return f"Job {job_id} is still running. Use check_status to monitor."
    elif job.status == "failed":
        return f"Job {job_id} failed: {job.error}"
    else:
        return f"Result for {job_id}:\n{job.result}"


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
        model="qwen/qwen3.5-flash-02-23",
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
        tools=[task, async_research, start_job, check_status, get_result],
        system_prompt=(
            "You are a supervisor coordinating specialized sub-agents to complete tasks. "
            "Available sub-agents:\n"
            "- research: Research and fact-finding tasks\n"
            "- writer: Content creation and editing tasks\n\n"
            "Tools available:\n"
            "- 'task': Synchronously delegate to a sub-agent by name (research or writer)\n"
            "- 'async_research': Non-blocking research for queries\n"
            "- 'start_job': Start a long-running background job with a specific agent\n"
            "- 'check_status': Check status of a background job (pending/running/completed/failed)\n"
            "- 'get_result': Retrieve the result of a completed background job\n\n"
            "For long-running tasks, use the three-tool pattern:\n"
            "1. Call 'start_job' with the appropriate agent_name ('research' or 'writer') and description\n"
            "2. Use 'check_status' to monitor progress\n"
            "3. Use 'get_result' once the job is completed\n\n"
            "Decide which agent is best suited for each task based on the user's request. "
            "After receiving results, synthesize them into a coherent response. "
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
    
    # Example 1: Simple synchronous task using task dispatcher
    print("=" * 60)
    print("Example 1: Synchronous task using 'task' dispatcher")
    print("=" * 60)
    result = asyncio.run(app.ainvoke({"messages": [HumanMessage(content="Use the task tool to research the history of AI")]}))
    for msg in result["messages"]:
        print(f"{msg.type}: {msg.content}")
    
    # Example 2: Three-tool pattern - supervisor decides which agent to use
    print("\n" + "=" * 60)
    print("Example 2: Three-tool pattern (supervisor chooses agent)")
    print("=" * 60)
    
    # Step 1: Start a background job - supervisor decides agent
    print("\nStep 1: Starting background job (supervisor picks agent)...")
    start_result = asyncio.run(app.ainvoke({
        "messages": [HumanMessage(content="Start a background job to write a poem about nature")]
    }))
    for msg in start_result["messages"]:
        print(f"{msg.type}: {msg.content}")
        # Extract job ID from response for next steps
        if "job_" in msg.content:
            import re
            match = re.search(r"job_\w+", msg.content)
            if match:
                job_id = match.group()
    
    # Wait for job to complete
    print("\n(Waiting 3 seconds for job to complete...)")
    asyncio.run(asyncio.sleep(3))
    
    # Step 2: Check status using the job ID
    print("\nStep 2: Checking job status...")
    status_result = asyncio.run(app.ainvoke({
        "messages": [HumanMessage(content=f"Check the status of {job_id}")]
    }))
    for msg in status_result["messages"]:
        print(f"{msg.type}: {msg.content}")
    
    # Step 3: Get result
    print("\nStep 3: Getting result...")
    get_result_output = asyncio.run(app.ainvoke({
        "messages": [HumanMessage(content=f"Get the result for {job_id}")]
    }))
    for msg in get_result_output["messages"]:
        print(f"{msg.type}: {msg.content}")