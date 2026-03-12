import React from 'react';
import { useSwarmState } from '../context/WebSocketContext';
import { CALLSIGNS } from '../utils/constants';

const SEVERITY_ICONS = {
  0: '○',  // INFO
  1: '⚠',  // WARNING
  2: '●',  // CRITICAL
};

const SEVERITY_CLASSES = {
  0: 'info',
  1: 'warning',
  2: 'critical',
};

export default function AlertFeed() {
  const { state } = useSwarmState();

  return (
    <div className="alert-feed" data-testid="alert-feed">
      <h2>Alert Feed</h2>
      <div className="alert-list" data-testid="alert-list">
        {state.alerts.map((alert, idx) => (
          <div
            key={`${alert.drone_id}-${alert.alert_seq || idx}`}
            className={`alert-item ${SEVERITY_CLASSES[alert.severity] || 'info'}`}
            data-testid="alert-item"
          >
            <span className="alert-icon">{SEVERITY_ICONS[alert.severity] || '○'}</span>
            <span className="alert-callsign">{CALLSIGNS[alert.drone_id] || `Drone ${alert.drone_id}`}</span>
            <span className="alert-message">{alert.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
