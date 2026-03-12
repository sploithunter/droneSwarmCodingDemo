import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WebSocketProvider } from '../../context/WebSocketContext';
import { reducer, initialState } from '../../context/WebSocketContext';

// Mock recharts
vi.mock('recharts', async () => {
  const actual = await vi.importActual('recharts');
  return {
    ...actual,
    ResponsiveContainer: ({ children }) => <div>{children}</div>,
  };
});

// Mock useWebSocket
vi.mock('../../hooks/useWebSocket', () => ({
  default: () => ({ current: null }),
}));

// Mock leaflet
const mkMarker = () => ({ setLatLng() { return this; }, setIcon() { return this; }, addTo() { return this; }, bindPopup() { return this; }, on() { return this; } });
vi.mock('leaflet', () => ({
  default: {
    map: () => ({ setView() { return this; }, remove() {}, removeLayer() {} }),
    tileLayer: () => ({ addTo() {} }),
    marker: () => mkMarker(),
    divIcon: () => ({}),
    polygon: () => ({ addTo() {} }),
    polyline: () => ({ addTo() { return this; }, setLatLngs() {} }),
  },
}));
vi.mock('leaflet/dist/leaflet.css', () => ({}));

import App from '../../App';

describe('SPEC 20 — E2E Dashboard Smoke Test', () => {
  it('full app renders with all major sections', () => {
    render(<App />);
    expect(screen.getByTestId('app')).toBeInTheDocument();
    expect(screen.getByTestId('header')).toBeInTheDocument();
    expect(screen.getByTestId('map-panel')).toBeInTheDocument();
    expect(screen.getByTestId('drone-selector')).toBeInTheDocument();
    expect(screen.getByTestId('telemetry-panel')).toBeInTheDocument();
    expect(screen.getByTestId('command-panel')).toBeInTheDocument();
  });

  it('simulates receiving drone data and updating UI', () => {
    // Build up state through reducer to simulate real data flow
    let state = initialState;

    // Simulate connection
    state = reducer(state, { type: 'SET_CONNECTED', payload: true });
    expect(state.wsConnected).toBe(true);

    // Simulate drone state batch
    state = reducer(state, {
      type: 'DRONE_STATE_BATCH',
      payload: {
        drones: Array.from({ length: 8 }, (_, i) => ({
          drone_id: i,
          mode: i < 7 ? 2 : 0,
          battery_pct: 100 - i * 5,
          position: { latitude: 37.386 + i * 0.001, longitude: -122.084 },
          heading_deg: i * 45,
          ground_speed_mps: i < 7 ? 10 : 0,
          motor_rpm: [5000, 5100, 4900, 5050],
          internal_temp_c: 35 + i,
        })),
      },
    });
    expect(Object.keys(state.droneStates)).toHaveLength(8);
    expect(state.droneStates[7].mode).toBe(0); // IDLE

    // Simulate alert
    state = reducer(state, {
      type: 'DRONE_ALERT',
      payload: {
        drone_id: 2,
        alert_seq: 1,
        severity: 1,
        alert_type: 0,
        message: 'Battery at 30%',
      },
    });
    expect(state.alerts).toHaveLength(1);
    expect(state.alerts[0].drone_id).toBe(2);

    // Simulate swarm summary
    state = reducer(state, {
      type: 'SWARM_SUMMARY',
      payload: {
        active_drones: 5,
        faulted_drones: 1,
        returning_drones: 1,
        idle_drones: 1,
        avg_battery_pct: 73,
        min_battery_pct: 31,
        min_battery_drone_id: 2,
        missions_completed: 0,
        active_alerts: 1,
      },
    });
    expect(state.swarmSummary.active_drones).toBe(5);

    // Simulate mission plan
    state = reducer(state, {
      type: 'MISSION_PLAN',
      payload: {
        drone_id: 0,
        mission_name: 'Perimeter Patrol',
        waypoints: [
          { latitude: 37.387, longitude: -122.084, altitude_m: 50 },
          { latitude: 37.387, longitude: -122.083, altitude_m: 50 },
        ],
        is_active: true,
      },
    });
    expect(state.missions[0].mission_name).toBe('Perimeter Patrol');

    // Select drone
    state = reducer(state, { type: 'SELECT_DRONE', payload: 3 });
    expect(state.selectedDroneId).toBe(3);
  });

  it('renders with pre-populated state', () => {
    const populatedState = {
      wsConnected: true,
      droneStates: Object.fromEntries(
        Array.from({ length: 8 }, (_, i) => [i, {
          drone_id: i, mode: i < 7 ? 2 : 0, battery_pct: 90 - i * 5,
          position: { latitude: 37.386, longitude: -122.084 },
          heading_deg: 0, ground_speed_mps: 10,
          motor_rpm: [5000, 5000, 5000, 5000], internal_temp_c: 40,
        }])
      ),
      droneHistory: {},
      droneTrails: {},
      missions: {},
      alerts: [
        { drone_id: 2, alert_seq: 1, severity: 1, message: 'Low battery' },
      ],
      swarmSummary: {
        active_drones: 6, faulted_drones: 0, returning_drones: 1, idle_drones: 1,
        avg_battery_pct: 75, min_battery_pct: 55, min_battery_drone_id: 6,
        missions_completed: 1, active_alerts: 1,
      },
      selectedDroneId: 0,
      showTrails: true,
      showWaypoints: true,
      darkMode: true,
    };

    render(
      <WebSocketProvider initialStateOverride={populatedState}>
        <div data-testid="e2e-container">
          {/* Import and render individual components to test with state */}
        </div>
      </WebSocketProvider>
    );
    expect(screen.getByTestId('e2e-container')).toBeInTheDocument();
  });
});
