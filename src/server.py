"""FastAPI server with WebSocket support for real-time agent communication."""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from src.agent_graph import app, job_storage, JobResult


# =============================================================================
# Models
# =============================================================================

class MessageType(str, Enum):
    HUMAN = "human"
    AI = "ai"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    JOB_STATUS = "job_status"
    SYSTEM = "system"


class Message(BaseModel):
    id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}")
    type: MessageType
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class JobInfo(BaseModel):
    job_id: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class ChatSession(BaseModel):
    session_id: str
    messages: List[Message] = Field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    jobs: Dict[str, JobInfo] = Field(default_factory=dict)
    pending_job_starts: Dict[str, Dict[str, Any]] = Field(default_factory=dict)  # tool_call_id -> args


# =============================================================================
# Session Manager
# =============================================================================

class SessionManager:
    """Manages chat sessions and WebSocket connections."""

    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.connections: Dict[str, List[WebSocket]] = {}
        self.job_sessions: Dict[str, set[str]] = {}  # job_id -> set of session_ids

    def create_session(self) -> ChatSession:
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        session = ChatSession(session_id=session_id)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        return self.sessions.get(session_id)

    def add_connection(self, session_id: str, websocket: WebSocket):
        if session_id not in self.connections:
            self.connections[session_id] = []
        self.connections[session_id].append(websocket)

    def remove_connection(self, session_id: str, websocket: WebSocket):
        if session_id in self.connections:
            self.connections[session_id].remove(websocket)
            if not self.connections[session_id]:
                del self.connections[session_id]

    def track_job(self, job_id: str, session_id: str):
        """Track which sessions are interested in a job."""
        if job_id not in self.job_sessions:
            self.job_sessions[job_id] = set()
        self.job_sessions[job_id].add(session_id)

    async def broadcast_job_update(self, job_id: str, job: JobResult):
        """Broadcast job status update to all tracking sessions."""
        if job_id in self.job_sessions:
            for session_id in list(self.job_sessions[job_id]):
                if session_id in self.connections:
                    data = {
                        "type": "job_status",
                        "data": {
                            "job_id": job_id,
                            "status": job.status,
                            "result": job.result,
                            "error": job.error,
                            "completed_at": job.completed_at.isoformat() if job.completed_at else None
                        }
                    }
                    await self.broadcast(session_id, data)

    async def broadcast(self, session_id: str, data: dict):
        """Broadcast data to all connected clients for a session."""
        if session_id in self.connections:
            disconnected = []
            for ws in self.connections[session_id]:
                try:
                    await ws.send_json(data)
                except Exception:
                    disconnected.append(ws)
            for ws in disconnected:
                self.remove_connection(session_id, ws)


session_manager = SessionManager()


# =============================================================================
# FastAPI App
# =============================================================================

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler to set up event loop for job callbacks."""
    global _event_loop
    _event_loop = asyncio.get_running_loop()
    set_event_loop(_event_loop)
    yield

app_api = FastAPI(title="Agent Graph API", version="1.0.0", lifespan=lifespan)

app_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# REST Endpoints
# =============================================================================

@app_api.get("/api/sessions")
async def list_sessions():
    """List all active sessions."""
    return {
        "sessions": [
            {"session_id": sid, "message_count": len(s.messages)}
            for sid, s in session_manager.sessions.items()
        ]
    }


@app_api.post("/api/sessions")
async def create_session():
    """Create a new chat session."""
    session = session_manager.create_session()
    # Add welcome message
    welcome = Message(
        type=MessageType.SYSTEM,
        content="Welcome! I'm a supervisor agent that can coordinate specialized sub-agents. "
                "I can start background jobs with research or writer agents. Try asking me to "
                "research a topic or write something!"
    )
    session.messages.append(welcome)
    return {"session_id": session.session_id}


@app_api.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details including messages and jobs."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Refresh job info from storage
    for job_id in session.jobs:
        job = job_storage.get_job(job_id)
        if job:
            session.jobs[job_id] = JobInfo(
                job_id=job.job_id,
                status=job.status,
                result=job.result,
                error=job.error,
                created_at=job.created_at,
                completed_at=job.completed_at
            )

    return {
        "session_id": session.session_id,
        "messages": session.messages,
        "tool_calls": session.tool_calls,
        "jobs": list(session.jobs.values())
    }


@app_api.get("/api/jobs")
async def list_jobs():
    """List all jobs across all sessions."""
    jobs = []
    for job_id in job_storage._jobs:
        job = job_storage.get_job(job_id)
        if job:
            jobs.append({
                "job_id": job.job_id,
                "status": job.status,
                "result": job.result,
                "error": job.error,
                "created_at": job.created_at,
                "completed_at": job.completed_at
            })
    return {"jobs": jobs}


@app_api.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get specific job details."""
    job = job_storage.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.job_id,
        "status": job.status,
        "result": job.result,
        "error": job.error,
        "created_at": job.created_at,
        "completed_at": job.completed_at
    }


