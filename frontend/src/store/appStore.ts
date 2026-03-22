import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';

export type MessageType = 'human' | 'ai' | 'tool_call' | 'tool_result' | 'job_status' | 'system';

export interface Message {
  id: string;
  type: MessageType;
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface ToolCall {
  id: string;
  name: string;
  args: Record<string, any>;
  timestamp: string;
}

export interface Job {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: string;
  error?: string;
  agent?: string;
  description?: string;
  created_at: string;
  completed_at?: string;
}

export interface AgentNode {
  id: string;
  label: string;
  type: 'supervisor' | 'subagent' | 'user';
  status: 'idle' | 'active' | 'completed';
  lastActivity?: string;
}

export interface AgentEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  animated?: boolean;
  active?: boolean;
}

interface AppState {
  // Session
  sessionId: string | null;
  connected: boolean;
  websocket: WebSocket | null;

  // Messages
  messages: Message[];

  // Tool calls
  toolCalls: ToolCall[];

  // Jobs
  jobs: Job[];

  // Agent graph visualization
  agentNodes: AgentNode[];
  agentEdges: AgentEdge[];
  activeAgent: string | null;

  // Status
  status: 'idle' | 'thinking' | 'error';
  statusMessage: string;
  error: string | null;

  // Polling
  jobPollingInterval: NodeJS.Timeout | null;

  // Actions
  createSession: () => Promise<void>;
  sendMessage: (content: string) => void;
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
  updateJobStatus: (jobId: string, status: Partial<Job>) => void;
  setActiveAgent: (agentId: string | null) => void;
  clearSession: () => void;
  startJobPolling: () => void;
  stopJobPolling: () => void;
}

const API_URL = 'http://localhost:8000';

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  sessionId: null,
  connected: false,
  websocket: null,
  messages: [],
  toolCalls: [],
  jobs: [],
  agentNodes: [
    { id: 'user', label: 'User', type: 'user', status: 'idle' },
    { id: 'supervisor', label: 'Supervisor', type: 'supervisor', status: 'idle' },
    { id: 'research', label: 'Research Agent', type: 'subagent', status: 'idle' },
    { id: 'writer', label: 'Writer Agent', type: 'subagent', status: 'idle' },
  ],
  agentEdges: [
    { id: 'e1', source: 'user', target: 'supervisor', label: 'request' },
    { id: 'e2', source: 'supervisor', target: 'research', label: 'delegate' },
    { id: 'e3', source: 'supervisor', target: 'writer', label: 'delegate' },
  ],
  activeAgent: null,
  status: 'idle',
  statusMessage: 'Ready',
  error: null,
  jobPollingInterval: null,

  createSession: async () => {
    try {
      const response = await fetch(`${API_URL}/api/sessions`, {
        method: 'POST',
      });
      const data = await response.json();
      set({ sessionId: data.session_id, messages: [], toolCalls: [], jobs: [] });
      get().connectWebSocket();
    } catch (err) {
      set({ error: `Failed to create session: ${err}` });
    }
  },

  sendMessage: (content: string) => {
    const { websocket, connected } = get();
    if (!connected || !websocket) {
      set({ error: 'Not connected to server' });
      return;
    }

    // Add user message optimistically
    const userMessage: Message = {
      id: `msg_${uuidv4().slice(0, 8)}`,
      type: 'human',
      content,
      timestamp: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMessage],
      status: 'thinking',
      statusMessage: 'Sending...',
    }));

    // Send via WebSocket
    websocket.send(JSON.stringify({
      type: 'user_message',
      content,
    }));

    // Activate supervisor
    set({ activeAgent: 'supervisor' });
  },

  connectWebSocket: () => {
    const { sessionId } = get();
    if (!sessionId) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);

    ws.onopen = () => {
      set({ connected: true, websocket: ws, error: null });
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    ws.onclose = () => {
      set({ connected: false, websocket: null, status: 'idle' });
    };

    ws.onerror = () => {
      set({ error: 'WebSocket connection error', connected: false });
    };
  },

  disconnectWebSocket: () => {
    const { websocket } = get();
    if (websocket) {
      websocket.close();
      set({ websocket: null, connected: false });
    }
  },

  updateJobStatus: (jobId: string, status: Partial<Job>) => {
    set((state) => ({
      jobs: state.jobs.map((job) =>
        job.job_id === jobId ? { ...job, ...status } : job
      ),
    }));
  },

  setActiveAgent: (agentId: string | null) => {
    set((state) => ({
      activeAgent: agentId,
      agentNodes: state.agentNodes.map((node) => ({
        ...node,
        status: node.id === agentId ? 'active' : node.id === 'user' ? 'idle' : 
                node.status === 'active' ? 'completed' : node.status,
      })),
    }));
  },

  clearSession: () => {
    get().disconnectWebSocket();
    get().stopJobPolling();
    set({
      sessionId: null,
      messages: [],
      toolCalls: [],
      jobs: [],
      connected: false,
      websocket: null,
      activeAgent: null,
      status: 'idle',
      statusMessage: 'Ready',
      error: null,
    });
  },

  startJobPolling: () => {
    const { stopJobPolling } = get();
    stopJobPolling(); // Clear any existing interval
    
    const interval = setInterval(() => {
      const { jobs, sessionId } = get();
      if (!sessionId) return;
      
      // Poll for each running job
      jobs.filter(job => job.status === 'running').forEach(async (job) => {
        try {
          const resp = await fetch(`${API_URL}/api/jobs/${job.job_id}/status`);
          if (resp.ok) {
            const data = await resp.json();
            if (data.status !== job.status) {
              // Status changed, update via WebSocket handler
              handleWebSocketMessage({
                type: 'job_status',
                data: data
              });
            }
          }
        } catch (err) {
          console.error('Failed to poll job status:', err);
        }
      });
    }, 2000); // Poll every 2 seconds
    
    set({ jobPollingInterval: interval });
  },

  stopJobPolling: () => {
    const { jobPollingInterval } = get();
    if (jobPollingInterval) {
      clearInterval(jobPollingInterval);
      set({ jobPollingInterval: null });
    }
  },
}));

