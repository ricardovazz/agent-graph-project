"""Simple web UI for the Three-tool pattern agent."""
import asyncio
import re
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from langchain_core.messages import HumanMessage
from src.agent_graph import app, job_storage

# =============================================================================
# FastAPI App
# =============================================================================

app_fastapi = FastAPI(title="Agent Graph UI")


# =============================================================================
# Models
# =============================================================================

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    job_id: Optional[str] = None
    notification: Optional[dict] = None


class JobStatus(BaseModel):
    job_id: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class Notification(BaseModel):
    id: str
    job_id: str
    message: str
    type: str  # "success" or "error"
    timestamp: str
    read: bool = False


# =============================================================================
# State
# =============================================================================

# Store chat history per session
chat_sessions: dict[str, List[ChatMessage]] = {}
# Store notifications per session
notifications: dict[str, List[Notification]] = {}
# Store active jobs per session
active_jobs: dict[str, set] = {}


# =============================================================================
# Background Job Monitor
# =============================================================================

async def monitor_jobs():
    """Background task to monitor job completion and create notifications."""
    while True:
        await asyncio.sleep(2)  # Check every 2 seconds
        
        for session_id, job_ids in list(active_jobs.items()):
            for job_id in list(job_ids):
                job = job_storage.get_job(job_id)
                if job and job.status in ("completed", "failed"):
                    # Create notification
                    if session_id not in notifications:
                        notifications[session_id] = []
                    
                    if job.status == "completed":
                        notif = Notification(
                            id=f"notif_{uuid.uuid4().hex[:8]}",
                            job_id=job_id,
                            message=f"Job {job_id} completed! Click to view results.",
                            type="success",
                            timestamp=datetime.now().isoformat()
                        )
                    else:
                        notif = Notification(
                            id=f"notif_{uuid.uuid4().hex[:8]}",
                            job_id=job_id,
                            message=f"Job {job_id} failed: {job.error}",
                            type="error",
                            timestamp=datetime.now().isoformat()
                        )
                    
                    notifications[session_id].append(notif)
                    job_ids.discard(job_id)  # Remove from active jobs


# =============================================================================
# API Endpoints
# =============================================================================

@app_fastapi.get("/", response_class=HTMLResponse)
async def get_ui():
    """Serve the main UI."""
    return HTMLResponse(content=HTML_TEMPLATE)


@app_fastapi.post("/api/chat")
async def chat(request: ChatRequest):
    """Process a chat message and return response."""
    session_id = "default"  # Single session for simplicity
    
    # Initialize session if needed
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []
    if session_id not in active_jobs:
        active_jobs[session_id] = set()
    
    # Add user message to history
    chat_sessions[session_id].append(ChatMessage(
        role="user",
        content=request.message,
        timestamp=datetime.now().isoformat()
    ))
    
    # Process with agent
    result = await app.ainvoke({
        "messages": [HumanMessage(content=request.message)]
    })
    
    assistant_message = result["messages"][-1].content
    
    # Add assistant response to history
    chat_sessions[session_id].append(ChatMessage(
        role="assistant",
        content=assistant_message,
        timestamp=datetime.now().isoformat()
    ))
    
    # Check if a job was started
    job_id_match = re.search(r"job_\w+", assistant_message)
    job_id = job_id_match.group() if job_id_match else None
    
    if job_id:
        active_jobs[session_id].add(job_id)
    
    return ChatResponse(
        response=assistant_message,
        job_id=job_id
    )


@app_fastapi.get("/api/jobs")
async def list_jobs():
    """List all jobs."""
    jobs = job_storage.list_jobs()
    return [
        JobStatus(
            job_id=job.job_id,
            status=job.status,
            result=job.result,
            error=job.error,
            created_at=job.created_at.isoformat(),
            completed_at=job.completed_at.isoformat() if job.completed_at else None
        )
        for job in jobs
    ]


@app_fastapi.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Get a specific job's status and result."""
    job = job_storage.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(
        job_id=job.job_id,
        status=job.status,
        result=job.result,
        error=job.error,
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None
    )


@app_fastapi.get("/api/notifications")
async def get_notifications():
    """Get unread notifications."""
    session_id = "default"
    session_notifications = notifications.get(session_id, [])
    unread = [n for n in session_notifications if not n.read]
    return unread


