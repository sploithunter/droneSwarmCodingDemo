import { describe, it, expect } from 'vitest';
import { reducer, initialState, trimHistory, MAX_ALERTS } from '../context/WebSocketContext';

describe('WebSocketContext reducer', () => {
  it('SET_CONNECTED updates wsConnected', () => {
    const state = reducer(initialState, { type: 'SET_CONNECTED', payload: true });
    expect(state.wsConnected).toBe(true);
  });

  it('DRONE_STATE_BATCH updates droneStates', () => {
    const action = {
      type: 'DRONE_STATE_BATCH',
      payload: {
        drones: [
          { drone_id: 0, battery_pct: 85, position: { latitude: 37.386, longitude: -122.084 } },
          { drone_id: 1, battery_pct: 72, position: { latitude: 37.387, longitude: -122.083 } },
        ],
      },
    };
    const state = reducer(initialState, action);
    expect(state.droneStates[0].battery_pct).toBe(85);
    expect(state.droneStates[1].battery_pct).toBe(72);
  });

  it('DRONE_STATE_BATCH appends to history', () => {
    const action = {
      type: 'DRONE_STATE_BATCH',
      payload: {
        drones: [{ drone_id: 0, battery_pct: 85, position: { latitude: 37.386, longitude: -122.084 } }],
      },
    };
    let state = reducer(initialState, action);
    state = reducer(state, action);
    expect(state.droneHistory[0].length).toBe(2);
  });

  it('DRONE_STATE_BATCH appends to trails', () => {
    const action = {
      type: 'DRONE_STATE_BATCH',
      payload: {
        drones: [{ drone_id: 0, battery_pct: 85, position: { latitude: 37.386, longitude: -122.084 } }],
      },
    };
    const state = reducer(initialState, action);
    expect(state.droneTrails[0].length).toBe(1);
    expect(state.droneTrails[0][0].lat).toBeCloseTo(37.386);
  });

  it('DRONE_ALERT prepends to alerts', () => {
    const alert1 = { drone_id: 0, message: 'first' };
    const alert2 = { drone_id: 1, message: 'second' };
    let state = reducer(initialState, { type: 'DRONE_ALERT', payload: alert1 });
    state = reducer(state, { type: 'DRONE_ALERT', payload: alert2 });
    expect(state.alerts[0].message).toBe('second');
    expect(state.alerts[1].message).toBe('first');
  });

  it('DRONE_ALERT caps at MAX_ALERTS', () => {
    let state = initialState;
    for (let i = 0; i < 150; i++) {
      state = reducer(state, { type: 'DRONE_ALERT', payload: { drone_id: 0, message: `alert ${i}` } });
    }
    expect(state.alerts.length).toBe(MAX_ALERTS);
  });

  it('MISSION_PLAN stores mission by drone_id', () => {
    const mission = { drone_id: 3, mission_name: 'Test', waypoints: [] };
    const state = reducer(initialState, { type: 'MISSION_PLAN', payload: mission });
    expect(state.missions[3].mission_name).toBe('Test');
  });

  it('SWARM_SUMMARY updates summary', () => {
    const summary = { active_drones: 5, faulted_drones: 1 };
    const state = reducer(initialState, { type: 'SWARM_SUMMARY', payload: summary });
    expect(state.swarmSummary.active_drones).toBe(5);
  });

  it('SELECT_DRONE changes selectedDroneId', () => {
    const state = reducer(initialState, { type: 'SELECT_DRONE', payload: 5 });
    expect(state.selectedDroneId).toBe(5);
  });

  it('TOGGLE_TRAILS flips showTrails', () => {
    const state = reducer(initialState, { type: 'TOGGLE_TRAILS' });
    expect(state.showTrails).toBe(false);
  });

  it('TOGGLE_WAYPOINTS flips showWaypoints', () => {
    const state = reducer(initialState, { type: 'TOGGLE_WAYPOINTS' });
    expect(state.showWaypoints).toBe(false);
  });

  it('TOGGLE_DARK_MODE flips darkMode', () => {
    const state = reducer(initialState, { type: 'TOGGLE_DARK_MODE' });
    expect(state.darkMode).toBe(false);
  });
});

describe('trimHistory', () => {
  it('removes old entries', () => {
    const now = Date.now();
    const entries = [
      { _localTime: now - 200000 },  // 200s ago — too old for 120s window
      { _localTime: now - 60000 },   // 60s ago — within window
      { _localTime: now },           // now
    ];
    const trimmed = trimHistory(entries, 120);
    expect(trimmed.length).toBe(2);
  });

  it('returns empty array for empty input', () => {
    expect(trimHistory([], 120)).toEqual([]);
  });
});
