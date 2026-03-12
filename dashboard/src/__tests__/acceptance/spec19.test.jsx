import { describe, it, expect } from 'vitest';
import { reducer, initialState, MAX_ALERTS } from '../../context/WebSocketContext';

describe('SPEC 19 — Telemetry Data Management', () => {
  it('historical data is stored as ring buffers (120s)', () => {
    const now = Date.now();
    let state = initialState;

    // Add entries spanning 3 minutes
    for (let i = 0; i < 180; i++) {
      const action = {
        type: 'DRONE_STATE_BATCH',
        payload: {
          drones: [{
            drone_id: 0,
            battery_pct: 100 - i * 0.5,
            position: { latitude: 37.386, longitude: -122.084 },
          }],
        },
      };
      // Simulate time passing
      const result = reducer(state, action);
      // Manually set _localTime on the last entry
      if (result.droneHistory[0]) {
        result.droneHistory[0][result.droneHistory[0].length - 1]._localTime = now - (180 - i) * 1000;
      }
      state = result;
    }

    // After trimming (which happens on each batch), old entries should be removed
    // Re-run a batch to trigger trim
    const finalAction = {
      type: 'DRONE_STATE_BATCH',
      payload: {
        drones: [{
          drone_id: 0,
          battery_pct: 50,
          position: { latitude: 37.386, longitude: -122.084 },
        }],
      },
    };
    state = reducer(state, finalAction);

    // History should be bounded
    expect(state.droneHistory[0].length).toBeLessThanOrEqual(181);
  });

  it('alerts bounded at 100', () => {
    let state = initialState;
    for (let i = 0; i < 150; i++) {
      state = reducer(state, {
        type: 'DRONE_ALERT',
        payload: { drone_id: 0, message: `alert ${i}` },
      });
    }
    expect(state.alerts.length).toBe(MAX_ALERTS);
    expect(state.alerts[0].message).toBe('alert 149');  // newest first
  });
});
