import React from 'react';
import { useSwarmState } from '../context/WebSocketContext';

export default function ConnectionStatus() {
  const { state } = useSwarmState();
  const connected = state.wsConnected;

  return (
    <div className="connection-status" data-testid="connection-status">
      <span
        className={`status-dot ${connected ? 'connected' : 'disconnected'}`}
        data-testid="status-dot"
      />
      <span data-testid="status-text">
        {connected ? 'Connected' : 'Disconnected'}
      </span>
    </div>
  );
}