function handleWebSocketMessage(data: { type: string; data: any }) {
  switch (data.type) {
    case 'message':
      useAppStore.setState((s) => ({
        messages: [...s.messages, data.data],
        status: data.data.type === 'ai' ? 'idle' : s.status,
        statusMessage: data.data.type === 'ai' ? 'Ready' : s.statusMessage,
      }));
      break;

    case 'tool_call':
      useAppStore.setState((s) => ({
        toolCalls: [...s.toolCalls, data.data],
        activeAgent: data.data.name === 'start_job' ? 
          (data.data.args?.agent_name === 'research' ? 'research' : 'writer') : 'supervisor',
      }));
      break;

    case 'tool_result':
      useAppStore.setState((s) => ({
        messages: [...s.messages, {
          id: `tool_result_${uuidv4().slice(0, 8)}`,
          type: 'tool_result' as MessageType,
          content: data.data.content,
          timestamp: new Date().toISOString(),
          metadata: { tool_call_id: data.data.tool_call_id },
        }],
      }));
      break;

    case 'job_status':
      const newJob: Job = {
        job_id: data.data.job_id,
        status: data.data.status as Job['status'],
        agent: data.data.agent,
        description: data.data.description,
        created_at: data.data.created_at,
        result: data.data.result,
        error: data.data.error,
        completed_at: data.data.completed_at,
      };
      useAppStore.setState((s) => {
        // Check if job already exists
        const existingJobIndex = s.jobs.findIndex(j => j.job_id === newJob.job_id);
        let updatedJobs;
        if (existingJobIndex >= 0) {
          // Update existing job
          updatedJobs = [...s.jobs];
          updatedJobs[existingJobIndex] = { ...updatedJobs[existingJobIndex], ...newJob };
        } else {
          // Add new job
          updatedJobs = [...s.jobs, newJob];
        }
        
        // Start polling if there are running jobs
        const hasRunningJobs = updatedJobs.some(j => j.status === 'running');
        if (hasRunningJobs) {
          useAppStore.getState().startJobPolling();
        }
        
        return { jobs: updatedJobs };
      });
      break;

    case 'status':
      useAppStore.setState({
        status: data.data.status as 'idle' | 'thinking',
        statusMessage: data.data.message,
      });
      break;

    case 'error':
      useAppStore.setState({
        error: data.data.message,
        status: 'idle',
      });
      break;
  }
}
