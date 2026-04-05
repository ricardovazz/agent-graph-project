"""Agent graph with 3-Layer Skills pattern and Three-tool pattern for background jobs.

This implements the proper multi-agent skills architecture:
- Layer 1 (Capability Catalog): Supervisor knows what subagents can do
- Layer 2 (Process Skills): Same business process, different views per role
- Layer 3 (Specialist Skills): Subagents own execution expertise

Reference: SKILLS-3LAYER-PATTERN.md
"""
from langchain.agents import create_agent
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Optional, Literal
from operator import add
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import asyncio
import threading
import os
import logging
from pathlib import Path

from src.skills import SkillStore
from src.skill_tools import create_skill_tools
from src.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


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
        self._threads: dict[str, threading.Thread] = {}
    
    def create_job(self, job_id: str) -> JobResult:
        job = JobResult(job_id=job_id, status="pending")
        self._jobs[job_id] = job
        return job
    
    def get_job(self, job_id: str) -> Optional[JobResult]:
        return self._jobs.get(job_id)
    
    def register_thread(self, job_id: str, thread: threading.Thread) -> None:
        self._threads[job_id] = thread
    
    def get_thread(self, job_id: str) -> Optional[threading.Thread]:
        return self._threads.get(job_id)
    
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
# Subagents with Layer 3 (Specialist) Skills
# =============================================================================

# Each subagent has its OWN skill store with specialist skills (Layer 3)
# They also have access to Layer 2 process skills (their role-specific view)

SUBAGENT_SKILLS_DIRS = {
    "research": Path(__file__).parent.parent / "skills" / "subagents" / "research",
    "writing": Path(__file__).parent.parent / "skills" / "subagents" / "writing",
    "code-generation": Path(__file__).parent.parent / "skills" / "code-generation",
}

# Also include the specialist skills from root level
SPECIALIST_SKILLS_DIRS = {
    "research": [
        Path(__file__).parent.parent / "skills" / "research",
        Path(__file__).parent.parent / "skills" / "subagents" / "research",
    ],
    "writing": [
        Path(__file__).parent.parent / "skills" / "writing",
        Path(__file__).parent.parent / "skills" / "subagents" / "writing",
    ],
    "code-generation": [
        Path(__file__).parent.parent / "skills" / "code-generation",
    ],
}


def create_subagent_skill_store(agent_name: str) -> SkillStore:
    """Create a skill store for a specific subagent with its relevant skills."""
    # For now, use the specialist skills from root level
    # In production, you'd merge multiple directories
    skills_dir = SPECIALIST_SKILLS_DIRS.get(agent_name, [Path(__file__).parent.parent / "skills" / agent_name])
    
    # Create store with the primary skills directory
    store = SkillStore(skills_dir[0])
    store.scan()
    return store


def create_subagent(agent_name: str, system_prompt: str):
    """Create a subagent with its own specialist skills (Layer 3)."""
    skill_store = create_subagent_skill_store(agent_name)
    skill_tools = create_skill_tools(skill_store)
    
    logger.info(f"Created subagent '{agent_name}' with {len(skill_store.get_skill_names())} skills")
    
    return create_agent(
        model=get_llm(),
        tools=skill_tools,
        system_prompt=system_prompt,
    )


# Create subagents with their own specialist skills
research_agent = create_subagent(
    "research",
    "You are a research specialist. Use your research skill to find and summarize information."
)

writer_agent = create_subagent(
    "writing",
    "You are a writing specialist. Create and edit content for various purposes."
)

code_generation_agent = create_subagent(
    "code-generation",
    "You are a code generation specialist. Write, review, and debug code."
)

SUBAGENTS = {
    "research": research_agent,
    "writing": writer_agent,
    "code-generation": code_generation_agent,
}


# =============================================================================
# Three-Tool Pattern
# =============================================================================

