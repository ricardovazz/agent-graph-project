import React from 'react';
import { useAppStore } from './store/appStore';
import { ChatInterface } from './components/ChatInterface';
import { JobStatusPanel } from './components/JobStatusPanel';
import { ToolCallVisualizer } from './components/ToolCallVisualizer';
import AgentGraph from './components/AgentGraph';

function App() {
  const { sessionId, connected, createSession, clearSession, error, messages, toolCalls, jobs } = useAppStore();

  React.useEffect(() => {
    if (!sessionId) {
      createSession();
    }
  }, [sessionId, createSession]);

  return (
    <div className="min-vh-100 bg-light">
      {/* Header */}
      <header className="bg-dark text-white py-3 shadow">
        <div className="container-fluid">
          <div className="d-flex justify-content-between align-items-center">
            <div className="d-flex align-items-center gap-3">
              <h1 className="h3 mb-0">🤖 Agent Graph Dashboard</h1>
              <span className={`badge ${connected ? 'bg-success' : 'bg-danger'}`}>
                {connected ? '● Connected' : '○ Disconnected'}
              </span>
            </div>
            <div className="d-flex align-items-center gap-3">
              {sessionId && (
                <small className="text-muted">
                  Session: <code>{sessionId}</code>
                </small>
              )}
              <button 
                className="btn btn-outline-light btn-sm"
                onClick={clearSession}
              >
                🔄 New Session
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Error Alert */}
      {error && (
        <div className="container-fluid mt-3">
          <div className="alert alert-danger alert-dismissible fade show" role="alert">
            <strong>Error:</strong> {error}
            <button 
              type="button" 
              className="btn-close" 
              onClick={() => useAppStore.setState({ error: null })}
            />
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="container-fluid py-4">
        {/* Stats Row */}
        <div className="row g-3 mb-4">
          <div className="col-md-3">
            <div className="card shadow-sm border-primary">
              <div className="card-body text-center">
                <div className="display-4 text-primary">💬</div>
                <h3 className="h2 mb-0">{messages.length}</h3>
                <p className="text-muted mb-0">Messages</p>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card shadow-sm border-success">
              <div className="card-body text-center">
                <div className="display-4 text-success">🔧</div>
                <h3 className="h2 mb-0">{toolCalls.length}</h3>
                <p className="text-muted mb-0">Tool Calls</p>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card shadow-sm border-warning">
              <div className="card-body text-center">
                <div className="display-4 text-warning">⚙️</div>
                <h3 className="h2 mb-0">{jobs.length}</h3>
                <p className="text-muted mb-0">Background Jobs</p>
              </div>
            </div>
          </div>
          <div className="col-md-3">
            <div className="card shadow-sm border-info">
              <div className="card-body text-center">
                <div className="display-4 text-info">🤖</div>
                <h3 className="h2 mb-0">3</h3>
                <p className="text-muted mb-0">Active Agents</p>
              </div>
            </div>
          </div>
        </div>

        {/* Agent Graph */}
        <div className="row g-3 mb-4">
          <div className="col-12">
            <AgentGraph />
          </div>
        </div>

        {/* Main Dashboard Grid */}
        <div className="row g-3">
          <div className="col-lg-6">
            <ChatInterface />
          </div>
          <div className="col-lg-3">
            <JobStatusPanel />
          </div>
          <div className="col-lg-3">
            <ToolCallVisualizer />
          </div>
        </div>

        {/* Info Section */}
        <div className="row g-3 mt-4">
          <div className="col-12">
            <div className="card shadow-sm">
              <div className="card-header bg-light">
                <h5 className="mb-0">ℹ️ How It Works</h5>
              </div>
              <div className="card-body">
                <div className="row g-4">
                  <div className="col-md-4">
                    <div className="d-flex align-items-start gap-3">
                      <div className="fs-1">🎯</div>
                      <div>
                        <h6>Supervisor Agent</h6>
                        <p className="small text-muted mb-0">
                          Coordinates tasks and delegates to specialized sub-agents using the three-tool pattern.
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="d-flex align-items-start gap-3">
                      <div className="fs-1">🔍</div>
                      <div>
                        <h6>Research Agent</h6>
                        <p className="small text-muted mb-0">
                          Handles research and fact-finding tasks in background jobs.
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-4">
                    <div className="d-flex align-items-start gap-3">
                      <div className="fs-1">✏️</div>
                      <div>
                        <h6>Writer Agent</h6>
                        <p className="small text-muted mb-0">
                          Creates and edits content based on your requests.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-light rounded">
                  <h6>Try these commands:</h6>
                  <ul className="mb-0 small">
                    <li><code>"Start a background job to research the history of AI"</code></li>
                    <li><code>"Start a job with the writer agent to write a poem about coding"</code></li>
                    <li><code>"Check the status of the current job"</code></li>
                    <li><code>"Get the result of the last job"</code></li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-dark text-white py-3 mt-5">
        <div className="container-fluid text-center">
          <small className="text-muted">
            Agent Graph Dashboard • Built with LangChain, FastAPI, React & WebSocket
          </small>
        </div>
      </footer>
    </div>
  );
}

export default App;
