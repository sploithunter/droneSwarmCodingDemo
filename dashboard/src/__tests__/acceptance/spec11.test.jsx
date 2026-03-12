import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WebSocketProvider } from '../../context/WebSocketContext';
import ConnectionStatus from '../../components/ConnectionStatus';

describe('SPEC 11 — Connection Management', () => {
  it('shows Connected when wsConnected is true', () => {
    render(
      <WebSocketProvider initialStateOverride={{
        wsConnected: true, droneStates: {}, droneHistory: {}, droneTrails: {},
        missions: {}, alerts: [], swarmSummary: null, selectedDroneId: 0,
        showTrails: true, showWaypoints: true, darkMode: true,
      }}>
        <ConnectionStatus />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('status-text').textContent).toBe('Connected');
  });

  it('shows Disconnected when wsConnected is false', () => {
    render(
      <WebSocketProvider initialStateOverride={{
        wsConnected: false, droneStates: {}, droneHistory: {}, droneTrails: {},
        missions: {}, alerts: [], swarmSummary: null, selectedDroneId: 0,
        showTrails: true, showWaypoints: true, darkMode: true,
      }}>
        <ConnectionStatus />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('status-text').textContent).toBe('Disconnected');
  });

  it('has green class when connected', () => {
    render(
      <WebSocketProvider initialStateOverride={{
        wsConnected: true, droneStates: {}, droneHistory: {}, droneTrails: {},
        missions: {}, alerts: [], swarmSummary: null, selectedDroneId: 0,
        showTrails: true, showWaypoints: true, darkMode: true,
      }}>
        <ConnectionStatus />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('status-dot').classList.contains('connected')).toBe(true);
  });
});
