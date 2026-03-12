import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { WebSocketProvider } from '../../context/WebSocketContext';
import DroneSelector from '../../components/DroneSelector';

const baseState = {
  wsConnected: true,
  droneStates: {
    0: { drone_id: 0, mode: 2 },
    4: { drone_id: 4, mode: 7 },
    7: { drone_id: 7, mode: 0 },
  },
  droneHistory: {}, droneTrails: {},
  missions: {}, alerts: [], swarmSummary: null,
  selectedDroneId: 0,
  showTrails: true, showWaypoints: true, darkMode: true,
};

describe('SPEC 15 — Drone Selector', () => {
  it('shows 8 drone tabs', () => {
    render(
      <WebSocketProvider initialStateOverride={baseState}>
        <DroneSelector />
      </WebSocketProvider>
    );
    for (let i = 0; i < 8; i++) {
      expect(screen.getByTestId(`drone-tab-${i}`)).toBeInTheDocument();
    }
  });

  it('tabs show callsigns', () => {
    render(
      <WebSocketProvider initialStateOverride={baseState}>
        <DroneSelector />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('drone-tab-0').textContent).toContain('ALPHA');
    expect(screen.getByTestId('drone-tab-7').textContent).toContain('HOTEL');
  });

  it('selected tab is highlighted', () => {
    render(
      <WebSocketProvider initialStateOverride={baseState}>
        <DroneSelector />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('drone-tab-0').classList.contains('selected')).toBe(true);
  });

  it('clicking tab changes selection', () => {
    render(
      <WebSocketProvider initialStateOverride={baseState}>
        <DroneSelector />
      </WebSocketProvider>
    );
    fireEvent.click(screen.getByTestId('drone-tab-5'));
    expect(screen.getByTestId('drone-tab-5').classList.contains('selected')).toBe(true);
  });
});
