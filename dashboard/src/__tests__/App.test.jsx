import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from '../App';

// Mock useWebSocket since it tries to connect
vi.mock('../hooks/useWebSocket', () => ({
  default: () => ({ current: null }),
}));

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

describe('App', () => {
  it('renders without crash', () => {
    render(<App />);
    expect(screen.getByTestId('app')).toBeInTheDocument();
  });

  it('displays title', () => {
    render(<App />);
    expect(screen.getByText('Drone Swarm Monitor')).toBeInTheDocument();
  });
});