@app_fastapi.post("/api/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str):
    """Mark a notification as read."""
    session_id = "default"
    for notif in notifications.get(session_id, []):
        if notif.id == notif_id:
            notif.read = True
            return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Notification not found")


@app_fastapi.post("/api/notifications/{notif_id}/action")
async def action_notification(notif_id: str):
    """Action a notification - returns the message to send to agent."""
    session_id = "default"
    for notif in notifications.get(session_id, []):
        if notif.id == notif_id:
            notif.read = True
            # Return the message that should be sent to the agent
            return {
                "message": f"Check job {notif.job_id} and summarize the results.",
                "job_id": notif.job_id
            }
    raise HTTPException(status_code=404, detail="Notification not found")


@app_fastapi.get("/api/history")
async def get_history():
    """Get chat history."""
    session_id = "default"
    return chat_sessions.get(session_id, [])


@app_fastapi.delete("/api/history")
async def clear_history():
    """Clear chat history."""
    session_id = "default"
    chat_sessions[session_id] = []
    return {"status": "ok"}


# =============================================================================
# Startup
# =============================================================================

@app_fastapi.on_event("startup")
async def startup_event():
    """Start background job monitor."""
    asyncio.create_task(monitor_jobs())


# =============================================================================
# HTML Template
# =============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Graph - Three-Tool Pattern</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            border-bottom: 1px solid #333;
        }
        
        h1 {
            font-size: 1.5rem;
            color: #00d9ff;
        }
        
        .notification-bell {
            position: relative;
            cursor: pointer;
            font-size: 1.5rem;
        }
        
        .notification-badge {
            position: absolute;
            top: -5px;
            right: -5px;
            background: #ff4757;
            color: white;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            font-size: 0.75rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px 0;
        }
        
        .message {
            margin-bottom: 20px;
            padding: 15px 20px;
            border-radius: 12px;
            max-width: 80%;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.user {
            background: #00d9ff;
            color: #1a1a2e;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }
        
        .message.assistant {
            background: #2d2d44;
            border-bottom-left-radius: 4px;
        }
        
        .input-container {
            display: flex;
            gap: 10px;
            padding: 20px 0;
            border-top: 1px solid #333;
        }
        
        input[type="text"] {
            flex: 1;
            padding: 15px 20px;
            border: none;
            border-radius: 25px;
            background: #2d2d44;
            color: #e0e0e0;
            font-size: 1rem;
        }
        
        input[type="text"]:focus {
            outline: 2px solid #00d9ff;
        }
        
        button {
            padding: 15px 30px;
            border: none;
            border-radius: 25px;
            background: #00d9ff;
            color: #1a1a2e;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, background 0.2s;
        }
        
        button:hover {
            transform: scale(1.05);
            background: #00b8d9;
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Notifications Panel */
        .notifications-panel {
            position: fixed;
            top: 70px;
            right: 20px;
            width: 350px;
            background: #2d2d44;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
            z-index: 1000;
            display: none;
        }
        
        .notifications-panel.show {
            display: block;
        }
        
        .notifications-header {
            padding: 15px 20px;
            border-bottom: 1px solid #333;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .notifications-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .notification-item {
            padding: 15px 20px;
            border-bottom: 1px solid #333;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .notification-item:hover {
            background: #3d3d54;
        }
        
        .notification-item.success {
            border-left: 4px solid #2ed573;
        }
        
        .notification-item.error {
            border-left: 4px solid #ff4757;
        }
        
        .notification-item .time {
            font-size: 0.75rem;
            color: #888;
            margin-top: 5px;
        }
        
        .empty-notifications {
            padding: 30px 20px;
            text-align: center;
            color: #888;
        }
        
        /* Quick Actions */
        .quick-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }
        
        .quick-action {
            padding: 8px 16px;
            background: #3d3d54;
            border: 1px solid #00d9ff;
            border-radius: 20px;
            color: #00d9ff;
            font-size: 0.85rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .quick-action:hover {
            background: #00d9ff;
            color: #1a1a2e;
        }
        
        /* Loading */
        .typing-indicator {
            display: none;
            padding: 15px 20px;
            background: #2d2d44;
            border-radius: 12px;
            max-width: 80px;
        }
        
        .typing-indicator.show {
            display: block;
        }
        
        .typing-indicator span {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #00d9ff;
            border-radius: 50%;
            margin: 0 2px;
            animation: bounce 1.4s infinite ease-in-out;
        }
        
        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 Agent Graph</h1>
            <div class="notification-bell" onclick="toggleNotifications()">
                🔔
                <span class="notification-badge" id="notifBadge" style="display: none;">0</span>
            </div>
        </header>
        
        <div class="quick-actions">
            <span class="quick-action" onclick="sendQuickMessage('Start a background job with the writer agent to write a poem about nature')">
                📝 Write poem
            </span>
            <span class="quick-action" onclick="sendQuickMessage('Start a background job with the research agent to explain quantum computing')">
                🔬 Research quantum
            </span>
            <span class="quick-action" onclick="sendQuickMessage('Start a background job with the writer agent to write a short story about AI')">
                📖 Write story
            </span>
        </div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message assistant">
                Welcome! I can run background tasks using specialized agents. 
                Try starting a job with the writer or research agent!
            </div>
        </div>
        
        <div class="typing-indicator" id="typingIndicator">
            <span></span><span></span><span></span>
        </div>
        
        <div class="input-container">
            <input type="text" id="messageInput" placeholder="Type a message..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()" id="sendBtn">Send</button>
        </div>
    </div>
    
    <!-- Notifications Panel -->
    <div class="notifications-panel" id="notificationsPanel">
        <div class="notifications-header">
            <h3>Notifications</h3>
            <span style="cursor: pointer; color: #888;" onclick="toggleNotifications()">✕</span>
        </div>
        <div class="notifications-list" id="notificationsList">
            <div class="empty-notifications">No notifications</div>
        </div>
    </div>
    
    <script>
        let currentJobId = null;
        
        async function sendMessage(message = null) {
            const input = document.getElementById('messageInput');
            const sendBtn = document.getElementById('sendBtn');
            const messageText = message || input.value.trim();
            
            if (!messageText) return;
            
            // Add user message to chat
            addMessage('user', messageText);
            input.value = '';
            sendBtn.disabled = true;
            
            // Show typing indicator
            document.getElementById('typingIndicator').classList.add('show');
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: messageText })
                });
                
                const data = await response.json();
                
                // Hide typing indicator
                document.getElementById('typingIndicator').classList.remove('show');
                
                // Add assistant response
                addMessage('assistant', data.response);
                
                // Store job ID if present
                if (data.job_id) {
                    currentJobId = data.job_id;
                }
                
                // Check for notifications
                checkNotifications();
                
            } catch (error) {
                console.error('Error:', error);
                document.getElementById('typingIndicator').classList.remove('show');
                addMessage('assistant', 'Error: Could not process your message.');
            }
            
            sendBtn.disabled = false;
        }
        
        function sendQuickMessage(message) {
            sendMessage(message);
        }
        
        function addMessage(role, content) {
            const container = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            messageDiv.textContent = content;
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        async function checkNotifications() {
            try {
                const response = await fetch('/api/notifications');
                const notifications = await response.json();
                
                const badge = document.getElementById('notifBadge');
                if (notifications.length > 0) {
                    badge.textContent = notifications.length;
                    badge.style.display = 'flex';
                } else {
                    badge.style.display = 'none';
                }
            } catch (error) {
                console.error('Error checking notifications:', error);
            }
        }
        
        function toggleNotifications() {
            const panel = document.getElementById('notificationsPanel');
            panel.classList.toggle('show');
            
            if (panel.classList.contains('show')) {
                loadNotifications();
            }
        }
        
        async function loadNotifications() {
            try {
                const response = await fetch('/api/notifications');
                const notifications = await response.json();
                
                const list = document.getElementById('notificationsList');
                
                if (notifications.length === 0) {
                    list.innerHTML = '<div class="empty-notifications">No notifications</div>';
                    return;
                }
                
                list.innerHTML = notifications.map(notif => `
                    <div class="notification-item ${notif.type}" onclick="actionNotification('${notif.id}')">
                        <div>${notif.message}</div>
                        <div class="time">${new Date(notif.timestamp).toLocaleTimeString()}</div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading notifications:', error);
            }
        }
        
        async function actionNotification(notifId) {
            try {
                const response = await fetch(`/api/notifications/${notifId}/action`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                // Mark as read
                await fetch(`/api/notifications/${notifId}/read`, { method: 'POST' });
                
                // Close panel
                document.getElementById('notificationsPanel').classList.remove('show');
                
                // Send message to agent
                sendMessage(data.message);
                
                // Update badge
                checkNotifications();
                
            } catch (error) {
                console.error('Error actioning notification:', error);
            }
        }
        
        // Poll for notifications every 5 seconds
        setInterval(checkNotifications, 5000);
    </script>
</body>
</html>
"""


# =============================================================================
# Run Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app_fastapi, host="0.0.0.0", port=8000)
