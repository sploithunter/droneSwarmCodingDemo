import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { WebSocketProvider } from '../../context/WebSocketContext';

// Mock leaflet since it doesn't work in jsdom
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

import MapPanel from '../../components/MapPanel';

// MapPanel uses Leaflet which doesn't work in jsdom.
// We test the component renders and map controls work.

const testState = {
  wsConnected: true,
  droneStates: {
    0: { drone_id: 0, mode: 2, heading_deg: 45, position: { latitude: 37.387, longitude: -122.084 } },
  },
  droneHistory: {},
  droneTrails: { 0: [{ lat: 37.386, lon: -122.084, _localTime: Date.now() }] },
  missions: {},
  alerts: [],
  swarmSummary: null,
  selectedDroneId: 0,
  showTrails: true,
  showWaypoints: true,
  darkMode: true,
};

describe('SPEC 12 — Map Panel', () => {
  it('renders map panel container', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <MapPanel />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('map-panel')).toBeInTheDocument();
  });

  it('has map controls', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <MapPanel />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('toggle-trails')).toBeInTheDocument();
    expect(screen.getByTestId('toggle-waypoints')).toBeInTheDocument();
  });

  it('trail toggle button has active class when trails on', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <MapPanel />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('toggle-trails').classList.contains('active')).toBe(true);
  });

  it('trail toggle button dispatches', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <MapPanel />
      </WebSocketProvider>
    );
    fireEvent.click(screen.getByTestId('toggle-trails'));
    // After click, showTrails should be false, so button loses active class
    expect(screen.getByTestId('toggle-trails').classList.contains('active')).toBe(false);
  });
});
