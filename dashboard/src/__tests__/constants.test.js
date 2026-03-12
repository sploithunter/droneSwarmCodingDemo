import { describe, it, expect } from 'vitest';
import { CALLSIGNS, MODE_COLORS, BASE_STATION, WS_URL } from '../utils/constants';

describe('constants', () => {
  it('has 8 callsigns', () => {
    expect(CALLSIGNS).toHaveLength(8);
  });

  it('callsigns match spec', () => {
    expect(CALLSIGNS).toEqual([
      'ALPHA', 'BRAVO', 'CHARLIE', 'DELTA',
      'ECHO', 'FOXTROT', 'GOLF', 'HOTEL'
    ]);
  });

  it('all modes have colors', () => {
    const modes = ['IDLE', 'TAKEOFF', 'EN_ROUTE', 'HOVERING', 'RETURNING_TO_BASE', 'LANDING', 'LANDED', 'FAULT'];
    modes.forEach(mode => {
      expect(MODE_COLORS[mode]).toBeDefined();
    });
  });

  it('base station coordinates', () => {
    expect(BASE_STATION.lat).toBeCloseTo(37.3861, 4);
    expect(BASE_STATION.lon).toBeCloseTo(-122.0839, 4);
  });

  it('WebSocket URL is defined', () => {
    expect(WS_URL).toBe('ws://localhost:8765');
  });
});
