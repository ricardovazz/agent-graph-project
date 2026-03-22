# Agent Graph Dashboard

An interactive real-time dashboard for visualizing agent communication in a LangGraph-based multi-agent system. Built with **FastAPI**, **WebSocket**, **React**, **TypeScript**, and **Zustand** for reactive state management.

## Features

- 🤖 **Multi-Agent System**: Supervisor coordinates specialized sub-agents (Research & Writer)
- 💬 **Real-Time Chat**: Interactive chat interface with live message streaming
- 🔧 **Tool Call Visualization**: See all tool calls as they happen
- ⚙️ **Background Job Tracking**: Monitor job status with real-time updates
- 🕸️ **Agent Communication Graph**: Visual representation of agent interactions
- 📊 **Live Statistics**: Dashboard with message, tool call, and job counts

## Architecture

```
┌─────────────┐     ┌─────────────────────────────────────────────────┐
│             │     │              FastAPI Backend                    │
│    User     │────▶│  ┌─────────────────────────────────────────┐   │
│             │ WS  │  │           Agent Graph (LangGraph)       │   │
└─────────────┘     │  │  ┌───────────┐                          │   │
      ▲             │  │  │Supervisor │──▶ start_job tool        │   │
      │             │  │  └───────────┘                          │   │
      │             │  │       │                                  │   │
      │             │  │       ├──▶ Research Agent (background)   │   │
      │             │  │       └──▶ Writer Agent (background)     │   │
      │             │  └─────────────────────────────────────────┘   │
      │             └─────────────────────────────────────────────────┘
      │
      │ REST + WebSocket
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    React Frontend (Zustand State)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │    Chat      │  │  Job Status  │  │  Tool Calls  │              │
│  │  Interface   │  │    Panel     │  │  Visualizer  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Agent Communication Graph (ReactFlow)           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.10+
- Node.js 18+ (v20.19+ recommended)
- OpenRouter API Key (or other LLM provider)

## Installation

### 1. Clone and Setup Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -e .
```

### 2. Setup Frontend

```bash
cd frontend
npm install
cd ..
```

### 3. Set API Key

```bash
# Windows (Command Prompt)
set OPENROUTER_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:OPENROUTER_API_KEY="your_api_key_here"

# Linux/Mac
export OPENROUTER_API_KEY=your_api_key_here
```

## Running the Application

### Option 1: Using Startup Script (Windows)

```bash
start.bat
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
python -m uvicorn src.server:app_api --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Access the Dashboard

Open your browser to: **http://localhost:5173**

## API Endpoints

### REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sessions` | Create a new chat session |
| GET | `/api/sessions` | List all active sessions |
| GET | `/api/sessions/{id}` | Get session details |
| GET | `/api/jobs` | List all background jobs |
| GET | `/api/jobs/{id}` | Get specific job details |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/{session_id}` | Real-time bidirectional communication |

**WebSocket Message Types:**
- `user_message` - Send user messages to the agent
- `message` - Receive AI/human/system messages
- `tool_call` - Tool invocation events
- `tool_result` - Tool execution results
- `job_status` - Background job updates
- `status` - Connection status updates

## Usage Examples

### Starting a Research Job

```
User: "Start a background job to research the history of artificial intelligence"

→ Supervisor calls: start_job(agent_name="research", description="...")
→ Job appears in Job Status panel with "running" status
→ Research agent processes in background
→ Status updates to "completed" when done
→ User can request: "Get the result of the job"
```

### Starting a Writing Job

```
User: "Start a job with the writer agent to write a haiku about coding"

→ Supervisor calls: start_job(agent_name="writer", description="...")
→ Writer agent creates content in background
→ Tool call appears in Tool Calls visualizer
→ Agent graph shows active agent highlighting
```

### Checking Job Status

```
User: "Check the status of job_abc123"

→ Supervisor calls: check_status(job_id="job_abc123")
→ Returns current status: pending/running/completed/failed
→ Job panel updates in real-time
```

## Project Structure

```
agent-graph-project/
├── src/
│   ├── agent_graph.py      # LangGraph agent definitions
│   ├── server.py           # FastAPI backend with WebSocket
│   └── __init__.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx       # Chat UI component
│   │   │   ├── JobStatusPanel.tsx      # Job tracking panel
│   │   │   ├── ToolCallVisualizer.tsx  # Tool call display
│   │   │   └── AgentGraph.tsx          # Agent visualization
│   │   ├── store/
│   │   │   └── appStore.ts             # Zustand state management
│   │   ├── App.tsx                     # Main app component
│   │   └── main.tsx                    # Entry point
│   └── package.json
├── pyproject.toml
├── start.bat                 # Windows startup script
├── start.sh                  # Linux/Mac startup script
└── README.md
```

## Three-Tool Pattern

The supervisor agent uses a three-tool pattern for background job management:

1. **`start_job(agent_name, description)`** - Initiates a background job
2. **`check_status(job_id)`** - Polls job status
3. **`get_result(job_id)`** - Retrieves completed results

This pattern enables:
- Non-blocking agent execution
- Real-time status updates
- Clean separation of concerns

## Technology Stack

### Backend
- **FastAPI** - Async web framework
- **WebSocket** - Real-time bidirectional communication
- **LangGraph** - Agent orchestration
- **LangChain** - LLM integration
- **Threading** - Background job execution

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Zustand** - State management
- **ReactFlow** - Graph visualization
- **Bootstrap 5** - Styling
- **ReactMarkdown** - Markdown rendering

## Troubleshooting

### "OPENROUTER_API_KEY environment variable is required"
Set your API key before starting the server (see Installation step 3).

### WebSocket connection fails
- Ensure the backend server is running on port 8000
- Check that no firewall is blocking WebSocket connections
- Verify the session ID is valid

### Frontend doesn't connect
- Make sure both backend and frontend are running
- Check browser console for errors
- Verify CORS is enabled (default in development)

## License

MIT
