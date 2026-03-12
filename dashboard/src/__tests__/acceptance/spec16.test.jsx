import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WebSocketProvider } from '../../context/WebSocketContext';
import TelemetryPanel from '../../components/TelemetryPanel';

// Mock recharts to avoid rendering issues in jsdom
vi.mock('recharts', async (importOriginal) => {
  const Original = await importOriginal();
  return {
    ...Original,
    ResponsiveContainer: ({ children }) => <div>{children}</div>,
  };
});

const now = Date.now();
const makeHistory = (count = 10) =>
  Array.from({ length: count }, (_, i) => ({
    _localTime: now - (count - i) * 1000,
    battery_pct: 100 - i,
    position: { latitude: 37.386, longitude: -122.084, altitude_m: 50 + i },
    ground_speed_mps: 10,
    motor_rpm: [5000, 5100, 4900, 5050],
    internal_temp_c: 35 + i * 0.5,
  }));

const testState = {
  wsConnected: true,
  droneStates: { 0: { drone_id: 0, mode: 2 } },
  droneHistory: { 0: makeHistory() },
  droneTrails: {},
  missions: {},
  alerts: [],
  swarmSummary: null,
  selectedDroneId: 0,
  showTrails: true,
  showWaypoints: true,
  darkMode: true,
};

describe('SPEC 16 — Telemetry Charts', () => {
  it('renders telemetry panel with all 5 charts', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <TelemetryPanel />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('telemetry-panel')).toBeInTheDocument();
    expect(screen.getByTestId('battery-chart')).toBeInTheDocument();
    expect(screen.getByTestId('altitude-chart')).toBeInTheDocument();
    expect(screen.getByTestId('speed-chart')).toBeInTheDocument();
    expect(screen.getByTestId('motor-rpm-chart')).toBeInTheDocument();
    expect(screen.getByTestId('temperature-chart')).toBeInTheDocument();
  });

  it('shows selected drone callsign', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <TelemetryPanel />
      </WebSocketProvider>
    );
    expect(screen.getByText(/ALPHA/)).toBeInTheDocument();
  });

  it('switches data when drone changes', () => {
    const stateWithTwo = {
      ...testState,
      droneHistory: { 0: makeHistory(), 3: makeHistory(5) },
      selectedDroneId: 3,
    };
    render(
      <WebSocketProvider initialStateOverride={stateWithTwo}>
        <TelemetryPanel />
      </WebSocketProvider>
    );
    expect(screen.getByText(/DELTA/)).toBeInTheDocument();
  });
});