@tool
def start_job(agent_name: str, description: str) -> str:
    """Start a background job and return a job ID.

    Args:
        agent_name: Name of the subagent to use ('research', 'writing', or 'code-generation')
        description: Detailed description of what the job should accomplish
    """
    if agent_name not in SUBAGENTS:
        return f"Unknown agent: {agent_name}. Available: {list(SUBAGENTS.keys())}"

    job_id = f"job_{uuid.uuid4().hex[:8]}"
    job_storage.create_job(job_id)
    job_storage.update_status(job_id, "running")

    def run_job():
        try:
            agent = SUBAGENTS[agent_name]
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(agent.ainvoke({
                    "messages": [{"role": "user", "content": description}]
                }))
                job_storage.update_status(
                    job_id, "completed",
                    result=result["messages"][-1].content
                )
            finally:
                loop.close()
        except Exception as e:
            job_storage.update_status(job_id, "failed", error=str(e))

    thread = threading.Thread(target=run_job, daemon=True, name=f"job_{job_id}")
    job_storage.register_thread(job_id, thread)
    thread.start()

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
    
    thread = job_storage.get_thread(job_id)
    if thread and not thread.is_alive() and job.status == "running":
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
# Skills System - 3-Layer Architecture
# =============================================================================

# Layer 1: Supervisor Capability Catalog (knows what subagents can do)
# Layer 2: Process Skills (same process, different views per role)
# Layer 3: Specialist Skills (subagent execution expertise)

SKILLS_DIR = Path(__file__).parent.parent / "skills"

# Supervisor gets Layer 1 (capabilities) + Layer 2 (orchestration processes)
SUPERVISOR_SKILLS_DIRS = [
    SKILLS_DIR / "supervisor" / "capabilities",  # Layer 1
    SKILLS_DIR / "supervisor" / "processes",     # Layer 2 (supervisor view)
]


def create_supervisor_skill_store() -> SkillStore:
    """Create skill store for supervisor with Layer 1 and Layer 2 skills.
    
    The supervisor needs:
    - Layer 1: Capability catalog (what subagents can do)
    - Layer 2: Process skills from orchestration perspective (when/how to delegate)
    """
    # For simplicity, we'll scan the entire supervisor directory
    # In production, you'd want to be more selective
    store = SkillStore(SKILLS_DIR / "supervisor")
    store.scan()
    return store


# Initialize supervisor skill store
supervisor_skill_store = create_supervisor_skill_store()
supervisor_skill_tools = create_skill_tools(supervisor_skill_store)

logger.info(f"Supervisor loaded with {len(supervisor_skill_store.get_skill_names())} skills")
logger.info(f"Supervisor skills: {supervisor_skill_store.get_skill_names()}")


# =============================================================================
# Supervisor Agent (Layer 1 + Layer 2 skills only)
# =============================================================================

# Supervisor has:
# - Job management tools (start_job, check_status, get_result)
# - Layer 1 skill tools (capability catalog)
# - Layer 2 skill tools (orchestration processes)
# Supervisor does NOT have Layer 3 (specialist) skills - those belong to subagents!

supervisor_tools = [start_job, check_status, get_result] + supervisor_skill_tools

# Build system prompt with Layer 1 capability catalog
capability_catalog = supervisor_skill_store.get_skill_catalog()

supervisor_agent = create_agent(
    model=get_llm(),
    tools=supervisor_tools,
    system_prompt=SYSTEM_PROMPT.format(
        current_time=datetime.now().isoformat(),
        skill_catalog=capability_catalog if capability_catalog else "No skills currently available."
    ),
)


async def supervisor(state: State) -> State:
    """Supervisor node that coordinates sub-agents."""
    response = await supervisor_agent.ainvoke({"messages": state["messages"]})
    return {"messages": [response["messages"][-1]]}


# =============================================================================
# Graph
# =============================================================================

graph = StateGraph(State)
graph.add_node("supervisor", supervisor)
graph.set_entry_point("supervisor")
graph.add_edge("supervisor", END)
app = graph.compile()


if __name__ == "__main__":
    import asyncio
    from langchain_core.messages import HumanMessage
    
    result = asyncio.run(app.ainvoke({
        "messages": [HumanMessage(content="Start a background job to research the history of AI")]
    }))
    for msg in result["messages"]:
        print(f"{msg.type}: {msg.content}")
