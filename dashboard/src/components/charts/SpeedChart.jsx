import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function SpeedChart({ history }) {
  const windowMs = 120000;
  const now = Date.now();
  const data = history
    .filter(h => now - h._localTime < windowMs)
    .map(h => ({
      time: ((h._localTime - now) / 1000).toFixed(0),
      speed: h.ground_speed_mps,
    }));

  return (
    <div className="chart-container" data-testid="speed-chart">
      <h3>Speed (m/s)</h3>
      <ResponsiveContainer width="100%" height={150}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis domain={[0, 15]} unit="m/s" />
          <Tooltip />
          <Line type="monotone" dataKey="speed" stroke="var(--chart-3)" dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
