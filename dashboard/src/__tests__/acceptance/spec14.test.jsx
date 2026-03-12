import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WebSocketProvider } from '../../context/WebSocketContext';
import AlertFeed from '../../components/AlertFeed';

describe('SPEC 14 — Alert Feed', () => {
  it('displays alerts with callsign and message', () => {
    const testState = {
      wsConnected: true, droneStates: {}, droneHistory: {}, droneTrails: {},
      missions: {}, selectedDroneId: 0,
      showTrails: true, showWaypoints: true, darkMode: true,
      swarmSummary: null,
      alerts: [
        { drone_id: 2, alert_seq: 1, severity: 1, message: 'Low battery 30%' },
        { drone_id: 4, alert_seq: 2, severity: 2, message: 'Motor fault' },
      ],
    };
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <AlertFeed />
      </WebSocketProvider>
    );
    const items = screen.getAllByTestId('alert-item');
    expect(items).toHaveLength(2);
    expect(items[0].textContent).toContain('CHARLIE');
    expect(items[0].textContent).toContain('Low battery 30%');
  });

  it('severity classes applied', () => {
    const testState = {
      wsConnected: true, droneStates: {}, droneHistory: {}, droneTrails: {},
      missions: {}, selectedDroneId: 0,
      showTrails: true, showWaypoints: true, darkMode: true,
      swarmSummary: null,
      alerts: [
        { drone_id: 0, alert_seq: 1, severity: 2, message: 'Critical' },
        { drone_id: 0, alert_seq: 2, severity: 1, message: 'Warning' },
        { drone_id: 0, alert_seq: 3, severity: 0, message: 'Info' },
      ],
    };
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <AlertFeed />
      </WebSocketProvider>
    );
    const items = screen.getAllByTestId('alert-item');
    expect(items[0].classList.contains('critical')).toBe(true);
    expect(items[1].classList.contains('warning')).toBe(true);
    expect(items[2].classList.contains('info')).toBe(true);
  });

  it('newest alerts appear first', () => {
    const testState = {
      wsConnected: true, droneStates: {}, droneHistory: {}, droneTrails: {},
      missions: {}, selectedDroneId: 0,
      showTrails: true, showWaypoints: true, darkMode: true,
      swarmSummary: null,
      alerts: [
        { drone_id: 0, alert_seq: 2, severity: 1, message: 'Second' },
        { drone_id: 0, alert_seq: 1, severity: 0, message: 'First' },
      ],
    };
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <AlertFeed />
      </WebSocketProvider>
    );
    const items = screen.getAllByTestId('alert-item');
    expect(items[0].textContent).toContain('Second');
  });
});
