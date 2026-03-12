import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function AltitudeChart({ history }) {
  const windowMs = 120000;
  const now = Date.now();
  const data = history
    .filter(h => now - h._localTime < windowMs)
    .map(h => ({
      time: ((h._localTime - now) / 1000).toFixed(0),
      altitude: h.position ? h.position.altitude_m : 0,
    }));

  return (
    <div className="chart-container" data-testid="altitude-chart">
      <h3>Altitude (m)</h3>
      <ResponsiveContainer width="100%" height={150}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis domain={[0, 120]} unit="m" />
          <Tooltip />
          <Line type="monotone" dataKey="altitude" stroke="var(--chart-2)" dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
