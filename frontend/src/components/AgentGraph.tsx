import React, { useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  MarkerType,
  type Node,
  type Edge,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useAppStore } from '../store/appStore';

const AgentGraph: React.FC = () => {
  const { agentNodes, agentEdges, activeAgent, messages } = useAppStore();

  // Count messages per agent for activity visualization
  const messageCounts = useMemo(() => {
    const counts: Record<string, number> = { user: 0, supervisor: 0, research: 0, writer: 0 };
    messages.forEach(msg => {
      if (msg.type === 'human') counts.user++;
      else if (msg.type === 'ai') counts.supervisor++;
      else if (msg.type === 'tool_call') {
        const agentName = msg.metadata?.args?.agent_name;
        if (agentName === 'research') counts.research++;
        else if (agentName === 'writer') counts.writer++;
      }
    });
    return counts;
  }, [messages]);

  const nodes: Node[] = useMemo(() =>
    agentNodes.map(node => {
      const isActive = node.id === activeAgent;
      const messageCount = messageCounts[node.id as keyof typeof messageCounts] || 0;

      let bgColor = '#6c757d';
      let borderColor = '#495057';

      if (node.type === 'supervisor') {
        bgColor = '#0d6efd';
        borderColor = '#0a58ca';
      } else if (node.type === 'subagent') {
        bgColor = node.id === 'research' ? '#198754' : '#ffc107';
        borderColor = node.id === 'research' ? '#146c43' : '#d99e0b';
      } else if (node.type === 'user') {
        bgColor = '#6f42c1';
        borderColor = '#59359a';
      }

      if (isActive) {
        bgColor = '#dc3545';
        borderColor = '#b02a37';
      }

      const nodePosition = node.id === 'user' ? { x: 50, y: 50 } :
                  node.id === 'supervisor' ? { x: 300, y: 50 } :
                  node.id === 'research' ? { x: 550, y: 0 } :
                  { x: 550, y: 150 };

      return {
        id: node.id,
        position: nodePosition,
        data: {
          label: (
            <div className={`p-3 rounded text-center ${isActive ? 'animate-pulse' : ''}`}>
              <div
                className="fw-bold text-white mb-1"
                style={{
                  backgroundColor: bgColor,
                  border: `2px solid ${borderColor}`,
                  borderRadius: '8px',
                  padding: '12px 20px',
                  minWidth: '150px',
                  boxShadow: isActive ? '0 0 20px rgba(220, 53, 69, 0.5)' : '0 2px 8px rgba(0,0,0,0.15)',
                  transition: 'all 0.3s ease',
                }}
              >
                <div className="d-flex align-items-center justify-content-center gap-2">
                  {node.id === 'user' && '👤'}
                  {node.id === 'supervisor' && '🎯'}
                  {node.id === 'research' && '🔍'}
                  {node.id === 'writer' && '✏️'}
                  <span>{node.label}</span>
                </div>
                {messageCount > 0 && (
                  <div className="mt-1">
                    <span className="badge bg-white bg-opacity-25">
                      {messageCount} msgs
                    </span>
                  </div>
                )}
              </div>
              <div className="mt-1">
                <span className={`badge ${isActive ? 'bg-danger' : 'bg-success'}`}>
                  {isActive ? '⚡ Active' : '○ Idle'}
                </span>
              </div>
            </div>
          ),
        },
        draggable: false,
        selectable: false,
        style: {
          background: 'transparent',
          border: 'none',
        },
      };
    }), [agentNodes, activeAgent, messageCounts]
  );

  const edges: Edge[] = useMemo(() => 
    agentEdges.map(edge => {
      const isActive = activeAgent === edge.target;
      return {
        ...edge,
        type: 'smoothstep',
        animated: isActive,
        style: { 
          stroke: isActive ? '#dc3545' : '#6c757d', 
          strokeWidth: isActive ? 3 : 2,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isActive ? '#dc3545' : '#6c757d',
        },
        labelStyle: {
          fill: isActive ? '#dc3545' : '#6c757d',
          fontWeight: isActive ? 'bold' : 'normal',
          fontSize: '12px',
        },
      };
    }), [agentEdges, activeAgent]
  );

  return (
    <div className="card h-100 shadow-sm">
      <div className="card-header bg-dark text-white">
        <h5 className="mb-0">🕸️ Agent Communication Graph</h5>
      </div>
      
      <div className="card-body p-0" style={{ height: '400px' }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          attributionPosition="bottom-left"
          nodesDraggable={false}
          nodesConnectable={false}
          elementsSelectable={false}
          panOnDrag={false}
          zoomOnScroll={false}
          zoomOnPinch={false}
          zoomOnDoubleClick={false}
        >
          <Background color="#aaa" gap={16} />
          <Controls showInteractive={false} />
          <MiniMap
            nodeColor={(n: Node) => {
              if (n.id === 'user') return '#6f42c1';
              if (n.id === 'supervisor') return '#0d6efd';
              if (n.id === 'research') return '#198754';
              return '#ffc107';
            }}
            maskColor="rgb(240, 240, 240, 0.6)"
          />
        </ReactFlow>
      </div>
      
      <div className="card-footer bg-light">
        <small className="text-muted">
          <span className="badge bg-primary me-1">Supervisor</span>
          <span className="badge bg-success me-1">Research</span>
          <span className="badge bg-warning text-dark me-1">Writer</span>
          <span className="badge bg-secondary">User</span>
        </small>
      </div>
    </div>
  );
};

export default AgentGraph;
