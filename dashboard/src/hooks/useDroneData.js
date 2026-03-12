import { useMemo } from 'react';
import { useSwarmState } from '../context/WebSocketContext';

export default function useDroneData(droneId) {
  const { state } = useSwarmState();
  const id = droneId !== undefined ? droneId : state.selectedDroneId;

  return useMemo(() => ({
    current: state.droneStates[id] || null,
    history: state.droneHistory[id] || [],
    trail: state.droneTrails[id] || [],
    mission: state.missions[id] || null,
  }), [state.droneStates[id], state.droneHistory[id], state.droneTrails[id], state.missions[id], id]);
}
