import React, { useState } from 'react';
import { useSwarmState } from '../context/WebSocketContext';
import { CALLSIGNS } from '../utils/constants';

export default function CommandPanel({ wsRef }) {
  const { state, sendCommand } = useSwarmState();
  const [broadcast, setBroadcast] = useState(false);
  const [speed, setSpeed] = useState('');
  const [altitude, setAltitude] = useState('');
  const [wpLat, setWpLat] = useState('');
  const [wpLon, setWpLon] = useState('');
  const [wpAlt, setWpAlt] = useState('');

  const droneId = broadcast ? 255 : state.selectedDroneId;
  const callsign = broadcast ? 'ALL' : (CALLSIGNS[state.selectedDroneId] || `Drone ${state.selectedDroneId}`);

  const send = (command, parameter = 0.0, target = null) => {
    const cmd = {
      drone_id: droneId,
      command,
      parameter,
      target_position: target,
    };
    sendCommand(wsRef?.current, cmd);
  };

  return (
    <div className="command-panel" data-testid="command-panel">
      <h2>Commands — {callsign}</h2>

      <div className="broadcast-toggle">
        <label data-testid="broadcast-toggle">
          <input
            type="checkbox"
            checked={broadcast}
            onChange={(e) => setBroadcast(e.target.checked)}
          />
          Send to All Drones
        </label>
      </div>

      <div className="quick-commands" data-testid="quick-commands">
        <button data-testid="btn-rtb" onClick={() => send('RETURN_TO_BASE')}>Return to Base</button>
        <button data-testid="btn-hover" onClick={() => send('HOVER')}>Hover</button>
        <button data-testid="btn-resume" onClick={() => send('RESUME_MISSION')}>Resume Mission</button>
        <button data-testid="btn-eland" onClick={() => send('EMERGENCY_LAND')}>Emergency Land</button>
      </div>

      <div className="param-commands" data-testid="param-commands">
        <div className="param-row">
          <input
            type="number"
            data-testid="input-speed"
            placeholder="m/s"
            value={speed}
            onChange={(e) => setSpeed(e.target.value)}
          />
          <button data-testid="btn-set-speed" onClick={() => send('SET_SPEED', parseFloat(speed) || 0)}>
            Set Speed
          </button>
        </div>
        <div className="param-row">
          <input
            type="number"
            data-testid="input-altitude"
            placeholder="meters"
            value={altitude}
            onChange={(e) => setAltitude(e.target.value)}
          />
          <button data-testid="btn-set-altitude" onClick={() => send('SET_ALTITUDE', parseFloat(altitude) || 0)}>
            Set Altitude
          </button>
        </div>
      </div>

      <div className="waypoint-command" data-testid="waypoint-command">
        <h3>Go To Waypoint</h3>
        <input type="number" data-testid="input-wp-lat" placeholder="Latitude" value={wpLat} onChange={(e) => setWpLat(e.target.value)} />
        <input type="number" data-testid="input-wp-lon" placeholder="Longitude" value={wpLon} onChange={(e) => setWpLon(e.target.value)} />
        <input type="number" data-testid="input-wp-alt" placeholder="Altitude" value={wpAlt} onChange={(e) => setWpAlt(e.target.value)} />
        <button data-testid="btn-goto" onClick={() => send('GOTO_WAYPOINT', 0, {
          latitude: parseFloat(wpLat) || 0,
          longitude: parseFloat(wpLon) || 0,
          altitude_m: parseFloat(wpAlt) || 0,
        })}>
          Go To Waypoint
        </button>
      </div>
    </div>
  );
}
