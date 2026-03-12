import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WebSocketProvider } from '../../context/WebSocketContext';
import SwarmOverview from '../../components/SwarmOverview';

const testState = {
  wsConnected: true, droneStates: {}, droneHistory: {}, droneTrails: {},
  missions: {}, alerts: [], selectedDroneId: 0,
  showTrails: true, showWaypoints: true, darkMode: true,
  swarmSummary: {
    active_drones: 5, faulted_drones: 1, returning_drones: 1, idle_drones: 1,
    avg_battery_pct: 73.25, min_battery_pct: 31.0, min_battery_drone_id: 2,
    missions_completed: 3, active_alerts: 2,
  },
};

describe('SPEC 13 — Swarm Overview', () => {
  it('shows status cards with correct counts', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <SwarmOverview />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('card-active').textContent).toContain('5');
    expect(screen.getByTestId('card-faulted').textContent).toContain('1');
    expect(screen.getByTestId('card-returning').textContent).toContain('1');
    expect(screen.getByTestId('card-idle').textContent).toContain('1');
  });

  it('shows battery overview', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <SwarmOverview />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('avg-battery').textContent).toContain('73%');
    expect(screen.getByTestId('min-battery').textContent).toContain('31%');
    expect(screen.getByTestId('min-battery').textContent).toContain('CHARLIE');
  });

  it('shows mission stats', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <SwarmOverview />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('missions-done').textContent).toContain('3');
    expect(screen.getByTestId('active-alerts').textContent).toContain('2');
  });
});
