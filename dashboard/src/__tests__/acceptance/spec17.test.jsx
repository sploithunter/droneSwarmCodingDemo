import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { WebSocketProvider } from '../../context/WebSocketContext';
import CommandPanel from '../../components/CommandPanel';

const testState = {
  wsConnected: true,
  droneStates: { 0: { drone_id: 0, mode: 2 } },
  droneHistory: {},
  droneTrails: {},
  missions: {},
  alerts: [],
  swarmSummary: null,
  selectedDroneId: 3,
  showTrails: true,
  showWaypoints: true,
  darkMode: true,
};

describe('SPEC 17 — Command Panel', () => {
  it('renders quick command buttons', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <CommandPanel />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('btn-rtb')).toBeInTheDocument();
    expect(screen.getByTestId('btn-hover')).toBeInTheDocument();
    expect(screen.getByTestId('btn-resume')).toBeInTheDocument();
    expect(screen.getByTestId('btn-eland')).toBeInTheDocument();
  });

  it('renders parameter inputs', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <CommandPanel />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('input-speed')).toBeInTheDocument();
    expect(screen.getByTestId('input-altitude')).toBeInTheDocument();
    expect(screen.getByTestId('btn-set-speed')).toBeInTheDocument();
    expect(screen.getByTestId('btn-set-altitude')).toBeInTheDocument();
  });

  it('renders waypoint inputs', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <CommandPanel />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('input-wp-lat')).toBeInTheDocument();
    expect(screen.getByTestId('input-wp-lon')).toBeInTheDocument();
    expect(screen.getByTestId('input-wp-alt')).toBeInTheDocument();
    expect(screen.getByTestId('btn-goto')).toBeInTheDocument();
  });

  it('has broadcast toggle', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <CommandPanel />
      </WebSocketProvider>
    );
    expect(screen.getByTestId('broadcast-toggle')).toBeInTheDocument();
  });

  it('shows target drone callsign', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <CommandPanel />
      </WebSocketProvider>
    );
    expect(screen.getByText(/DELTA/)).toBeInTheDocument();
  });

  it('broadcast toggle shows ALL', () => {
    render(
      <WebSocketProvider initialStateOverride={testState}>
        <CommandPanel />
      </WebSocketProvider>
    );
    fireEvent.click(screen.getByTestId('broadcast-toggle').querySelector('input'));
    expect(screen.getByText(/ALL/)).toBeInTheDocument();
  });
});
