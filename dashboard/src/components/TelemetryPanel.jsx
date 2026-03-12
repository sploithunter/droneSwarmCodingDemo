import React from 'react';
import { useSwarmState } from '../context/WebSocketContext';
import BatteryChart from './charts/BatteryChart';
import AltitudeChart from './charts/AltitudeChart';
import SpeedChart from './charts/SpeedChart';
import MotorRPMChart from './charts/MotorRPMChart';
import TemperatureChart from './charts/TemperatureChart';
import { CALLSIGNS } from '../utils/constants';

export default function TelemetryPanel() {
  const { state } = useSwarmState();
  const droneId = state.selectedDroneId;
  const history = state.droneHistory[droneId] || [];
  const callsign = CALLSIGNS[droneId] || `Drone ${droneId}`;

  return (
    <div className="telemetry-panel" data-testid="telemetry-panel">
      <h2>Telemetry — {callsign} ({droneId})</h2>
      <div className="chart-grid">
        <BatteryChart history={history} />
        <AltitudeChart history={history} />
        <SpeedChart history={history} />
        <MotorRPMChart history={history} />
        <TemperatureChart history={history} />
      </div>
    </div>
  );
}
