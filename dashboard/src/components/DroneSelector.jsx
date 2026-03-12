import React from 'react';
import { useSwarmState } from '../context/WebSocketContext';
import { CALLSIGNS, DRONE_COLORS } from '../utils/constants';

const MODE_NAMES = ['IDLE', 'TAKEOFF', 'EN_ROUTE', 'HOVERING', 'RETURNING_TO_BASE', 'LANDING', 'LANDED', 'FAULT'];

const MODE_COLOR_MAP = {
  0: '#808080', // IDLE
  1: '#2196F3', // TAKEOFF
  2: '#2196F3', // EN_ROUTE
  3: '#00BCD4', // HOVERING
  4: '#FF9800', // RETURNING_TO_BASE
  5: '#FF9800', // LANDING
  6: '#808080', // LANDED
  7: '#F44336', // FAULT
};

export default function DroneSelector() {
  const { state, dispatch } = useSwarmState();

  return (
    <div className="drone-selector" data-testid="drone-selector">
      {CALLSIGNS.map((callsign, id) => {
        const droneState = state.droneStates[id];
        const mode = droneState ? droneState.mode : 0;
        const modeColor = MODE_COLOR_MAP[mode] || '#808080';
        const isSelected = state.selectedDroneId === id;

        return (
          <button
            key={id}
            className={`drone-tab ${isSelected ? 'selected' : ''}`}
            data-testid={`drone-tab-${id}`}
            onClick={() => dispatch({ type: 'SELECT_DRONE', payload: id })}
            style={{ borderColor: modeColor }}
          >
            <span className="tab-indicator" style={{ backgroundColor: modeColor }} />
            <span className="tab-id">{id}</span>
            <span className="tab-callsign">{callsign}</span>
          </button>
        );
      })}
    </div>
  );
}
