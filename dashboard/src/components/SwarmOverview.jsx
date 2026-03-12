import React from 'react';
import { useSwarmState } from '../context/WebSocketContext';
import { CALLSIGNS } from '../utils/constants';

export default function SwarmOverview() {
  const { state } = useSwarmState();
  const summary = state.swarmSummary;

  if (!summary) {
    return <div className="swarm-overview" data-testid="swarm-overview">Waiting for data...</div>;
  }

  const minDroneName = CALLSIGNS[summary.min_battery_drone_id] || `Drone ${summary.min_battery_drone_id}`;

  return (
    <div className="swarm-overview" data-testid="swarm-overview">
      <h2>Swarm Overview</h2>
      <div className="status-cards" data-testid="status-cards">
        <div className="status-card" data-testid="card-active">
          <span className="card-value">{summary.active_drones}</span>
          <span className="card-label">Active</span>
        </div>
        <div className="status-card" data-testid="card-faulted">
          <span className="card-value">{summary.faulted_drones}</span>
          <span className="card-label">Faulted</span>
        </div>
        <div className="status-card" data-testid="card-returning">
          <span className="card-value">{summary.returning_drones}</span>
          <span className="card-label">Returning</span>
        </div>
        <div className="status-card" data-testid="card-idle">
          <span className="card-value">{summary.idle_drones}</span>
          <span className="card-label">Idle</span>
        </div>
      </div>
      <div className="battery-overview">
        <div data-testid="avg-battery">
          Avg Battery: {Math.round(summary.avg_battery_pct)}%
          <div className="battery-bar">
            <div
              className="battery-fill"
              style={{ width: `${summary.avg_battery_pct}%` }}
            />
          </div>
        </div>
        <div data-testid="min-battery">
          Min Battery: {Math.round(summary.min_battery_pct)}% ({minDroneName})
        </div>
      </div>
      <div className="mission-stats">
        <div data-testid="missions-done">Missions Done: {summary.missions_completed}</div>
        <div data-testid="active-alerts">Active Alerts: {summary.active_alerts}</div>
      </div>
    </div>
  );
}
