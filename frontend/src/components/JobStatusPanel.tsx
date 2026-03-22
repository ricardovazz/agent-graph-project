import React from 'react';
import { useAppStore, type Job } from '../store/appStore';

export const JobStatusPanel: React.FC = () => {
  const { jobs } = useAppStore();

  const getStatusBadge = (status: Job['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-secondary';
      case 'running':
        return 'bg-warning text-dark';
      case 'completed':
        return 'bg-success';
      case 'failed':
        return 'bg-danger';
      default:
        return 'bg-secondary';
    }
  };

  const getStatusIcon = (status: Job['status']) => {
    switch (status) {
      case 'pending':
        return '⏳';
      case 'running':
        return '🔄';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      default:
        return '📋';
    }
  };

  const getAgentIcon = (agent?: string) => {
    switch (agent) {
      case 'research':
        return '🔍';
      case 'writer':
        return '✏️';
      default:
        return '🤖';
    }
  };

  // Auto-refresh jobs every 2 seconds
  React.useEffect(() => {
    const interval = setInterval(async () => {
      // Poll for job updates
      const runningJobs = jobs.filter(j => j.status === 'running');
      if (runningJobs.length > 0) {
        // In a real app, you'd fetch updated job status here
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [jobs]);

  return (
    <div className="card h-100 shadow-sm">
      <div className="card-header bg-dark text-white">
        <h5 className="mb-0">⚙️ Background Jobs</h5>
      </div>
      
      <div className="card-body overflow-auto" style={{ maxHeight: '100%' }}>
        {jobs.length === 0 ? (
          <div className="text-center text-muted mt-4">
            <p className="mb-0">No background jobs</p>
            <small>Jobs will appear here when started</small>
          </div>
        ) : (
          <div className="d-flex flex-column gap-3">
            {jobs.map((job) => (
              <div 
                key={job.job_id}
                className="card border shadow-sm"
                style={{ fontSize: '0.85rem' }}
              >
                <div className="card-body p-3">
                  <div className="d-flex justify-content-between align-items-start mb-2">
                    <div className="d-flex align-items-center gap-2">
                      <span className="fs-5">{getAgentIcon(job.agent)}</span>
                      <code className="bg-light px-2 py-1 rounded">
                        {job.job_id}
                      </code>
                    </div>
                    <span className={`badge ${getStatusBadge(job.status)}`}>
                      {getStatusIcon(job.status)} {job.status}
                    </span>
                  </div>
                  
                  {job.description && (
                    <p className="mb-2 text-muted small">
                      <strong>Task:</strong> {job.description}
                    </p>
                  )}
                  
                  {job.agent && (
                    <p className="mb-2">
                      <small className="text-muted">Agent: </small>
                      <span className="fw-bold text-capitalize">{job.agent}</span>
                    </p>
                  )}
                  
                  {job.status === 'running' && (
                    <div className="progress" style={{ height: '6px' }}>
                      <div 
                        className="progress-bar progress-bar-striped progress-bar-animated"
                        style={{ width: '100%' }}
                      />
                    </div>
                  )}
                  
                  {job.status === 'completed' && job.result && (
                    <div className="mt-2 p-2 bg-success bg-opacity-10 rounded">
                      <small className="fw-bold text-success">✓ Result:</small>
                      <p className="mb-0 mt-1 small">{job.result}</p>
                    </div>
                  )}
                  
                  {job.status === 'failed' && job.error && (
                    <div className="mt-2 p-2 bg-danger bg-opacity-10 rounded">
                      <small className="fw-bold text-danger">✗ Error:</small>
                      <p className="mb-0 mt-1 small">{job.error}</p>
                    </div>
                  )}
                  
                  <div className="mt-2 d-flex justify-content-between">
                    <small className="text-muted">
                      Started: {new Date(job.created_at).toLocaleString()}
                    </small>
                    {job.completed_at && (
                      <small className="text-muted">
                        Completed: {new Date(job.completed_at).toLocaleString()}
                      </small>
                    )}
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
