# LangSmith Tracing Setup Guide

## Problem Solved

The Three-Tool Pattern was using `threading.Thread` for background jobs, which caused:
1. **Lost tracing context**: Python's `contextvars` don't propagate to new threads
2. **No sub-agent visibility**: Sub-agent traces didn't appear in LangSmith UI
3. **No graph nodes**: LangGraph node execution wasn't visible in traces
4. **No conversation grouping**: Related runs weren't grouped together

## Solution Implemented

### 1. Context Propagation for Threads
Replaced `threading.Thread` with LangSmith's `ContextThreadPoolExecutor`, which automatically propagates tracing context to worker threads.

### 2. Callback Handler Integration
Added `LangChainTracer` callback handler that's passed to:
- Supervisor agent invocations
- Sub-agent invocations (within background jobs)
- Graph compilation

### 3. Thread Support (LangSmith Threads)
Added thread management functions to group related runs together:
- `create_thread_id()`: Generate unique thread IDs
- `get_thread_config(thread_id)`: Get config dict with thread_id and callbacks

### 4. Environment Configuration
LangSmith tracing requires these environment variables:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your-api-key-here
LANGSMITH_PROJECT=agent-graph-project  # optional, defaults to "default"
```

## Setup Instructions

### Step 1: Get LangSmith API Key
1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Sign up or log in
3. Go to Settings → API Keys
4. Create a new API key

### Step 2: Configure Environment
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```bash
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=lsv2_pt_...  # Your LangSmith API key
   LANGSMITH_PROJECT=agent-graph-project
   OPENROUTER_API_KEY=sk_or_...   # Your OpenRouter API key
   ```

### Step 3: Install Dependencies
```bash
pip install -e .
```

Or install just the new dependencies:
```bash
pip install langsmith python-dotenv typing_extensions
```

### Step 4: Run and Verify
```bash
python test.py
```

You should see:
```
✓ LangSmith tracing enabled
  Project: agent-graph-project
  View traces at: https://smith.langchain.com
```

## Viewing Traces

After running your agent:

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Navigate to your project (`agent-graph-project`)
3. Click on a recent trace
4. You'll see:
   - **Graph nodes**: Each node (e.g., "supervisor") as a run
   - **Tool calls**: `start_job`, `check_status`, `get_result`
   - **Sub-agent traces**: Nested runs for research/writer agents
   - **LLM calls**: Individual model invocations with inputs/outputs
   - **Timing**: Execution duration for each step

## Key Changes Made

### `src/agent_graph.py`

```python
# NEW: Imports
from langsmith.utils import ContextThreadPoolExecutor
from langchain_core.tracers.langchain import LangChainTracer
from langsmith import Client

# NEW: LangSmith tracer initialization
_langsmith_client = Client() if os.environ.get("LANGSMITH_API_KEY") else None
_langchain_tracer = LangChainTracer(client=_langsmith_client) if _langsmith_client else None

def _get_callbacks():
    """Get callbacks for tracing if LangSmith is configured."""
    return [_langchain_tracer] if _langchain_tracer else []

# UPDATED: JobStorage uses ContextThreadPoolExecutor
class JobStorage:
    def __init__(self):
        self._executor: ContextThreadPoolExecutor = ContextThreadPoolExecutor(max_workers=10)

# UPDATED: start_job captures callbacks and passes to sub-agent
@tool
def start_job(agent_name: str, description: str) -> str:
    callbacks = _get_callbacks()
    
    def run_job():
        result = loop.run_until_complete(agent.ainvoke(
            {"messages": [...]},
            config={"callbacks": callbacks} if callbacks else {}
        ))

# UPDATED: Graph nodes use callbacks
async def supervisor(state: State) -> State:
    callbacks = _get_callbacks()
    config = {"callbacks": callbacks} if callbacks else {}
    response = await supervisor_agent.ainvoke({"messages": state["messages"]}, config=config)
```

### `test.py`

```python
# NEW: Environment variable loading
from dotenv import load_dotenv
load_dotenv()

# NEW: Tracing status check
if os.environ.get("LANGSMITH_API_KEY"):
    print("✓ LangSmith tracing enabled")
else:
    print("✗ LangSmith tracing NOT enabled")

# NEW: Thread support for grouping related runs
from src.agent_graph import get_thread_config, create_thread_id

thread_id = create_thread_id()
config = get_thread_config(thread_id)

# All runs with same thread_id are grouped in LangSmith
result = await app.ainvoke({"messages": [...]}, config=config)
```

## Using LangSmith Threads

### What Are Threads?

**Threads** group related runs together in LangSmith, perfect for:
- Multi-turn conversations
- Polling workflows (start → check → get_result)
- User session tracking
- Related job executions

### How to Use Threads

```python
from src.agent_graph import get_thread_config, create_thread_id

# Option 1: Auto-generate thread ID
thread_id = create_thread_id()
config = get_thread_config(thread_id)

# Option 2: Use your own thread ID (e.g., user ID, session ID)
config = get_thread_config("user_123_session_456")

# Option 3: No threading (each run independent)
config = get_thread_config()

# Use config in all invocations
result = await app.ainvoke({"messages": [...]}, config=config)
```

### Viewing Threads in LangSmith

1. Go to [smith.langchain.com](https://smith.langchain.com)
2. Navigate to your project
3. Click the **Threads** tab
4. Find your thread by ID or filter by metadata
5. Click to see all runs grouped together

### Best Practices

| Use Case | Thread ID Strategy |
|----------|-------------------|
| User conversations | `user_{user_id}` |
| Session tracking | `session_{session_id}` |
| Job workflows | `job_{job_id}` |
| Testing | `test_{timestamp}` |
| Production | `{user_id}_{conversation_id}` |

## Troubleshooting

### No traces appearing in LangSmith
1. Verify `LANGSMITH_API_KEY` is set correctly
2. Check `LANGSMITH_TRACING=true` is set
3. Ensure you're looking at the correct project
4. Check network connectivity to LangSmith API

### Sub-agent traces still not showing
1. Verify callbacks are being passed in `ainvoke()` calls
2. Check that `ContextThreadPoolExecutor` is being used (not `threading.Thread`)
3. Ensure LangSmith API key has proper permissions

### Graph nodes not visible
1. Make sure callbacks are passed to graph compilation or node functions
2. Use `.with_config({"callbacks": [...]})` when compiling or invoking the graph

## References

- [LangSmith Observability Docs](https://docs.langchain.com/oss/python/langgraph/observability)
- [Context Propagation with Threading](https://docs.langchain.com/langsmith/nest-traces#context-propagation-using-threading)
- [Trace with LangGraph](https://docs.langchain.com/langsmith/trace-with-langgraph)