# =============================================================================
# WebSocket Endpoint
# =============================================================================

@app_api.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time communication."""
    await websocket.accept()

    # Get or create session
    session = session_manager.get_session(session_id)
    if not session:
        # Create session with the provided session_id from URL
        session = ChatSession(session_id=session_id)
        session_manager.sessions[session_id] = session
        # Add welcome message
        welcome = Message(
            type=MessageType.SYSTEM,
            content="Connected! I'm ready to coordinate agents. Ask me to start a research or writing task."
        )
        session.messages.append(welcome)
        await websocket.send_json({
            "type": "message",
            "data": welcome.model_dump(mode="json")
        })

    session_manager.add_connection(session_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get("type") == "user_message":
                content = message_data.get("content", "")
                await handle_user_message(websocket, session, content)

    except WebSocketDisconnect:
        session_manager.remove_connection(session_id, websocket)


async def handle_user_message(websocket: WebSocket, session: ChatSession, content: str):
    """Handle incoming user message and process through agent graph."""
    # Add user message to session
    user_msg = Message(type=MessageType.HUMAN, content=content)
    session.messages.append(user_msg)

    # Broadcast user message
    await session_manager.broadcast(session.session_id, {
        "type": "message",
        "data": user_msg.model_dump(mode="json")
    })

    # Process through agent graph with streaming
    try:
        # Send thinking indicator
        await session_manager.broadcast(session.session_id, {
            "type": "status",
            "data": {"status": "thinking", "message": "Supervisor is processing..."}
        })

        # Stream the agent graph response with messages mode to capture tool calls
        async for chunk in app.astream(
            {"messages": [HumanMessage(content=content)]},
            stream_mode=["messages", "updates"],
            version="v2",
        ):
            if chunk["type"] == "messages":
                msg, metadata = chunk["data"]
                
                # Handle tool call chunks from AIMessageChunk
                if hasattr(msg, 'tool_call_chunks') and msg.tool_call_chunks:
                    for tc in msg.tool_call_chunks:
                        tool_call_data = {
                            "id": tc.get("id", ""),
                            "name": tc.get("name", ""),
                            "args": tc.get("args", {}),
                            "timestamp": datetime.now().isoformat(),
                            "node": metadata.get("langgraph_node", ""),
                        }

                        # Broadcast tool call
                        await session_manager.broadcast(session.session_id, {
                            "type": "tool_call",
                            "data": tool_call_data
                        })

                        # Store tool call
                        session.tool_calls.append(tool_call_data)

                # Handle regular AI messages (with content or tool_calls)
                if isinstance(msg, AIMessage) and (msg.content or (hasattr(msg, 'tool_calls') and msg.tool_calls)):
                    ai_msg = Message(
                        type=MessageType.AI,
                        content=msg.content or "",
                        metadata={
                            "tool_calls": msg.tool_calls if hasattr(msg, 'tool_calls') and msg.tool_calls else []
                        }
                    )
                    session.messages.append(ai_msg)

                    # Store and broadcast completed tool calls
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tc in msg.tool_calls:
                            tool_call_data = {
                                "id": tc.get("id", ""),
                                "name": tc.get("name", ""),
                                "args": tc.get("args", {}),
                                "timestamp": datetime.now().isoformat(),
                                "node": metadata.get("langgraph_node", ""),
                            }
                            session.tool_calls.append(tool_call_data)

                            # Broadcast tool call
                            await session_manager.broadcast(session.session_id, {
                                "type": "tool_call",
                                "data": tool_call_data
                            })

                            # Track pending job start
                            if tc.get("name") == "start_job":
                                args = tc.get("args", {})
                                session.pending_job_starts[tc.get("id", "")] = {
                                    "agent_name": args.get("agent_name", "unknown"),
                                    "description": args.get("description", ""),
                                }

                    await session_manager.broadcast(session.session_id, {
                        "type": "message",
                        "data": ai_msg.model_dump(mode="json")
                    })

            elif chunk["type"] == "updates":
                # Handle state updates (can be used for debugging/progress)
                for node_name, update in chunk["data"].items():
                    if update.get("messages"):
                        for msg in update["messages"]:
                            if isinstance(msg, ToolMessage):
                                tool_msg = Message(
                                    type=MessageType.TOOL_RESULT,
                                    content=msg.content or "",
                                    metadata={"tool_call_id": msg.tool_call_id if hasattr(msg, 'tool_call_id') else ""}
                                )
                                session.messages.append(tool_msg)

                                # Check if this is a start_job response and extract job ID
                                tool_call_id = msg.tool_call_id if hasattr(msg, 'tool_call_id') else ""
                                if tool_call_id in session.pending_job_starts:
                                    # Extract job ID from tool response
                                    import re
                                    job_match = re.search(r"job_\w+", msg.content or "")
                                    if job_match:
                                        job_id = job_match.group()
                                        job = job_storage.get_job(job_id)
                                        pending_info = session.pending_job_starts.pop(tool_call_id)

                                        if job:
                                            session.jobs[job_id] = JobInfo(
                                                job_id=job.job_id,
                                                status=job.status,
                                                created_at=job.created_at
                                            )
                                            # Track this job for real-time updates
                                            session_manager.track_job(job_id, session.session_id)
                                            # Broadcast job status
                                            await session_manager.broadcast(session.session_id, {
                                                "type": "job_status",
                                                "data": {
                                                    "job_id": job_id,
                                                    "status": job.status,
                                                    "agent": pending_info.get("agent_name", "unknown"),
                                                    "description": pending_info.get("description", ""),
                                                    "created_at": job.created_at.isoformat()
                                                }
                                            })

                                await session_manager.broadcast(session.session_id, {
                                    "type": "tool_result",
                                    "data": {
                                        "content": msg.content,
                                        "tool_call_id": msg.tool_call_id if hasattr(msg, 'tool_call_id') else ""
                                    }
                                })

        # Update status
        await session_manager.broadcast(session.session_id, {
            "type": "status",
            "data": {"status": "idle", "message": "Ready"}
        })

    except Exception as e:
        error_msg = Message(
            type=MessageType.SYSTEM,
            content=f"Error: {str(e)}"
        )
        session.messages.append(error_msg)
        await session_manager.broadcast(session.session_id, {
            "type": "error",
            "data": {"message": str(e)}
        })


# =============================================================================
# Job Status Polling
# =============================================================================

@app_api.get("/api/sessions/{session_id}/jobs/stream")
async def stream_job_updates(session_id: str):
    """Stream job status updates for a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    updates = []
    for job_id in session.jobs:
        job = job_storage.get_job(job_id)
        if job:
            updates.append({
                "job_id": job.job_id,
                "status": job.status,
                "result": job.result,
                "error": job.error,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            })

    return {"updates": updates}


@app_api.get("/api/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Get status of a specific job."""
    job = job_storage.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "result": job.result,
        "error": job.error,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }


# =============================================================================
# Job Status Callback
# =============================================================================

# Store the event loop when the server starts
_event_loop = None

def set_event_loop(loop):
    """Store the event loop for job callbacks."""
    global _event_loop
    _event_loop = loop

def on_job_status_change(job_id: str, job: JobResult):
    """Callback to broadcast job status changes to connected clients."""
    if _event_loop:
        try:
            asyncio.run_coroutine_threadsafe(
                session_manager.broadcast_job_update(job_id, job),
                _event_loop
            )
        except Exception:
            pass

# Register the callback
job_storage.add_callback(on_job_status_change)


# =============================================================================
# Main Entry Point
# =============================================================================

def main():
    """Main entry point for the server."""
    import uvicorn
    uvicorn.run(app_api, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
