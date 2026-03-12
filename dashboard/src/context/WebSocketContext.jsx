import React, { createContext, useContext, useReducer, useCallback } from 'react';

const WebSocketContext = createContext(null);

const MAX_HISTORY_SEC = 120;
const MAX_TRAIL_SEC = 60;
const MAX_ALERTS = 100;

const initialState = {
  wsConnected: false,
  droneStates: {},
  droneHistory: {},
  droneTrails: {},
  missions: {},
  alerts: [],
  swarmSummary: null,
  selectedDroneId: 0,
  showTrails: true,
  showWaypoints: true,
  darkMode: true,
};

function trimHistory(history, maxSec) {
  if (!history || history.length === 0) return history;
  const cutoff = Date.now() - maxSec * 1000;
  return history.filter(h => h._localTime >= cutoff);
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_CONNECTED':
      return { ...state, wsConnected: action.payload };

    case 'DRONE_STATE_BATCH': {
      const drones = action.payload.drones || [];
      const newStates = { ...state.droneStates };
      const newHistory = { ...state.droneHistory };
      const newTrails = { ...state.droneTrails };
      const now = Date.now();

      for (const drone of drones) {
        const id = drone.drone_id;
        newStates[id] = drone;

        // Append to history
        const entry = { ...drone, _localTime: now };
        const hist = [...(newHistory[id] || []), entry];
        newHistory[id] = trimHistory(hist, MAX_HISTORY_SEC);

        // Append to trails
        if (drone.position) {
          const pos = { lat: drone.position.latitude, lon: drone.position.longitude, _localTime: now };
          const trail = [...(newTrails[id] || []), pos];
          newTrails[id] = trimHistory(trail, MAX_TRAIL_SEC);
        }
      }

      return { ...state, droneStates: newStates, droneHistory: newHistory, droneTrails: newTrails };
    }

    case 'DRONE_ALERT': {
      const alert = action.payload;
      const alerts = [alert, ...state.alerts].slice(0, MAX_ALERTS);
      return { ...state, alerts };
    }

    case 'MISSION_PLAN': {
      const mission = action.payload;
      return {
        ...state,
        missions: { ...state.missions, [mission.drone_id]: mission },
      };
    }

    case 'SWARM_SUMMARY':
      return { ...state, swarmSummary: action.payload };

    case 'SELECT_DRONE':
      return { ...state, selectedDroneId: action.payload };

    case 'TOGGLE_TRAILS':
      return { ...state, showTrails: !state.showTrails };

    case 'TOGGLE_WAYPOINTS':
      return { ...state, showWaypoints: !state.showWaypoints };

    case 'TOGGLE_DARK_MODE':
      return { ...state, darkMode: !state.darkMode };

    default:
      return state;
  }
}

export function WebSocketProvider({ children, initialStateOverride }) {
  const [state, dispatch] = useReducer(reducer, initialStateOverride || initialState);

  const sendCommand = useCallback((ws, command) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'drone_command',
        data: command,
      }));
    }
  }, []);

  return (
    <WebSocketContext.Provider value={{ state, dispatch, sendCommand }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useSwarmState() {
  const context = useContext(WebSocketContext);
  if (!context) throw new Error('useSwarmState must be used within WebSocketProvider');
  return context;
}

export { reducer, initialState, trimHistory, MAX_HISTORY_SEC, MAX_TRAIL_SEC, MAX_ALERTS };
export default WebSocketContext;
