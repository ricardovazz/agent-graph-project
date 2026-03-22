import React from 'react';
import { useAppStore } from '../store/appStore';

export const ToolCallVisualizer: React.FC = () => {
  const { toolCalls } = useAppStore();

  const getToolIcon = (toolName: string) => {
    switch (toolName) {
      case 'start_job':
        return '🚀';
      case 'check_status':
        return '📊';
      case 'get_result':
        return '📦';
      default:
        return '🔧';
    }
  };

  const getToolDescription = (toolName: string) => {
    switch (toolName) {
      case 'start_job':
        return 'Starts a background job with a sub-agent';
      case 'check_status':
        return 'Checks the status of a background job';
      case 'get_result':
        return 'Retrieves the result of a completed job';
      default:
        return 'Tool execution';
    }
  };

  return (
    <div className="card h-100 shadow-sm">
      <div className="card-header bg-dark text-white">
        <h5 className="mb-0">🔧 Tool Calls</h5>
      </div>
      
      <div className="card-body overflow-auto" style={{ maxHeight: '100%' }}>
        {toolCalls.length === 0 ? (
          <div className="text-center text-muted mt-4">
            <p className="mb-0">No tool calls yet</p>
            <small>Tool calls will appear here when the supervisor uses them</small>
          </div>
        ) : (
          <div className="d-flex flex-column gap-2">
            {toolCalls.map((call, index) => (
              <div 
                key={call.id || index}
                className="card border-primary border-opacity-25"
              >
                <div className="card-body p-3">
                  <div className="d-flex align-items-center gap-2 mb-2">
                    <span className="fs-4">{getToolIcon(call.name)}</span>
                    <div>
                      <code className="fw-bold text-primary">{call.name}</code>
                      <small className="text-muted d-block">
                        {getToolDescription(call.name)}
                      </small>
                    </div>
                  </div>
                  
                  {Object.keys(call.args).length > 0 && (
                    <div className="bg-light rounded p-2 mt-2">
                      <small className="fw-bold text-muted d-block mb-1">Arguments:</small>
                      <pre className="mb-0 small" style={{ fontSize: '0.75rem', overflow: 'auto' }}>
                        {JSON.stringify(call.args, null, 2)}
                      </pre>
                    </div>
                  )}
                  
                  <div className="mt-2 text-end">
                    <small className="text-muted">
                      {new Date(call.timestamp).toLocaleTimeString()}
                    </small>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
